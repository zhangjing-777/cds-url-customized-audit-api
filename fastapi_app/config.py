from pydantic_settings import BaseSettings
from typing import Dict, ClassVar
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class Settings(BaseSettings):
    # 这些是可以通过环境变量配置的字段
    database_url: str = "postgresql://username:password@localhost:5432/crawler_db"
    audit_service_url: str = "http://localhost:8004"
    
    # 这些是固定的配置，使用 ClassVar
    crawler_configs: ClassVar[Dict[str, str]] = {
        "gys": "./gys_travelsky_com_cn/config.ini",
        "travelsky": "./travelsky_cn/config.ini", 
        "travelskyir": "./travelskyir_com/config.ini"
    }
    
    data_paths: ClassVar[Dict[str, str]] = {
        "gys": "./gys_travelsky_com_cn/data",
        "travelsky": "./travelsky_cn/data",
        "travelskyir": "./travelskyir_com/data"
    }
    
    crawler_scripts: ClassVar[Dict[str, str]] = {
        "gys": "./gys_travelsky_com_cn/gys_travelsky_com_cn.py",
        "travelsky": "./travelsky_cn/travelsky_cn.py",
        "travelskyir": "./travelskyir_com/travelskyir_com.py"
    }
    
    class Config:
        env_file = ".env"

settings = Settings()