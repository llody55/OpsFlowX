#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import logging
import subprocess
from config import ALLOWED_IPS, AUTH_TOKEN
from functools import wraps
from flask import Flask, request, send_file, jsonify, Response

app = Flask(__name__)


"""
安装组件：pip3 install flask -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
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

# 检查IP和Token的装饰器
def check_auth(func):
    @wraps(func) 
    def wrapper(*args, **kwargs):
        # 检查来源IP
        client_ip = request.remote_addr
        logging.info(f"来源IP: {client_ip}")
        if client_ip not in ALLOWED_IPS:
            return jsonify({"error": "Forbidden: IP not allowed"}), 403

        # 检查Token
        token = request.headers.get("Authorization")
        if token != AUTH_TOKEN:
            return jsonify({"error": "Forbidden: Invalid token"}), 403

        return func(*args, **kwargs)
    return wrapper

# 文件上传
@app.route('/upload', methods=['POST'])
@check_auth
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    file.save(file_path)
    return jsonify({"message": "File uploaded successfully"}), 200

# 文件下载
@app.route('/download/<filename>', methods=['GET'])
@check_auth
def download_file(filename):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    return send_file(file_path, as_attachment=True)

# 命令执行
@app.route('/execute', methods=['POST'])
@check_auth
def execute_command():
    data = request.json
    if 'command' not in data:
        return jsonify({"error": "No command provided"}), 400
    
    # 获取当前主机的环境变量
    env = os.environ.copy()

    try:
        result = subprocess.run(data['command'], shell=True, capture_output=True, text=True, env=env)
        if result.returncode == 0:
            status = "success"
        else:
            status = "failed"
         # 格式化输出
        output = (
            f"Status: {status}\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )
        return Response(output, status=200, mimetype="text/plain")
    except Exception as e:
        return jsonify({"error": str(e), "status": "failed"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)