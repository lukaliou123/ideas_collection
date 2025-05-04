FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖和curl（用于健康检查）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser && \
    # 创建数据目录并设置权限
    touch /app/app.db && \
    chown -R appuser:appuser /app

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["python", "main.py"] 