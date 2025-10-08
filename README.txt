✅ Koyeb用Discord BOTデプロイパッケージ（修正版）

【修正内容】
- Procfileで python -> python3 に修正
- .python-version を追加（Python 3.13を指定）

【使い方】
1. ZIPを展開してGitHubリポジトリ直下に配置
2. git add . && git commit -m 'Add Koyeb deploy files' && git push
3. KoyebでBuild method を Python / Procfile に設定してデプロイ
4. 環境変数 DISCORD_TOKEN を設定
5. RedeployでBOTが常時稼働します
