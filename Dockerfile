# 使用官方 Python 镜像作为基础镜像
FROM python:3.12.2-alpine

# 设置工作目录
WORKDIR /app

# 将当前目录中的文件添加到工作目录中
COPY . /app

# 复制依赖文件
COPY requirements.txt /app/

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 时区
ENV TZ="Asia/Shanghai"

#构建版本
ARG BUILD_SHA
ARG BUILD_TAG
ENV BUILD_SHA=$BUILD_SHA
ENV BUILD_TAG=$BUILD_TAG

# 端口
EXPOSE 5005

# 运行应用程序
CMD ["python", "./app/run.py"]