from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, Boolean, Float
from sqlalchemy.dialects.postgresql.psycopg2 import PGDialect_psycopg2
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from datetime import datetime
from .config import settings
import logging

logger = logging.getLogger(__name__)

# 修补SQLAlchemy以支持openGauss
def patch_opengauss():
    """修补SQLAlchemy支持openGauss"""
       
    original_get_server_version_info = PGDialect_psycopg2._get_server_version_info
    
    def patched_get_server_version_info(self, connection):
        try:
            return original_get_server_version_info(self, connection)
        except AssertionError:
            # openGauss版本检查失败时，返回PostgreSQL 14.0
            logger.warning("检测到openGauss，使用PostgreSQL 14.0兼容模式")
            return (14, 0)
    
    PGDialect_psycopg2._get_server_version_info = patched_get_server_version_info

# 应用补丁
patch_opengauss()

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,  # 连接池类型
    pool_size=20,  # 连接池大小
    max_overflow=0,  # 最大溢出连接数
    pool_recycle=3600,  # 连接回收时间
    pool_pre_ping=True,  # 连接前ping测试
)
        

# 创建数据库引擎
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class CrawlerTask(Base):
    __tablename__ = "crawler_tasks"
    
    id = Column(Integer, primary_key=True)
    site_name = Column(String(255), nullable=False)
    status = Column(String(50), default="stopped")
    pid = Column(Integer, nullable=True)
    start_time = Column(DateTime, nullable=True)
    last_run = Column(DateTime, nullable=True)

class AuditTask(Base):
    __tablename__ = "audit_tasks"
    
    id = Column(Integer, primary_key=True)
    task_id = Column(String(255), unique=True, nullable=False)
    site_name = Column(String(255), nullable=False)
    date_folder = Column(String(255), nullable=False)
    status = Column(String(50), default="pending")
    progress = Column(Integer, default=0)
    results = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditResult(Base):
    __tablename__ = "audit_url_results"
    
    id = Column(Integer, primary_key=True)
    task_id = Column(String(255), nullable=False)
    site_name = Column(String(255), nullable=False)
    date_folder = Column(String(255), nullable=False)
    page_name = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_name = Column(String(255), nullable=False)
    is_sensitive = Column(Boolean, default=False)
    confidence = Column(Float, nullable=True)
    is_abnormal_window = Column(Boolean, nullable=True)
    window_confidence = Column(Float, nullable=True)
    drawings_score = Column(Float, nullable=True)
    hentai_score = Column(Float, nullable=True)
    neutral_score = Column(Float, nullable=True)
    porn_score = Column(Float, nullable=True)
    sexy_score = Column(Float, nullable=True)
    sensitive_words = Column(Text, nullable=True)
    ocr_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    raw_response = Column(Text, nullable=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

