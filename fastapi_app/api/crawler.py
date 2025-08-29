from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..core.crawler_manager import crawler_manager
from ..core.task_scheduler import task_scheduler

router = APIRouter(prefix="/crawler", tags=["crawler"])

class ScheduleRequest(BaseModel):
    interval_minutes: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "interval_minutes": 60
            }
        }

@router.post("/start/{site_name}")
def start_crawler(
    site_name: str,
    db: Session = Depends(get_db)
):
    """
    启动指定网站的爬虫
    
    参数说明:
    - site_name: 网站名称，支持以下值:
        - "gys": 中航信供应商平台
        - "travelsky": 中航信官网
        - "travelskyir": 中航信投资者关系网站
    
    返回:
    - success: 布尔值，表示是否启动成功
    - pid: 进程ID（启动成功时）
    - message: 错误信息（启动失败时）
    
    示例:
    POST /crawler/start/gys
    """
    if site_name not in ["gys", "travelsky", "travelskyir"]:
        raise HTTPException(status_code=400, detail="无效的网站名称，支持: gys, travelsky, travelskyir")
    
    return crawler_manager.start_crawler(site_name, db)

@router.post("/stop/{site_name}")
def stop_crawler(
    site_name: str, 
    db: Session = Depends(get_db)
):
    """
    停止指定网站的爬虫
    
    参数说明:
    - site_name: 网站名称，支持: gys, travelsky, travelskyir
    
    返回:
    - success: 布尔值，表示是否停止成功
    - message: 错误信息（停止失败时）
    
    示例:
    POST /crawler/stop/gys
    """
    if site_name not in ["gys", "travelsky", "travelskyir"]:
        raise HTTPException(status_code=400, detail="无效的网站名称，支持: gys, travelsky, travelskyir")
    
    return crawler_manager.stop_crawler(site_name, db)

@router.get("/status")
def get_crawler_status(db: Session = Depends(get_db)):
    """
    查看所有爬虫的运行状态
    
    返回:
    - 包含所有网站爬虫状态的字典
    - 每个网站包含: status(running/stopped/error), pid, start_time, last_run
    
    示例响应:
    {
        "gys": {
            "status": "running",
            "pid": 12345,
            "start_time": "2024-01-01T10:00:00",
            "last_run": "2024-01-01T10:00:00"
        },
        "travelsky": {
            "status": "stopped",
            "pid": null,
            "start_time": null,
            "last_run": "2024-01-01T09:00:00"
        }
    }
    """
    return crawler_manager.get_status(db)

@router.post("/schedule/{site_name}")
def schedule_crawler(
    site_name: str, 
    request: ScheduleRequest,
    db: Session = Depends(get_db)
):
    """
    设置爬虫定时任务
    
    参数说明:
    - site_name: 网站名称，支持: gys, travelsky, travelskyir
    - interval_minutes: 执行间隔（分钟），最小值: 10分钟
    
    请求体示例:
    {
        "interval_minutes": 60
    }
    
    返回:
    - success: 布尔值
    - message: 成功或错误信息
    
    注意: 间隔时间建议设置为30分钟以上，避免对目标网站造成过大压力
    """
    if site_name not in ["gys", "travelsky", "travelskyir"]:
        raise HTTPException(status_code=400, detail="无效的网站名称")
    
    if request.interval_minutes < 10:
        raise HTTPException(status_code=400, detail="间隔时间不能少于10分钟")
    
    return task_scheduler.schedule_crawler(site_name, request.interval_minutes)

@router.delete("/schedule/{site_name}")
def remove_schedule(site_name: str):
    """
    删除爬虫定时任务
    
    参数说明:
    - site_name: 网站名称，支持: gys, travelsky, travelskyir
    
    返回:
    - success: 布尔值
    - message: 成功或错误信息
    """
    if site_name not in ["gys", "travelsky", "travelskyir"]:
        raise HTTPException(status_code=400, detail="无效的网站名称")
    
    return task_scheduler.remove_schedule(site_name)

@router.get("/schedules")
def get_schedules():
    """
    查看所有定时任务
    
    返回:
    - success: 布尔值
    - data: 定时任务列表，包含:
        - site_name: 网站名称
        - next_run: 下次运行时间
        - trigger: 触发器信息
    
    示例响应:
    {
        "success": true,
        "data": [
            {
                "site_name": "gys",
                "next_run": "2024-01-01T11:00:00",
                "trigger": "interval[0:01:00]"
            }
        ]
    }
    """
    return task_scheduler.get_schedules()