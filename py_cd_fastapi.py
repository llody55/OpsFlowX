#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import logging
import uvicorn
import subprocess
from config import ALLOWED_IPS, AUTH_TOKEN
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Header, Depends, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse

app = FastAPI()

# 禁用自动生成文档
#app = FastAPI(docs_url=None, redoc_url=None)

"""
安装组件：pip3 install fastapi uvicorn python-multipart -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
"""

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler("app.log", mode="a")  # 输出到文件
    ]
)

# 创建日志记录器
logger = logging.getLogger(__name__)

# 统一上传下载目录
UPLOAD_DIR = "/data/uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
    logger.info(f"上传目录 {UPLOAD_DIR} 已创建")

# 检查IP和Token的依赖函数
def check_auth(request: Request, authorization: str = Header(None)):
    # 获取客户端IP
    client_ip = request.client.host  # 直接获取客户端IP
    logger.info(f"来源IP: {client_ip}")

    # 如果使用了反向代理（如 Nginx），可以从请求头中获取真实IP
    if "X-Forwarded-For" in request.headers:
        client_ip = request.headers["X-Forwarded-For"].split(",")[0].strip()
    elif "X-Real-IP" in request.headers:
        client_ip = request.headers["X-Real-IP"]

    logger.info(f"请求端IP: {client_ip}")

    # 检查来源IP
    if client_ip not in ALLOWED_IPS:
        logger.warning(f"拒绝访问：IP {client_ip} 不在允许列表中")
        raise HTTPException(status_code=403, detail="Forbidden: IP not allowed")

    # 检查Token
    if authorization != AUTH_TOKEN:
        logger.warning("拒绝访问：无效的 Token")
        raise HTTPException(status_code=403, detail="Forbidden: Invalid token")

    logger.info("认证通过")
    return True

# 文件上传
@app.post("/upload")
async def upload_file(file: UploadFile = File(...), auth: bool = Depends(check_auth)):
    if not file:
        logger.warning("上传失败：未提供文件")
        raise HTTPException(status_code=400, detail="No file part")
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        logger.info(f"文件 {file.filename} 已上传到 {file_path}")
        return JSONResponse(content={"message": "File uploaded successfully"}, status_code=200)
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")

# 文件下载
@app.get("/download/{filename}")
async def download_file(filename: str, auth: bool = Depends(check_auth)):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        logger.error(f"下载失败：文件 {filename} 不存在")
        raise HTTPException(status_code=404, detail="File not found")

    logger.info(f"文件 {filename} 已成功提供下载")
    return FileResponse(file_path, filename=filename)

# 命令执行
@app.post("/execute")
async def execute_command(command: dict, auth: bool = Depends(check_auth)):
    if 'command' not in command:
        logger.warning("执行失败：未提供命令")
        raise HTTPException(status_code=400, detail="No command provided")

    # 获取当前主机的环境变量
    env = os.environ.copy()

    try:
        result = subprocess.run(command['command'], shell=True, capture_output=True, text=True, env=env)
        if result.returncode == 0:
            status = "success"
            logger.info(f"命令执行成功：{command['command']}")
        else:
            status = "failed"
            logger.error(f"命令执行失败：{command['command']}")

        output = f"Status: {status}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        return PlainTextResponse(content=output, status_code=200)
    except Exception as e:
        logger.exception(f"命令执行发生异常：{command['command']}")
        return JSONResponse(content={"error": str(e), "status": "failed"}, status_code=500)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=9002)
