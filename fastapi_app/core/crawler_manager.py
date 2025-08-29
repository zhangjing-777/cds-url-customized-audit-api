import subprocess
import psutil
from sqlalchemy.orm import Session
from ..database import CrawlerTask, get_db
from ..config import settings
from datetime import datetime

class CrawlerManager:
    def __init__(self):
        self.processes = {}
    
    def start_crawler(self, site_name: str, db: Session):
        if site_name not in settings.crawler_scripts:
            return {"success": False, "message": "Invalid site name"}
        
        # 检查是否已运行
        task = db.query(CrawlerTask).filter(CrawlerTask.site_name == site_name).first()
        if task and task.status == "running" and task.pid and psutil.pid_exists(task.pid):
            return {"success": False, "message": "Crawler already running"}
        
        # 启动爬虫进程
        script_path = settings.crawler_scripts[site_name]
        process = subprocess.Popen(["python3.11", script_path], cwd=".")
        
        # 更新数据库
        if not task:
            task = CrawlerTask(site_name=site_name)
            db.add(task)
        
        task.status = "running"
        task.pid = process.pid
        task.start_time = datetime.utcnow()
        db.commit()
        
        self.processes[site_name] = process
        return {"success": True, "pid": process.pid}
    
    def stop_crawler(self, site_name: str, db: Session):
        task = db.query(CrawlerTask).filter(CrawlerTask.site_name == site_name).first()
        if not task or task.status != "running":
            return {"success": False, "message": "Crawler not running"}
        
        # 终止进程
        if task.pid and psutil.pid_exists(task.pid):
            process = psutil.Process(task.pid)
            process.terminate()
        
        # 更新状态
        task.status = "stopped"
        task.pid = None
        db.commit()
        
        if site_name in self.processes:
            del self.processes[site_name]
        
        return {"success": True}
    
    def get_status(self, db: Session):
        tasks = db.query(CrawlerTask).all()
        result = {}
        for task in tasks:
            # 检查进程是否还存活
            if task.status == "running" and task.pid and not psutil.pid_exists(task.pid):
                task.status = "stopped"
                task.pid = None
                db.commit()
            
            result[task.site_name] = {
                "status": task.status,
                "pid": task.pid,
                "start_time": task.start_time,
                "last_run": task.last_run
            }
        return result

crawler_manager = CrawlerManager()