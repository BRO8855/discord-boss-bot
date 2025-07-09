import discord
from discord.ext import tasks
import datetime
import json
import os
TOKEN = os.getenv('TOKEN')
from boss_data import boss_intervals, boss_delays

DATA_FILE = 'boss_data.json'
CHANNEL_ID = 1358993176660152423

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

boss_data = {}
manual_updated_bosses = set()

# 略称辞書
boss_aliases = {}
boss_aliases.update(dict.fromkeys(["アンドラス", "アンド"], "アンドラス"))
boss_aliases.update(dict.fromkeys(["ウカンバ", "水"], "ウカンバ"))
boss_aliases.update(dict.fromkeys(["エンクラ"], "エンクラ"))
boss_aliases.update(dict.fromkeys(["オルクス"], "オルクス"))
boss_aliases.update(dict.fromkeys(["オルフェン"], "オルフェン"))
boss_aliases.update(dict.fromkeys(["カタン"], "カタン"))
boss_aliases.update(dict.fromkeys(["カブリオ"], "カブリオ"))
boss_aliases.update(dict.fromkeys(["ガレス"], "ガレス"))
boss_aliases.update(dict.fromkeys(["クイーンアント", "クイアン", "QA", "あり", "アリ", "蟻"], "クイーンアント"))
boss_aliases.update(dict.fromkeys(["グラーキ", "グラ"], "グラーキ"))
boss_aliases.update(dict.fromkeys(["ケルソス", "ケル"], "ケルソス"))
boss_aliases.update(dict.fromkeys(["コアサセプタ", "コア", "サセプタ"], "コアサセプタ"))
boss_aliases.update(dict.fromkeys(["コルーン"], "コルーン"))
boss_aliases.update(dict.fromkeys(["サイラックス", "サイラ"], "サイラックス"))
boss_aliases.update(dict.fromkeys(["サヴァン"], "サヴァン"))
boss_aliases.update(dict.fromkeys(["サミュエル", "サミュ"], "サミュエル"))
boss_aliases.update(dict.fromkeys(["サルカ"], "サルカ"))
boss_aliases.update(dict.fromkeys(["シーラー", "風"], "シーラー"))
boss_aliases.update(dict.fromkeys(["スタン"], "スタン"))
boss_aliases.update(dict.fromkeys(["セル"], "セル"))
boss_aliases.update(dict.fromkeys(["タナトス"], "タナトス"))
boss_aliases.update(dict.fromkeys(["タラキン", "タラ"], "タラキン"))
boss_aliases.update(dict.fromkeys(["タルキン", "タル"], "タルキン"))
boss_aliases.update(dict.fromkeys(["チェルトゥバ", "チェル"], "チェルトゥバ"))
boss_aliases.update(dict.fromkeys(["ティミトリス", "トリス"], "ティミトリス"))
boss_aliases.update(dict.fromkeys(["ティミニエル", "ニエル"], "ティミニエル"))
boss_aliases.update(dict.fromkeys(["テンペスト", "テンペ"], "テンペスト"))
boss_aliases.update(dict.fromkeys(["ドラゴンビースト", "ドラビ", "DB"], "ドラゴンビースト"))
boss_aliases.update(dict.fromkeys(["トロンバ", "トロ"], "トロンバ"))
boss_aliases.update(dict.fromkeys(["ナイアス"], "ナイアス"))
boss_aliases.update(dict.fromkeys(["ノルムス", "地", "土"], "ノルムス"))
boss_aliases.update(dict.fromkeys(["ハーフ"], "ハーフ"))
boss_aliases.update(dict.fromkeys(["バシラ"], "バシラ"))
boss_aliases.update(dict.fromkeys(["バラック"], "バラック"))
boss_aliases.update(dict.fromkeys(["バルボ"], "バルボ"))
boss_aliases.update(dict.fromkeys(["バロン"], "バロン"))
boss_aliases.update(dict.fromkeys(["パンドライド", "パンドラ", "パンド"], "パンドライド"))
boss_aliases.update(dict.fromkeys(["パンナロード", "パンナ"], "パンナロード"))
boss_aliases.update(dict.fromkeys(["ヒシルローメ", "ヒシ", "ヒシル"], "ヒシルローメ"))
boss_aliases.update(dict.fromkeys(["フェニックス", "フェニ"], "フェニックス"))
boss_aliases.update(dict.fromkeys(["フェリス", "猫"], "フェリス"))
boss_aliases.update(dict.fromkeys(["ブラックリリー", "リリー", "リリ"], "ブラックリリー"))
boss_aliases.update(dict.fromkeys(["フリント"], "フリント"))
boss_aliases.update(dict.fromkeys(["ブレカ"], "ブレカ"))
boss_aliases.update(dict.fromkeys(["ヘカトン"], "ヘカトン"))
boss_aliases.update(dict.fromkeys(["ベヒモス", "ベヒ"], "ベヒモス"))
boss_aliases.update(dict.fromkeys(["マトゥラ", "マト"], "マトゥラ"))
boss_aliases.update(dict.fromkeys(["モデウス", "モデ"], "モデウス"))
boss_aliases.update(dict.fromkeys(["ミュータントクルマ", "MK", "ミュー", "ミュークル"], "ミュータントクルマ"))
boss_aliases.update(dict.fromkeys(["ムーフ", "闇"], "ムーフ"))
boss_aliases.update(dict.fromkeys(["メデューサ", "メデ", "メデュ"], "メデューサ"))
boss_aliases.update(dict.fromkeys(["ラーハ"], "ラーハ"))
boss_aliases.update(dict.fromkeys(["ランドール", "ランド"], "ランドール"))
boss_aliases.update(dict.fromkeys(["レピロ"], "レピロ"))
boss_aliases.update(dict.fromkeys(["汚染したクルマ", "汚染"], "汚染したクルマ"))
boss_aliases.update(dict.fromkeys(["忘却の鏡", "忘却", "鏡"], "忘却の鏡"))

