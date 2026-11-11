# Render(또는 Docker 지원 호스팅)용. 로컬: docker build -t mirinohu-api . && docker run -p 7860:7860 mirinohu-api
# 포트는 호스팅이 주는 PORT 환경변수를 따르고, 없으면 7860.
FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 user
USER user
WORKDIR /home/user/app
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
COPY --chown=user app ./app
ENV PATH=/home/user/.local/bin:$PATH \
    ALLOWED_ORIGINS=https://mirinohulab.github.io
EXPOSE 7860
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860} --no-access-log"]
