from fastapi import FastAPI
#from .database import engine, Base
from .api import crawler, content, audit

# 创建数据库表
#Base.metadata.create_all(bind=engine)

app = FastAPI(title="Spider Management API", version="1.0.0")

# 注册路由
app.include_router(crawler.router)
app.include_router(content.router)
app.include_router(audit.router)

@app.get("/")
def root():
    return {"message": "Spider Management API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}