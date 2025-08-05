FROM python:3.11
WORKDIR /bot
# requirements.txt のみを先にコピーしてインストール
COPY requirements.txt .
RUN pip install -r requirements.txt
# その他のファイルをコピー
COPY . .
# Renderがウェブサービスとして認識できるよう、CMDをGunicornに設定する
CMD gunicorn -w 4 -b 0.0.0.0:8000 main:app
