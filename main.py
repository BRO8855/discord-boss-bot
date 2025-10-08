import discord
from discord.ext import tasks
import datetime
import json
import os
from dotenv import load_dotenv
from boss_data import boss_intervals, boss_delays  # 事前に作成済みとする

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DATA_FILE = 'boss_data.json'
AUTO_CLEAR_FILE = 'auto_clear_flag.json'
BOSS_ALIAS_FILE = 'boss_aliases.json'

# 管理するチャンネルリスト
CHANNELS = [1358993176660152423, 1409751384257073284, 1409751416603541585, 1409751447620288532, 1409751475067949117]

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# --- チャンネルごとのデータ ---
boss_data_per_channel = {}
manual_updated_per_channel = {}

# --- boss_aliases ---
def load_boss_aliases(file_path=BOSS_ALIAS_FILE):
    aliases = {}
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for official_name, names in data.items():
                for name in names:
                    aliases[name] = official_name
    return aliases

boss_aliases = load_boss_aliases()

# --- データ保存/読み込み ---
def save_data():
    json_data = {}
    for ch_id, data in boss_data_per_channel.items():
        json_data[str(ch_id)] = {
            boss: {"next": v["next"].strftime('%Y-%m-%d %H:%M'), "interval": v["interval"]}
            for boss, v in data.items()
        }
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

def load_data():
    global boss_data_per_channel, manual_updated_per_channel
    if not os.path.exists(DATA_FILE):
        return
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        raw = json.load(f)
        for ch_id_str, data in raw.items():
            ch_id = int(ch_id_str)
            boss_data_per_channel[ch_id] = {}
            manual_updated_per_channel[ch_id] = set()
            for boss, v in data.items():
                next_time = datetime.datetime.strptime(v["next"], '%Y-%m-%d %H:%M')
                boss_data_per_channel[ch_id][boss] = {"next": next_time, "interval": v["interval"]}

# --- auto_clear_flag.json ---
def get_last_clear_week(channel_id):
    if os.path.exists(AUTO_CLEAR_FILE):
        with open(AUTO_CLEAR_FILE, 'r') as f:
            data = json.load(f)
            return data.get(str(channel_id), 0)
    return 0

def set_last_clear_week(channel_id, week_number):
    data = {}
    if os.path.exists(AUTO_CLEAR_FILE):
        with open(AUTO_CLEAR_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    data[str(channel_id)] = week_number
    with open(AUTO_CLEAR_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- clear関数（今日5:00基準でリセット） ---
async def clear_boss_data(channel_id):
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))  # JST
    base_time = now.replace(hour=5, minute=0, second=0, microsecond=0)

    boss_data_per_channel[channel_id] = {}
    manual_updated_per_channel[channel_id] = set()

    for boss in boss_intervals:
        interval_minutes = boss_intervals[boss]
        delay_minutes = boss_delays.get(boss, 0)
        first_spawn = base_time + datetime.timedelta(minutes=delay_minutes)
        boss_data_per_channel[channel_id][boss] = {"next": first_spawn, "interval": interval_minutes}

    save_data()
    channel = client.get_channel(channel_id)
    if channel:
        await channel.send(f"🧹 全ボスの湧き時間を {base_time.strftime('%Y-%m-%d %H:%M')} JST 基準でリセットしました。")

# --- maintenance関数（入力時刻基準） ---
async def maintenance_reset(channel_id, base_time):
    boss_data_per_channel[channel_id] = {}
    manual_updated_per_channel[channel_id] = set()
    for boss in boss_intervals:
        interval_minutes = boss_intervals[boss]
        delay_minutes = boss_delays.get(boss, 0)
        first_spawn = base_time + datetime.timedelta(minutes=delay_minutes)
        boss_data_per_channel[channel_id][boss] = {"next": first_spawn, "interval": interval_minutes}
    save_data()
    channel = client.get_channel(channel_id)
    if channel:
        await channel.send(f"🛠 メンテナンス基準でリセットしました（{base_time.strftime('%Y-%m-%d %H:%M')} JST）")

# --- 起動時処理 ---
@client.event
async def on_ready():
    load_data()
    print(f'Logged in as {client.user}')

    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    week_number = now.isocalendar()[1]

    for ch_id in CHANNELS:
        if ch_id not in boss_data_per_channel:
            boss_data_per_channel[ch_id] = {}
            manual_updated_per_channel[ch_id] = set()

        # 水曜5時以降の初回起動で自動クリア
        if now.weekday() == 2 and now.hour >= 5 and get_last_clear_week(ch_id) != week_number:
            await clear_boss_data(ch_id)
            set_last_clear_week(ch_id, week_number)

    notify_bosses.start()
    weekly_reset.start()

# --- メッセージ処理 ---
@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id not in CHANNELS:
        return

    ch_id = message.channel.id
    boss_data = boss_data_per_channel[ch_id]
    manual_updated = manual_updated_per_channel[ch_id]

    content = message.content.strip()
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    channel = message.channel

    # clearコマンド
    if content.lower() == "clear":
        await clear_boss_data(ch_id)
        return

    # maintenanceコマンド
    if content.lower() == "maintenance":
        base_time = now.replace(second=0, microsecond=0)
        await maintenance_reset(ch_id, base_time)
        return

    # ボス登録（時間+オプション-1）
    parts = content.split()
    if len(parts) >= 2:
        boss_name = boss_aliases.get(parts[0], parts[0])
        time_str = parts[1]
        day_offset = -1 if len(parts) >= 3 and parts[2] == "-1" else 0

        if boss_name in boss_intervals and time_str.isdigit() and len(time_str) == 4:
            try:
                hour = int(time_str[:2])
                minute = int(time_str[2:])
                base_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + datetime.timedelta(days=day_offset)
                interval_minutes = boss_intervals[boss_name]
                next_spawn = base_time + datetime.timedelta(minutes=interval_minutes)

                boss_data[boss_name] = {"next": next_spawn, "interval": interval_minutes}
                manual_updated.add(boss_name)
                save_data()

                await channel.send(f"✅ {boss_name} の次の湧き時間を {next_spawn.strftime('%H:%M')} JST に更新しました。")
            except ValueError:
                await channel.send("⚠️ 時刻の形式が正しくありません。")

# --- 通知タスク ---
@tasks.loop(minutes=1)
async def notify_bosses():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    if now.minute != 0:
        return

    for ch_id in CHANNELS:
        boss_data = boss_data_per_channel[ch_id]
        upcoming = now + datetime.timedelta(hours=3)
        notify_list = []
        for boss, v in boss_data.items():
            spawn_time = v["next"]
            if now <= spawn_time <= upcoming:
                notify_list.append((spawn_time, boss))
            elif spawn_time < now:
                boss_data[boss]["next"] = spawn_time + datetime.timedelta(minutes=v["interval"])
                save_data()
        if notify_list:
            notify_list.sort(key=lambda x: x[0])
            channel = client.get_channel(ch_id)
            if channel:
                msg = "\n".join(f"{t.strftime('%H:%M')}/{b}" for t, b in notify_list)
                await channel.send("🔔 **ボス一覧**：\n" + msg)

# --- 毎週水曜5時リセット ---
@tasks.loop(hours=1)
async def weekly_reset():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    if now.weekday() == 2 and now.hour == 5:
        for ch_id in CHANNELS:
            await clear_boss_data(ch_id)
            week_number = now.isocalendar()[1]
            set_last_clear_week(ch_id, week_number)

client.run(TOKEN)
