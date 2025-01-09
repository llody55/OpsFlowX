### **OpsFlowX**

#### **项目简介** ：

OpsFlowX 是一个面向运维和持续部署（CD）场景的自动化工具，旨在通过简洁的API接口实现文件上传、下载和远程命令执行功能。可以用在流水线中，一键触发部署更新任务，或者巡检时，一键巡检并返回结果。

#### **核心功能** ：

* **文件上传** ：支持通过API接口快速上传文件到指定目录。
* **文件下载** ：提供安全的文件下载功能，确保文件传输的可靠性。
* **命令执行** ：支持远程执行Shell命令，并实时返回执行结果。
* **访问控制** ：基于IP白名单和Token认证，确保操作的安全性。

#### **适用场景** ：

* 快速部署脚本、配置文件传输等。
* 集成到CI/CD流水线中，实现自动化部署。
* 通过API接口管理远程服务器的文件和任务。
* 环境多，且都处于堡垒机保护下的环境。
* 绕过堡垒机对运维端的限制。

#### 使用方法：

##### docker部署示例

```bash
docker run -d --privileged  --name pycd -p 5000:5000 -v /root/py-cd/config.py:/app/config.py -v /var/run/docker.sock:/var/run/docker.sock  -v /data/uploads:/data/uploads -v /usr/bin/docker:/usr/bin/docker -v /usr/local/bin/docker-compose:/usr/local/bin/docker-compose  swr.cn-southwest-2.myhuaweicloud.com/llody/opsflowx:v20250109
```

##### 上传请求

```bash
curl -X POST -F "file=@/root/jdk-11.0.11_linux-x64_bin.tar.gz" -H "Authorization: 123456" http://192.168.1.225:5000/upload
```

> 默认存储在当前目录下的upload

##### 下载请求

```bash
curl -O  -H "Authorization: 123456" http://192.168.1.225:5000/download/jdk-11.0.11_linux-x64_bin.tar.gz
```

##### 命令执行请求

```bash
curl -X POST -H "Content-Type: application/json" -H "Authorization: 123456" -d '{"command": "rm /root/py-cd/jdk-11.0.11_linux-x64_bin.tar.gz &&rm /data/uploads/jdk-11.0.11_linux-x64_bin.tar.gz"}' http://192.168.1.225:5000/execute
```

##### 命令执行请求之-----变量传递

```bash
curl -X POST -H "Content-Type: application/json" -H "Authorization: 123456" \
-d '{"command": "export HW_PROD_SPACE_NAME=\"'"$HW_PROD_SPACE_NAME"'\"; echo ${HW_PROD_SPACE_NAME}"}' \
http://192.168.1.225:5000/execute
```

##### nginx代理示例

```nginx
server {
    listen      443 ssl;
    server_name ops.llody.top;
    client_max_body_size 1000m;
    ssl_certificate /etc/nginx/llody.top/llody.top.pem;
    ssl_certificate_key /etc/nginx/llody.top/llody.top.key;
    ssl_prefer_server_ciphers on;
  

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://192.168.1.225:5000;

        proxy_connect_timeout 60;
        proxy_read_timeout 1314;
        proxy_send_timeout 1314;

        proxy_redirect off;
        port_in_redirect off;
        proxy_buffering off;
    }
    location /docs {
        deny all;
        return 404;
    }

    location /redoc {
        deny all;
        return 404;
    }

    location /healthz {
        return 200;
  }
}

```
