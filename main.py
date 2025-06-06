from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
from telethon.tl.functions.users import GetFullUserRequest
import re

api_id = 24562058
api_hash = 'a5562428e856f01ac943de0d29036cde'
client = TelegramClient('user_session', api_id, api_hash)

def read_groups():
    with open('group_usernames.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

async def search_in_groups(query):
    is_id = re.fullmatch(r'\d+', query) is not None
    group_usernames = read_groups()
    found = []
    display_name = None

    for group in group_usernames:
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
                    if (is_id and str(u.id) == query) or (not is_id and u.username and u.username.lower() == query.lower().lstrip('@')):
                        display_name = u.username or str(u.id)
                        found.append(group)
                        break
                if len(users) < 200:
                    break
                offset += len(users)
        except Exception:
            continue

    return display_name or query, found

@client.on(events.NewMessage(pattern=r'^/check\s+(.+)$'))
async def check_handler(event):
    query = event.pattern_match.group(1).strip()
    username, groups = await search_in_groups(query)
    if groups:
        msg = f"✅ @{username} şu gruplarda bulundu:\n"
        msg += '\n'.join(f"- [@{g}](https://t.me/{g})" for g in groups)
    else:
        msg = f"❌ {query} hiçbir grupta bulunamadı."
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
    await event.respond(
        "Hoş geldin! Aşağıdaki komutlardan birini seç:",
        buttons=[
            [Button.inline("🔍 Kullanıcıyı Tara", b"check")],
            [Button.inline("ℹ️ Kullanıcı Bilgisi", b"info")]
        ]
    )

@client.on(events.CallbackQuery)
async def callback(event):
    if event.data == b"check":
        await event.edit("🔍 Lütfen şu şekilde gönder: `/check @kullaniciadi`", parse_mode='md')
    elif event.data == b"info":
        await event.edit("ℹ️ Lütfen şu şekilde gönder: `/userinfo @kullaniciadi`", parse_mode='md')

print("🚀 Bot başlatılıyor...")
client.start()
client.run_until_disconnected()
