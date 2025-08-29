from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..core.audit_manager import audit_manager

router = APIRouter(prefix="/audit", tags=["audit"])

@router.post("/start/{site_name}/{date}")
def start_audit(
    site_name: str, 
    date: str, 
    db: Session = Depends(get_db)
):
    """
    对指定网站的指定日期内容执行审核
    
    参数说明:
    - site_name: 网站名称，支持: gys, travelsky, travelskyir
    - date: 爬取时间目录名，格式: YYYY-MM-DD_HH_MM_SS
    
    返回:
    - success: 布尔值
    - task_id: 审核任务ID，用于查询任务状态
    - message: 错误信息（失败时）
    
    示例:
    POST /audit/start/gys/2024-01-01_10_30_15
    
    响应示例:
    {
        "success": true,
        "task_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    
    注意: 
    - 审核是异步执行的，需要通过task_id查询进度
    - 审核包括图片内容检测、文本敏感词检测、OCR文字识别
    """
    if site_name not in ["gys", "travelsky", "travelskyir"]:
        raise HTTPException(status_code=400, detail="无效的网站名称")
    
    # 验证日期格式
    try:
        from datetime import datetime
        datetime.strptime(date, "%Y-%m-%d_%H_%M_%S")
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为: YYYY-MM-DD_HH_MM_SS")
    
    return audit_manager.start_audit(site_name, date, db)

@router.get("/status/{task_id}")
def get_audit_status(
    task_id: str, 
    db: Session = Depends(get_db)
):
    """
    查看审核任务状态
    
    参数说明:
    - task_id: 审核任务ID，从start_audit接口获得
    
    返回:
    - success: 布尔值
    - data: 任务详情
        - task_id: 任务ID
        - status: 任务状态 (pending/running/completed/failed)
        - progress: 进度百分比 (0-100)
        - results: 结果信息
        - created_at: 创建时间
    
    示例:
    GET /audit/status/550e8400-e29b-41d4-a716-446655440000
    
    响应示例:
    {
        "success": true,
        "data": {
            "task_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "running",
            "progress": 45,
            "results": null,
            "created_at": "2024-01-01T10:30:15"
        }
    }
    """
    return audit_manager.get_task_status(task_id, db)

@router.get("/results/{site_name}")
def get_audit_results(
    site_name: str, 
    limit: Optional[int] = Query(10, description="返回记录数量限制", ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    查看指定网站的所有审核结果概览
    
    参数说明:
    - site_name: 网站名称，支持: gys, travelsky, travelskyir
    - limit: 可选，返回记录数量，默认10条，最多100条
    
    返回:
    - success: 布尔值
    - data: 审核结果列表，按创建时间倒序
        - task_id: 任务ID
        - date_folder: 爬取时间目录
        - status: 审核状态
        - progress: 进度
        - created_at: 创建时间
    
    示例:
    GET /audit/results/gys?limit=20
    """
    if site_name not in ["gys", "travelsky", "travelskyir"]:
        raise HTTPException(status_code=400, detail="无效的网站名称")
    
    result = audit_manager.get_audit_results(site_name, db)
    if result["success"] and limit:
        result["data"] = result["data"][:limit]
    
    return result

@router.get("/results/detailed/{task_id}")
def get_detailed_audit_results(
    task_id: str, 
    db: Session = Depends(get_db)
):
    """
    获取任务的详细审核结果
    
    参数说明:
    - task_id: 审核任务ID
    
    返回:
    - success: 布尔值
    - data: 详细审核结果
        - total_files: 总文件数
        - sensitive_files: 敏感文件数
        - image_files: 图片文件数
        - text_files: 文本文件数
        - details: 详细列表
            - page_name: 页面名称
            - file_type: 文件类型
            - file_name: 文件名
            - is_sensitive: 是否敏感
            - confidence: 置信度
            - 图片特有字段: is_abnormal_window, porn_score, sexy_score, ocr_text
            - 文本特有字段: sensitive_words
    
    示例:
    GET /audit/results/detailed/550e8400-e29b-41d4-a716-446655440000
    
    响应示例:
    {
        "success": true,
        "data": {
            "total_files": 25,
            "sensitive_files": 2,
            "image_files": 15,
            "text_files": 10,
            "details": [
                {
                    "page_name": "home",
                    "file_type": "image",
                    "file_name": "banner.jpg",
                    "is_sensitive": false,
                    "confidence": 0.1,
                    "porn_score": 0.05,
                    "sexy_score": 0.03,
                    "ocr_text": "欢迎访问中航信"
                }
            ]
        }
    }
    """
    return audit_manager.get_detailed_results(task_id, db)

@router.get("/statistics/{site_name}")
def get_audit_statistics(
    site_name: str, 
    db: Session = Depends(get_db)
):
    """
    获取网站的审核统计信息
    
    参数说明:
    - site_name: 网站名称，支持: gys, travelsky, travelskyir
    
    返回:
    - success: 布尔值
    - data: 统计信息
        - site_name: 网站名称
        - total_images: 总图片数
        - total_texts: 总文本数
        - sensitive_images: 敏感图片数
        - sensitive_texts: 敏感文本数
        - sensitivity_rate: 敏感率
            - images: 图片敏感率 (0-1)
            - texts: 文本敏感率 (0-1)
    
    示例:
    GET /audit/statistics/gys
    
    响应示例:
    {
        "success": true,
        "data": {
            "site_name": "gys",
            "total_images": 150,
            "total_texts": 200,
            "sensitive_images": 5,
            "sensitive_texts": 8,
            "sensitivity_rate": {
                "images": 0.033,
                "texts": 0.040
            }
        }
    }
    """
    if site_name not in ["gys", "travelsky", "travelskyir"]:
        raise HTTPException(status_code=400, detail="无效的网站名称")
    
    from ..database import AuditResult
    
    # 统计敏感内容
    sensitive_images = db.query(AuditResult).filter(
        AuditResult.site_name == site_name,
        AuditResult.file_type == "image",
        AuditResult.is_sensitive == True
    ).count()
    
    sensitive_texts = db.query(AuditResult).filter(
        AuditResult.site_name == site_name,
        AuditResult.file_type == "text", 
        AuditResult.is_sensitive == True
    ).count()
    
    total_images = db.query(AuditResult).filter(
        AuditResult.site_name == site_name,
        AuditResult.file_type == "image"
    ).count()
    
    total_texts = db.query(AuditResult).filter(
        AuditResult.site_name == site_name,
        AuditResult.file_type == "text"
    ).count()
    
    return {
        "success": True,
        "data": {
            "site_name": site_name,
            "total_images": total_images,
            "total_texts": total_texts,
            "sensitive_images": sensitive_images,
            "sensitive_texts": sensitive_texts,
            "sensitivity_rate": {
                "images": sensitive_images / total_images if total_images > 0 else 0,
                "texts": sensitive_texts / total_texts if total_texts > 0 else 0
            }
        }
    }