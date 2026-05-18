import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped
from yt_dlp import YoutubeDL

# ================== CONFIG ==================

API_ID = 35384207
API_HASH = "09c4bc9de62a417ccdd0c69b33912515"
BOT_TOKEN = "8605281051:AAFaTjKelth9etzPjx16UiSFm19Hd2SUAl4"

# Agar assistant account ka session string hai to yaha daalo
SESSION_STRING = None

# ============================================

bot = Client(
    "music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

if SESSION_STRING:
    assistant = Client(
        "assistant",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING
    )
else:
    assistant = Client(
        "assistant",
        api_id=API_ID,
        api_hash=API_HASH
    )

call_py = PyTgCalls(assistant)

queue = {}

# ================= YT-DLP =================

ydl_opts = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
}


def get_audio_url(query):

    with YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(
            f"ytsearch:{query}",
            download=False
        )

        if "entries" in info:
            video = info["entries"][0]

            return (
                video["url"],
                video["title"]
            )

    return None, None


# ================= PLAY =================

@bot.on_message(filters.command("play") & filters.group)
async def play(_, message: Message):

    if len(message.command) < 2:
        return await message.reply_text(
            "❌ Example:\n`/play tum hi ho`"
        )

    chat_id = message.chat.id

    query = " ".join(message.command[1:])

    msg = await message.reply_text(
        "🔎 Song search ho raha hai..."
    )

    try:

        audio_url, title = get_audio_url(query)

        if not audio_url:
            return await msg.edit(
                "❌ Song nahi mila."
            )

        if chat_id not in queue:
            queue[chat_id] = []

        if await call_py.is_connected(chat_id):

            queue[chat_id].append({
                "url": audio_url,
                "title": title
            })

            await msg.edit(
                f"📝 Queue me add hua:\n🎵 {title}"
            )

        else:

            await call_py.join_group_call(
                chat_id,
                AudioPiped(audio_url)
            )

            await msg.edit(
                f"▶ Playing:\n🎵 {title}"
            )

    except Exception as e:

        await msg.edit(f"❌ Error:\n{e}")


# ================= PAUSE =================

@bot.on_message(filters.command("pause") & filters.group)
async def pause(_, message: Message):

    try:

        await call_py.pause_stream(
            message.chat.id
        )

        await message.reply_text(
            "⏸ Music paused."
        )

    except Exception as e:

        await message.reply_text(
            f"❌ {e}"
        )


# ================= RESUME =================

@bot.on_message(filters.command("resume") & filters.group)
async def resume(_, message: Message):

    try:

        await call_py.resume_stream(
            message.chat.id
        )

        await message.reply_text(
            "▶ Music resumed."
        )

    except Exception as e:

        await message.reply_text(
            f"❌ {e}"
        )


# ================= SKIP =================

@bot.on_message(filters.command("skip") & filters.group)
async def skip(_, message: Message):

    chat_id = message.chat.id

    try:

        if (
            chat_id in queue
            and len(queue[chat_id]) > 0
        ):

            next_song = queue[chat_id].pop(0)

            await call_py.change_stream(
                chat_id,
                AudioPiped(next_song["url"])
            )

            await message.reply_text(
                f"⏭ Next Song:\n🎵 {next_song['title']}"
            )

        else:

            await call_py.leave_group_call(
                chat_id
            )

            await message.reply_text(
                "📭 Queue khali hai.\nVC leave kar diya."
            )

    except Exception as e:

        await message.reply_text(
            f"❌ {e}"
        )


# ================= STOP =================

@bot.on_message(filters.command("stop") & filters.group)
async def stop(_, message: Message):

    chat_id = message.chat.id

    try:

        queue[chat_id] = []

        await call_py.leave_group_call(
            chat_id
        )

        await message.reply_text(
            "⏹ Music stopped."
        )

    except Exception as e:

        await message.reply_text(
            f"❌ {e}"
        )


# ================= STREAM END =================

@call_py.on_stream_end()
async def stream_end(_, update):

    chat_id = update.chat_id

    if (
        chat_id in queue
        and len(queue[chat_id]) > 0
    ):

        next_song = queue[chat_id].pop(0)

        await call_py.change_stream(
            chat_id,
            AudioPiped(next_song["url"])
        )

    else:

        await call_py.leave_group_call(
            chat_id
        )


# ================= START =================

async def main():

    print("================================")
    print("✅ Starting Music Bot...")
    print("================================")

    await bot.start()

    await assistant.start()

    await call_py.start()

    print("================================")
    print("✅ Music Bot Started Successfully")
    print("================================")

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())