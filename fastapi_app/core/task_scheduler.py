from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from .crawler_manager import crawler_manager
from ..database import SessionLocal

class TaskScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
    
    def schedule_crawler(self, site_name: str, interval_minutes: int):
        job_id = f"crawler_{site_name}"
        
        # 删除已存在的任务
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        # 添加新的定时任务
        self.scheduler.add_job(
            func=self._run_scheduled_crawler,
            trigger=IntervalTrigger(minutes=interval_minutes),
            args=[site_name],
            id=job_id
        )
        
        return {"success": True, "message": f"Scheduled {site_name} every {interval_minutes} minutes"}
    
    def _run_scheduled_crawler(self, site_name: str):
        db = SessionLocal()
        try:
            crawler_manager.start_crawler(site_name, db)
        finally:
            db.close()
    
    def remove_schedule(self, site_name: str):
        job_id = f"crawler_{site_name}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            return {"success": True, "message": "Schedule removed"}
        return {"success": False, "message": "Schedule not found"}
    
    def get_schedules(self):
        jobs = []
        for job in self.scheduler.get_jobs():
            if job.id.startswith("crawler_"):
                site_name = job.id.replace("crawler_", "")
                jobs.append({
                    "site_name": site_name,
                    "next_run": job.next_run_time,
                    "trigger": str(job.trigger)
                })
        return {"success": True, "data": jobs}

task_scheduler = TaskScheduler()