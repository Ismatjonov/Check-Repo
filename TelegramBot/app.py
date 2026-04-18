#!/usr/bin/env python3
"""
Telegram бот для скачивания видео по ссылке.
Поддерживает: YouTube, TikTok, Instagram, Twitter/X, VK, и сотни других платформ через yt-dlp.

Установка зависимостей:
    pip install python-telegram-bot yt-dlp

Запуск:
    1. Получи токен у @BotFather в Telegram
    2. Вставь токен в переменную BOT_TOKEN
    3. python video_downloader_bot.py
"""

import os
import re
import asyncio
import logging
import tempfile
import shutil
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import yt_dlp

# ── Настройки ──────────────────────────────────────────────────────────────────
BOT_TOKEN = "8729016313:AAGYuG8MqpJaZ2SAgSNdGIDbcEW7h1LLu5E"  # <-- вставь токен от @BotFather

MAX_FILE_SIZE_MB = 50          # Telegram лимит для обычных ботов (50 МБ)
DOWNLOAD_DIR = tempfile.gettempdir()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Утилиты ────────────────────────────────────────────────────────────────────

URL_REGEX = re.compile(
    r"https?://[^\s]+"
)

def extract_url(text: str) -> str | None:
    """Извлекает первую ссылку из текста."""
    match = URL_REGEX.search(text)
    return match.group(0) if match else None


def human_size(bytes_: int) -> str:
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if bytes_ < 1024:
            return f"{bytes_:.1f} {unit}"
        bytes_ /= 1024
    return f"{bytes_:.1f} ТБ"


def get_ydl_opts(output_dir: str, quality: str = "best") -> dict:
    """Формирует опции yt-dlp в зависимости от желаемого качества."""
    format_map = {
    "best":   "best[ext=mp4]/best",
    "hd":     "best[height<=1080][ext=mp4]/best[height<=1080]",
    "medium": "best[height<=720][ext=mp4]/best[height<=720]",
    "low":    "best[height<=480][ext=mp4]/best[height<=480]",
    "audio":  "bestaudio[ext=m4a]/bestaudio",
}
    return {
        "format": format_map.get(quality, format_map["best"]),
        "outtmpl": os.path.join(output_dir, "%(title).60s.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,       # только одно видео, не плейлист
        "socket_timeout": 30,
    }


async def fetch_info(url: str) -> dict:
    """Получает метаданные видео без скачивания."""
    loop = asyncio.get_event_loop()

    def _fetch():
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "noplaylist": True}) as ydl:
            return ydl.extract_info(url, download=False)

    return await loop.run_in_executor(None, _fetch)


