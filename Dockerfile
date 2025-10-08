# Python公式イメージを使用
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# BOTのコードをコピー
COPY . .

# BOTを起動
CMD ["python", "app/bot.py"]
