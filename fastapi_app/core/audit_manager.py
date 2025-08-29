import uuid
import json
import threading
from pathlib import Path
from sqlalchemy.orm import Session
from ..database import AuditTask
from ..config import settings
from .audit_client import audit_client

class AuditManager:
    def __init__(self):
        self.running_tasks = {}
    
    def start_audit(self, site_name: str, date: str, db: Session):
        if site_name not in settings.data_paths:
            return {"success": False, "message": "Invalid site name"}
        
        folder_path = Path(settings.data_paths[site_name]) / date
        if not folder_path.exists():
            return {"success": False, "message": "Data folder not found"}
        
        task_id = str(uuid.uuid4())
        
        # 创建审核任务记录
        audit_task = AuditTask(
            task_id=task_id,
            site_name=site_name,
            date_folder=date,
            status="pending"
        )
        db.add(audit_task)
        db.commit()
        
        # 启动后台审核线程
        thread = threading.Thread(target=self._run_audit, args=(task_id, str(folder_path), db))
        thread.start()
        self.running_tasks[task_id] = thread
        
        return {"success": True, "task_id": task_id}
    
    def _run_audit(self, task_id: str, folder_path: str, db: Session):
        try:
            # 更新状态为运行中
            task = db.query(AuditTask).filter(AuditTask.task_id == task_id).first()
            task.status = "running"
            task.progress = 10
            db.commit()
            
            # 使用新的审核客户端，将结果存入数据库
            audit_client.process_site_with_db(
                task_id=task_id,
                site_name=task.site_name,
                date_folder=task.date_folder,
                folder_path=folder_path,
                db=db
            )
            
            # 更新为完成状态
            task.status = "completed"
            task.progress = 100
            db.commit()
            
        except Exception as e:
            task = db.query(AuditTask).filter(AuditTask.task_id == task_id).first()
            task.status = "failed"
            task.results = str(e)
            db.commit()
        
        finally:
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
    
    def get_task_status(self, task_id: str, db: Session):
        task = db.query(AuditTask).filter(AuditTask.task_id == task_id).first()
        if not task:
            return {"success": False, "message": "Task not found"}
        
        return {
            "success": True,
            "data": {
                "task_id": task.task_id,
                "status": task.status,
                "progress": task.progress,
                "results": task.results,
                "created_at": task.created_at
            }
        }
    
    def get_audit_results(self, site_name: str, db: Session):
        tasks = db.query(AuditTask).filter(AuditTask.site_name == site_name).all()
        return {
            "success": True,
            "data": [
                {
                    "task_id": t.task_id,
                    "date_folder": t.date_folder,
                    "status": t.status,
                    "progress": t.progress,
                    "created_at": t.created_at
                }
                for t in tasks
            ]
        }
    
    def get_detailed_results(self, task_id: str, db: Session):
        """获取任务的详细审核结果"""
        from ..database import AuditResult
        
        results = db.query(AuditResult).filter(AuditResult.task_id == task_id).all()
        
        summary = {
            "total_files": len(results),
            "sensitive_files": len([r for r in results if r.is_sensitive]),
            "image_files": len([r for r in results if r.file_type == "image"]),
            "text_files": len([r for r in results if r.file_type == "text"]),
            "details": []
        }
        
        for result in results:
            detail = {
                "page_name": result.page_name,
                "file_type": result.file_type,
                "file_name": result.file_name,
                "is_sensitive": result.is_sensitive,
                "confidence": result.confidence,
                "created_at": result.created_at
            }
            
            if result.file_type == "image":
                detail.update({
                    "is_abnormal_window": result.is_abnormal_window,
                    "porn_score": result.porn_score,
                    "sexy_score": result.sexy_score,
                    "ocr_text": result.ocr_text[:100] + "..." if result.ocr_text and len(result.ocr_text) > 100 else result.ocr_text
                })
            else:
                detail["sensitive_words"] = result.sensitive_words
            
            summary["details"].append(detail)
        
        return {"success": True, "data": summary}

audit_manager = AuditManager()