async def download_video(url: str, output_dir: str, quality: str = "best") -> Path:
    """Скачивает видео и возвращает путь к файлу."""
    loop = asyncio.get_event_loop()
    opts = get_ydl_opts(output_dir, quality)
    result: dict = {}

    def _download():
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            result["filename"] = ydl.prepare_filename(info)
            # Если файл был замержен — расширение могло смениться на .mp4
            result["info"] = info

    await loop.run_in_executor(None, _download)

    # Ищем реально скачанный файл
    raw = Path(result["filename"])
    if raw.exists():
        return raw

    # Иногда расширение меняется после мержа
    for ext in ("mp4", "mkv", "webm", "m4a", "mp3"):
        candidate = raw.with_suffix(f".{ext}")
        if candidate.exists():
            return candidate

    # Последний резерв — берём самый свежий файл в папке
    files = sorted(Path(output_dir).iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    if files:
        return files[0]

    raise FileNotFoundError("Не удалось найти скачанный файл.")


# ── Хендлеры ───────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "👋 *Привет! Я бот для скачивания видео.*\n\n"
        "Просто отправь мне ссылку на видео — и я его скачаю.\n\n"
        "🌐 *Поддерживаемые платформы:*\n"
        "YouTube · TikTok · Instagram · Twitter/X · VK · Twitch · "
        "Dailymotion · Reddit · Vimeo · и ещё 1000+ сайтов\n\n"
        "📎 *Команды:*\n"
        "/start — это сообщение\n"
        "/help — помощь\n\n"
        "⚠️ Лимит файла: 50 МБ (ограничение Telegram)."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📖 *Как пользоваться:*\n\n"
        "1. Скопируй ссылку на видео\n"
        "2. Отправь её мне в чат\n"
        "3. Выбери качество\n"
        "4. Подожди — пришлю файл!\n\n"
        "❓ *Почему бот не скачивает?*\n"
        "• Видео может быть приватным\n"
        "• Сайт может блокировать скачивание\n"
        "• Файл больше 50 МБ\n\n"
        "💡 Для больших файлов выбери *Низкое качество* или *Только аудио*."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Получает ссылку, запрашивает качество через inline-кнопки."""
    url = extract_url(update.message.text or "")
    if not url:
        await update.message.reply_text("❌ Не нашёл ссылку в сообщении. Отправь URL видео.")
        return

    # Сохраняем URL в user_data для дальнейшего использования
    context.user_data["pending_url"] = url

    status_msg = await update.message.reply_text("🔍 Проверяю ссылку…")

    try:
        info = await fetch_info(url)
        title = info.get("title", "Без названия")[:80]
        duration = info.get("duration")
        uploader = info.get("uploader") or info.get("channel") or "—"
        dur_str = f"{duration // 60}:{duration % 60:02d}" if duration else "неизвестно"

        caption = (
            f"🎬 *{title}*\n"
            f"👤 {uploader}\n"
            f"⏱ {dur_str}\n\n"
            "Выбери качество:"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔥 Лучшее",  callback_data="q:best"),
                InlineKeyboardButton("🖥 1080p",    callback_data="q:hd"),
            ],
            [
                InlineKeyboardButton("📺 720p",     callback_data="q:medium"),
                InlineKeyboardButton("📱 480p",     callback_data="q:low"),
            ],
            [
                InlineKeyboardButton("🎵 Аудио",   callback_data="q:audio"),
                InlineKeyboardButton("❌ Отмена",  callback_data="q:cancel"),
            ],
        ])

        await status_msg.edit_text(caption, parse_mode="Markdown", reply_markup=keyboard)

    except yt_dlp.utils.DownloadError as e:
        logger.warning("fetch_info error: %s", e)
        await status_msg.edit_text(
            "❌ Не удалось получить информацию о видео.\n"
            "Проверь ссылку или попробуй другой сайт."
        )
    except Exception as e:
        logger.exception("Unexpected error in handle_url")
        await status_msg.edit_text(f"❌ Ошибка: {e}")


async def handle_quality_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор качества и скачивает видео."""
    query = update.callback_query
    await query.answer()

    choice = query.data.split(":", 1)[1]

    if choice == "cancel":
        await query.edit_message_text("❌ Отменено.")
        context.user_data.pop("pending_url", None)
        return

    url = context.user_data.get("pending_url")
    if not url:
        await query.edit_message_text("❌ URL не найден. Отправь ссылку заново.")
        return

    quality_labels = {
        "best":   "лучшее",
        "medium": "720p",
        "low":    "480p",
        "audio":  "только аудио",
    }
    await query.edit_message_text(
        f"⬇️ Скачиваю ({quality_labels.get(choice, choice)})…\n"
        "Это может занять некоторое время."
    )

    tmp_dir = tempfile.mkdtemp(prefix="tgvid_")
    try:
        file_path = await download_video(url, tmp_dir, quality=choice)
        file_size = file_path.stat().st_size

        if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            await query.edit_message_text(
                f"❌ Файл слишком большой: {human_size(file_size)}.\n"
                f"Telegram позволяет отправлять не более {MAX_FILE_SIZE_MB} МБ.\n"
                "Попробуй выбрать более низкое качество."
            )
            return

        await query.edit_message_text("📤 Загружаю в Telegram…")

        if choice == "audio":
            await query.message.reply_audio(
                audio=open(file_path, "rb"),
                title=file_path.stem,
                caption=f"🎵 {file_path.stem}",
            )
        else:
            await query.message.reply_video(
                video=open(file_path, "rb"),
                caption=f"🎬 {file_path.stem}\n\n📎 {human_size(file_size)}",
                supports_streaming=True,
            )

        await query.edit_message_text("✅ Готово!")

    except yt_dlp.utils.DownloadError as e:
        logger.warning("download error: %s", e)
        await query.edit_message_text(
            "❌ Ошибка при скачивании.\n\n"
            f"Детали: `{str(e)[:300]}`",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.exception("Unexpected error in handle_quality_callback")
        await query.edit_message_text(f"❌ Непредвиденная ошибка:\n`{e}`", parse_mode="Markdown")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        context.user_data.pop("pending_url", None)


# ── Запуск ─────────────────────────────────────────────────────────────────────

def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(handle_quality_callback, pattern=r"^q:"))

    logger.info("Бот запущен. Нажми Ctrl+C для остановки.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