def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            boss: {
                "next": data["next"].strftime('%Y-%m-%d %H:%M'),
                "interval": data["interval"]
            } for boss, data in boss_data.items()
        }, f, ensure_ascii=False, indent=2)

def load_data():
    if not os.path.exists(DATA_FILE):
        return
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        raw = json.load(f)
        for boss, data in raw.items():
            next_time = datetime.datetime.strptime(data["next"], '%Y-%m-%d %H:%M')
            boss_data[boss] = {
                "next": next_time,
                "interval": data["interval"]
            }

@bot.event
async def on_ready():
    load_data()
    print(f"{bot.user} がログインしました")
    notify_bosses.start()
    weekly_reset.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.strip()
    now = datetime.datetime.now()
    channel = bot.get_channel(CHANNEL_ID)

    # clear
    if content.lower() == "clear":
        base_time = now.replace(hour=5, minute=0, second=0, microsecond=0)
        for boss in boss_intervals:
            interval_minutes = boss_intervals[boss]
            delay_minutes = boss_delays.get(boss, 0)
            first_spawn = base_time + datetime.timedelta(minutes=delay_minutes)
            boss_data[boss] = {
                "next": first_spawn,
                "interval": interval_minutes
            }
        manual_updated_bosses.clear()
        save_data()
        if channel:
            await channel.send(f"🧹 全ボスの湧き時間を {base_time.strftime('%Y-%m-%d %H:%M')} 基準でリセットしました。")
        return

    # reset
    if content.lower().startswith("reset"):
        parts = content.split()
        if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) == 12:
            try:
                y = int(parts[1][:4])
                m = int(parts[1][4:6])
                d = int(parts[1][6:8])
                h = int(parts[1][8:10])
                mi = int(parts[1][10:12])
                base_time = datetime.datetime(year=y, month=m, day=d, hour=h, minute=mi)
                for boss in boss_intervals:
                    if boss not in manual_updated_bosses:
                        interval_minutes = boss_intervals[boss]
                        delay_minutes = boss_delays.get(boss, 0)
                        first_spawn = base_time + datetime.timedelta(minutes=delay_minutes)
                        boss_data[boss] = {
                            "next": first_spawn,
                            "interval": interval_minutes
                        }
                save_data()
                if channel:
                    await channel.send(f"🧹 {base_time.strftime('%Y-%m-%d %H:%M')} 基準でリセットしました。")
            except ValueError:
                if channel:
                    await channel.send("⚠️ 日付フォーマットが正しくありません。")
            return

    # list
    if content.lower() == "list":
        three_hours_later = now + datetime.timedelta(hours=3)
        notify_list = []
        for boss, data in boss_data.items():
            spawn_time = data["next"]
            if now <= spawn_time <= three_hours_later:
                notify_list.append((spawn_time, boss))
        if notify_list:
            notify_list.sort(key=lambda x: x[0])
            msg = "\n".join(f"{t.strftime('%H:%M')}/{b}" for t, b in notify_list)
            if channel:
                await channel.send("🔔 **ボス一覧(3時間以内)**：\n" + msg)
        else:
            if channel:
                await channel.send("📝 3時間以内に湧くボスはありません。")
        return

    # ボス名 + 時刻
    parts = content.split()
    if len(parts) == 2:
        boss, time_str = parts
        boss = boss_aliases.get(boss, boss)
        if boss in boss_intervals and time_str.isdigit() and len(time_str) == 4:
            try:
                hour = int(time_str[:2])
                minute = int(time_str[2:])
                if not (0 <= hour < 24 and 0 <= minute < 60):
                    raise ValueError()
                base_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                interval_minutes = boss_intervals[boss]
                next_spawn = base_time + datetime.timedelta(minutes=interval_minutes)
                boss_data[boss] = {"next": next_spawn, "interval": interval_minutes}
                manual_updated_bosses.add(boss)
                save_data()
                if channel:
                    await channel.send(
                        f"✅ 登録「{boss}」\n"
                        f"討伐:{base_time.strftime('%m-%d %H:%M')}\n"
                        f"次回:{next_spawn.strftime('%m-%d %H:%M')}"
                    )
            except ValueError:
                pass
        return

    # ボス名だけ
    if len(parts) == 1:
        boss = parts[0]
        boss = boss_aliases.get(boss, boss)
        if boss in boss_intervals:
            base_time = now.replace(second=0, microsecond=0)
            interval_minutes = boss_intervals[boss]
            next_spawn = base_time + datetime.timedelta(minutes=interval_minutes)
            boss_data[boss] = {"next": next_spawn, "interval": interval_minutes}
            manual_updated_bosses.add(boss)
            save_data()
            if channel:
                await channel.send(
                    f"✅ 登録「{boss}」\n"
                    f"討伐:{base_time.strftime('%m-%d %H:%M')}\n"
                    f"次回:{next_spawn.strftime('%m-%d %H:%M')}"
                )
        return

