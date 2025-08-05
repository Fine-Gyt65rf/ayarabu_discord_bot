FROM python:3.11
# backend ディレクトリに移動
WORKDIR /bot
# backend ディレクトリの内容を全てコピー
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt
COPY backend/ ./
CMD ["python", "main.py"]
