from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from .database import engine, Base
from .api import crawler, content, audit
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Spider Management API", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动时检查数据库连接
@app.on_event("startup")
async def startup_event():
    try:
        # 使用文本SQL测试连接
        with engine.connect() as connection:
            from sqlalchemy import text
            result = connection.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()
            if test_value and test_value[0] == 1:
                logger.info("✅ 数据库连接验证成功")
            else:
                logger.warning("⚠️ 数据库连接测试返回异常结果")
        
    except Exception as e:
        logger.error(f"❌ 启动时数据库检查失败: {e}")

# 注册路由
app.include_router(crawler.router)
app.include_router(content.router)
app.include_router(audit.router)

@app.get("/")
def root():
    return {"message": "Spider Management API is running"}

@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            from sqlalchemy import text
            result = connection.execute(text("SELECT 1 as health"))
            test_value = result.fetchone()
            return {"status": "healthy", "database": "connected", "test_result": test_value[0] if test_value else None}
    except Exception as e:
        return {"status": "unhealthy", "database_error": str(e)}