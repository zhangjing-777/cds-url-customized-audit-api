from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from .config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class CrawlerTask(Base):
    __tablename__ = "crawler_tasks"
    
    id = Column(Integer, primary_key=True)
    site_name = Column(String, nullable=False)
    status = Column(String, default="stopped")  # running, stopped, error
    pid = Column(Integer, nullable=True)
    start_time = Column(DateTime, nullable=True)
    last_run = Column(DateTime, nullable=True)

class AuditTask(Base):
    __tablename__ = "audit_tasks"
    
    id = Column(Integer, primary_key=True)
    task_id = Column(String, unique=True, nullable=False)
    site_name = Column(String, nullable=False)
    date_folder = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed
    progress = Column(Integer, default=0)
    results = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# 在现有代码后面添加以下表定义

class AuditResult(Base):
    __tablename__ = "audit_url_results"
    
    id = Column(Integer, primary_key=True)
    task_id = Column(String, nullable=False)  # 关联审核任务
    site_name = Column(String, nullable=False)
    date_folder = Column(String, nullable=False)
    page_name = Column(String, nullable=False)  # 页面名称
    file_type = Column(String, nullable=False)  # 'image' or 'text'
    file_path = Column(String, nullable=False)  # 文件路径
    file_name = Column(String, nullable=False)  # 文件名
    
    # 审核结果字段
    is_sensitive = Column(Boolean, default=False)  # 是否敏感
    confidence = Column(Float, nullable=True)  # 置信度
    
    # 图片审核结果
    is_abnormal_window = Column(Boolean, nullable=True)  # 是否异常窗口
    window_confidence = Column(Float, nullable=True)
    
    # 色情内容检测
    drawings_score = Column(Float, nullable=True)
    hentai_score = Column(Float, nullable=True)
    neutral_score = Column(Float, nullable=True)
    porn_score = Column(Float, nullable=True)
    sexy_score = Column(Float, nullable=True)
    
    # 文本审核结果
    sensitive_words = Column(Text, nullable=True)  # 敏感词列表
    
    # OCR结果
    ocr_text = Column(Text, nullable=True)  # 识别的文字内容
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 原始审核响应（JSON格式）
    raw_response = Column(Text, nullable=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()