from telethon import TelegramClient, events
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
from telethon.tl.functions.users import GetFullUserRequest
import re
import asyncio

api_id = kendi api id gir
api_hash = 'kendi api hash gir'
client = TelegramClient('user_session', api_id, api_hash)

def read_groups():
    with open('group_usernames.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

async def search_in_group(group, query, is_id):
    try:
        entity = await client.get_entity(group)
        offset = 0
        while True:
            participants = await client(GetParticipantsRequest(
                channel=entity,
                filter=ChannelParticipantsSearch(''),
                offset=offset,
                limit=200,
                hash=0
            ))
            users = participants.users
            if not users:
                break
            for u in users:
                if (is_id and str(u.id) == query) or \
                   (not is_id and (
                        (u.username and u.username.lower() == query.lower().lstrip('@')) or
                        (u.first_name and query.lower() in u.first_name.lower()) or
                        (u.last_name and query.lower() in u.last_name.lower()) or
                        (u.first_name and u.last_name and query.lower() in f"{u.first_name} {u.last_name}".lower())
                   )):
                    return group, u.username or f"{u.first_name} {u.last_name}".strip() or str(u.id)
            if len(users) < 200:
                break
            offset += len(users)
            await asyncio.sleep(0.5)
    except Exception as e:
        print(f"[HATA] {group} grubunda tarama hatası: {e}")
        return None
    return None

async def search_in_groups(query):
    is_id = re.fullmatch(r'\d+', query) is not None
    groups = read_groups()
    tasks = [search_in_group(group, query, is_id) for group in groups]

    found_groups = []
    display_name = None
    for task in asyncio.as_completed(tasks):
        res = await task
        if res:
            group, username = res
            found_groups.append(group)
            display_name = username
            # Erken durdurmak istersen buraya break ekleyebilirsin
            # break

    return display_name or query, found_groups

@client.on(events.NewMessage(pattern=r'^/check\s+(.+)$'))
async def check_handler(event):
    query = event.pattern_match.group(1).strip()
    username, groups = await search_in_groups(query)
    if groups:
        msg = f"✅ **{username}** şu gruplarda bulundu:\n"
        msg += '\n'.join(f"- [@{g}](https://t.me/{g})" for g in groups)
    else:
        msg = f"❌ **{username}** hiçbir grupta bulunamadı."
    await event.reply(msg, parse_mode='md')

@client.on(events.NewMessage(pattern=r'^/userinfo\s+(.+)$'))
async def userinfo_handler(event):
    query = event.pattern_match.group(1).strip()
    try:
        user = await client.get_entity(query)
        full = await client(GetFullUserRequest(user.id))
        msg = f"👤 **Kullanıcı Bilgisi**\n"
        msg += f"• İsim: {user.first_name or ''} {user.last_name or ''}\n"
        msg += f"• Kullanıcı adı: @{user.username}\n" if user.username else ""
        msg += f"• ID: {user.id}\n"
        msg += f"• Bio: {full.full_user.about or 'Yok'}"
    except Exception as e:
        msg = f"❌ Kullanıcı bilgisi alınamadı: {e}"
    await event.reply(msg)

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    msg = (
        "Hoş geldin!\n"
        "Komutları şu şekilde kullanabilirsin:\n\n"
        "🔍 Kullanıcıyı gruplarda aramak için:\n"
        "`/check @kullaniciadi` veya `/check ID`\n\n"
        "ℹ️ Kullanıcı bilgilerini görmek için:\n"
        "`/userinfo @kullaniciadi`"
    )
    await event.respond(msg, parse_mode='md')

print("🚀 Bot başlatılıyor...")
client.start()
client.run_until_disconnected()
