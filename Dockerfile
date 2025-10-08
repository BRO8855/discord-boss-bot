# ベースイメージ
FROM node:18

# 作業ディレクトリを設定
WORKDIR /app

# package.json と package-lock.json を先にコピー
COPY package*.json ./

# 依存関係をインストール
RUN npm install

# ソースコードをコピー
COPY . .

# ポートを指定（必要なら）
EXPOSE 3000

# Bot起動コマンド
CMD ["node", "index.js"]
