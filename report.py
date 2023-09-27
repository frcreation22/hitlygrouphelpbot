from aiogram import types
from aiogram.dispatcher.filters import Command
from aiogram.types import ParseMode

reporting_status = {}  # {chat_id: status}

async def report_message(message: types.Message):
    if message.reply_to_message:
        chat_id = message.chat.id
        admins = await message.bot.get_chat_administrators(chat_id)
        admin_ids = [admin.user.id for admin in admins]
        
        if message.from_user.id in admin_ids:
            await message.reply("Admins can't report!")
            return

        notified = False
        for admin in admins:
            if admin.user.is_bot:
                continue
            await message.bot.send_message(admin.user.id, 
                                   f"Reported message in chat {chat_id}: [{message.reply_to_message.text}]",
                                   parse_mode=ParseMode.MARKDOWN)
            notified = True
        
        if notified:
            await message.reply("Admins have been notified!")
    else:
        await message.reply("Reply to a message to report it.")

async def toggle_reports(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /reports <on/off>")
        return

    chat_id = message.chat.id
    status = args[1].lower()

    if status == 'on':
        reporting_status[chat_id] = True
        await message.reply("Reports have been enabled!")
    elif status == 'off':
        reporting_status[chat_id] = False
        await message.reply("Reports have been disabled!")
    else:
        await message.reply("Usage: /reports <on/off>")

def setup(dp):
    # Here we're setting up message handlers for the report module
    dp.message_handler(lambda message: message.text.startswith("@admin") or 
                       (message.is_command() and message.text.split()[0][1:] == "report"))(report_message)
    
    dp.message_handler(Command('reports'), is_chat_admin=True)(toggle_reports)
