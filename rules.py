import logging
from aiogram import types
from aiogram.types import ParseMode

logging.basicConfig(level=logging.INFO)

# Dictionary to store chat rules. The chat ID will be the key.
chat_rules = {}

async def is_admin(message: types.Message, bot) -> bool:
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    return member.status == "administrator" or member.status == "creator"

# Using dp from the main bot file
def setup(dp):
    @dp.message_handler(commands=['rules'])
    async def send_rules(message: types.Message):
        rules = chat_rules.get(message.chat.id)
        if not rules:
            await message.reply(f"No rules have been set for `{message.chat.title}` ", parse_mode=ParseMode.MARKDOWN)
        else:
            await message.reply(f"The rules for `{message.chat.title}` are:\n\n{rules}", parse_mode=ParseMode.MARKDOWN)

    @dp.message_handler(commands=['setrules'])
    async def set_chat_rules(message: types.Message):
        bot = message.bot
        if not await is_admin(message, bot):
            return
        
        try:
            rules_text = message.text.split(' ', 1)[1]
            chat_rules[message.chat.id] = rules_text
            await message.reply(f"New rules for `{message.chat.title}` set successfully!", parse_mode=ParseMode.MARKDOWN)
        except IndexError:
            await message.reply("Please provide the rules. Format: `/setrules <rules>`", parse_mode=ParseMode.MARKDOWN)

    @dp.message_handler(commands=['resetrules'])
    async def reset_chat_rules(message: types.Message):
        bot = message.bot
        if not await is_admin(message, bot):
            return

        if message.chat.id in chat_rules:
            del chat_rules[message.chat.id]
        await message.reply(f"Rules for **{message.chat.title}** were successfully cleared!", parse_mode=ParseMode.MARKDOWN)
