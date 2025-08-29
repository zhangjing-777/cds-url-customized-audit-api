from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from datetime import datetime
from .config import settings
import logging

logger = logging.getLogger(__name__)

def create_database_engine():
    """创建数据库引擎，使用psycopg3"""
    try:
        # 使用 postgresql+psycopg 驱动 (psycopg3)
        db_url = settings.database_url
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        
        engine = create_engine(
            db_url,
            echo=False,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=0,
            pool_recycle=3600,
            pool_pre_ping=True,
            # psycopg3 特定参数
            connect_args={
                "server_settings": {
                    "application_name": "spider_management_api",
                    "client_encoding": "utf8"
                }
            }
        )
        
        # 测试连接
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            result.fetchone()
        
        logger.info(f"✅ 数据库连接成功 (psycopg3): {settings.database_url}")
        return engine
        
    except Exception as e:
        logger.error(f"❌ psycopg3数据库连接失败: {e}")
        
        # 尝试使用psycopg2备选
        try:
            db_url_psycopg2 = settings.database_url
            if "postgresql+psycopg://" in db_url_psycopg2:
                db_url_psycopg2 = db_url_psycopg2.replace("postgresql+psycopg://", "postgresql://", 1)
            
            engine = create_engine(
                db_url_psycopg2,
                echo=False,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_recycle=3600,
                pool_pre_ping=True,
            )
            
            # 测试连接
            with engine.connect() as connection:
                result = connection.execute("SELECT 1")
                result.fetchone()
            
            logger.info(f"✅ 数据库连接成功 (psycopg2备选): {settings.database_url}")
            return engine
            
        except Exception as e2:
            logger.error(f"❌ psycopg2备选连接也失败: {e2}")
            
            # 最后备选方案：SQLite
            sqlite_path = "sqlite:///./crawler.db"
            engine = create_engine(
                sqlite_path,
                connect_args={"check_same_thread": False},
                echo=False
            )
            logger.info(f"使用SQLite备选数据库: {sqlite_path}")
            return engine

# 创建数据库引擎
engine = create_database_engine()
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