@tasks.loop(minutes=1)
async def notify_bosses():
    now = datetime.datetime.now()
    if now.minute != 0:
        return
    upcoming = now + datetime.timedelta(hours=3)
    notify_list = []
    for boss, data in boss_data.items():
        spawn_time = data["next"]
        if now <= spawn_time <= upcoming:
            notify_list.append((spawn_time, boss))
        elif spawn_time < now:
            next_spawn = spawn_time + datetime.timedelta(minutes=data["interval"])
            boss_data[boss]["next"] = next_spawn
            save_data()
    if notify_list:
        notify_list.sort(key=lambda x: x[0])
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            msg = "\n".join(f"{t.strftime('%H:%M')}/{b}" for t, b in notify_list)
            await channel.send("🔔 **ボス一覧**：\n" + msg)

@tasks.loop(hours=1)
async def weekly_reset():
    now = datetime.datetime.now()
    if now.weekday() == 2 and now.hour == 5:
        base_time = now.replace(minute=0, second=0, microsecond=0)
        for boss in boss_intervals:
            interval_minutes = boss_intervals[boss]
            delay_minutes = boss_delays.get(boss, 0)
            first_spawn = base_time + datetime.timedelta(minutes=delay_minutes)
            boss_data[boss] = {"next": first_spawn, "interval": interval_minutes}
        manual_updated_bosses.clear()
        save_data()
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await channel.send("🔄 毎週水曜 5:00 に全ボスをリセットしました。")

bot.run(TOKEN)
