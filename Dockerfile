FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 安装Python依赖
RUN pip install -r requirements.txt

# 创建日志目录
RUN mkdir -p logs

# 启动脚本
CMD ["python", "startup.py"]