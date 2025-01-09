# 第一阶段
FROM --platform=$BUILDPLATFORM swr.cn-southwest-2.myhuaweicloud.com/llody/python:3.9.10-buster as builder

RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list
#RUN sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    gcc \
    lsb-release \
    libc6-dev \
    libsqlite3-dev \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

# 第二阶段
FROM --platform=$TARGETPLATFORM swr.cn-southwest-2.myhuaweicloud.com/llody/python:3.9.10-slim

LABEL maintainer="llody55"

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.9 /usr/local/lib/python3.9
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

EXPOSE 5000

ENV UPLOAD_DIR=/data/uploads

RUN mkdir -p ${UPLOAD_DIR}

CMD ["uvicorn", "py_cd_fastapi:app", "--host", "0.0.0.0", "--port", "5000"]