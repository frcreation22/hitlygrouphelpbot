import os
import rules
import report
import logging
import re
import asyncio  
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from pyrogram import Client
from aiogram.types import ParseMode
from aiogram.dispatcher.filters import BoundFilter
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


api_id = '18647671'
api_hash = "be6fb9e02ac9b9d898f944d9351f95e2"
pyro_client = Client("main", api_id=api_id, api_hash=api_hash)

aiogram_bot_token = '6534767620:AAFdbxpfAb4aNW2eP-ACVYo0clyTLKZq6bw'
bot = Bot(token=aiogram_bot_token)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())
logging.basicConfig(level=logging.INFO)


link_counts = {}  # Format: {chat_id: {user_id: count}}
LINK_BAN_COUNT = 4 
filters_db = {}
reporting_status = {}
chat_rules = {}
BAD_WORDS = {}  # Format: {chat_id: set_of_bad_words}
BAN_COUNT = 4  # Default value
USER_COUNTS = {}  # Format: {chat_id: {user_id: count}}


##Logistic for URLs
def load_urls():
    if not os.path.exists('urls.txt'):
        with open('urls.txt', 'w') as f:
            pass  # Creates an empty file
    with open('urls.txt', 'r') as f:
        return f.read().splitlines()

whitelisted_urls = load_urls()
chat_url_detection = {}

def contains_url(text):
    pattern = r'(?:http(s)?://)?([\w\-]+\.)+[\w\-]+(/[\w\-./?%&=]*)?'
    return bool(re.search(pattern, text))


##logic function for Filter
class TriggerFilter(BoundFilter):
    key = 'has_trigger'

    def __init__(self, has_trigger: bool):
        self.has_trigger = has_trigger

    async def check(self, message: types.Message):
        return message.chat.id in filters_db and message.text.lower() in filters_db[message.chat.id]

dp.filters_factory.bind(TriggerFilter)


###>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def is_admin(chat_id, user_id):
    chat_admins = await bot.get_chat_administrators(chat_id)
    return any(admin.user.id == user_id for admin in chat_admins)
    

	
##Rules
rules.setup(dp)
##Reporte
report.setup(dp)

# Create the inline keyboard
inline_kb = InlineKeyboardMarkup(row_width=2)
buttons = [
    InlineKeyboardButton("Telegram Channel", url="https://t.me/hitlyofficial"),
    InlineKeyboardButton("Telegram Group", url="https://t.me/hitly_official"),
    InlineKeyboardButton("Twitter", url="https://twitter.com/Hitlyofficial"),
    InlineKeyboardButton("Website", url="https://hitly.live/"),
]
inline_kb.add(*buttons)

# Welcome message with the inline keyboard attached
welcome_message = (
    "🎉 <b>ᗯEᒪᑕOᗰE, {mention}! ᗯEᒪᑕOᗰE TO Oᑌᖇ GᖇOᑌᑭ </b>\n\n"
    "🌐 𝐂𝐡𝐞𝐜𝐤 𝐨𝐮𝐭 𝐨𝐮𝐫 𝐬𝐨𝐜𝐢𝐚𝐥 𝐦𝐞𝐝𝐢𝐚 𝐩𝐫𝐞𝐬𝐞𝐧𝐜𝐞⟿\n\n"
)

@dp.message_handler(content_types=['new_chat_members'])
async def on_user_joined(message: types.Message):
    user_mention = f"@{message.new_chat_members[0].username}" if message.new_chat_members[0].username else message.new_chat_members[0].first_name
    await bot.send_message(message.chat.id, welcome_message.format(mention=user_mention), reply_markup=inline_kb, parse_mode='HTML')


#Ban************************************************************
@dp.message_handler(commands=['ban'])
async def ban_user(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        await message.reply("𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐬𝐞𝐝!")
        return

    args = message.get_args().split()
    target_user = None

    # Handling command with username (with or without '@')
    if args and (args[0].startswith("@") or not args[0].isdigit()):
        username = args[0].lstrip("@")
        user = await pyro_client.get_users(username)
        if user:
            target_user = await bot.get_chat_member(message.chat.id, user.id)
            if target_user:
                target_user = target_user.user  # Access the user object here

    # Handling command with user ID
    elif args and args[0].isdigit():
        user_id = int(args[0])
        target_user = await bot.get_chat_member(message.chat.id, user_id)
        if target_user:
            target_user = target_user.user  # Access the user object here

    # Handling reply to a user's message
    elif message.reply_to_message:
        target_user = message.reply_to_message.from_user

    if target_user and await is_admin(message.chat.id, target_user.id):
        await message.reply("Why would I ban an admin?")
        return

    if target_user:
        await bot.kick_chat_member(message.chat.id, target_user.id)
        await message.reply(f"Banned user {target_user.username or target_user.id}")
    else:
        await message.reply("User not found!")

@dp.message_handler(commands=['addbw'])
async def add_bad_words(message: types.Message):
    chat_id = message.chat.id

    if not await is_admin(chat_id, message.from_user.id):
        await message.reply("𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐬𝐞𝐝!")
        return

    # Initialize group data if not present
    if chat_id not in BAD_WORDS:
        BAD_WORDS[chat_id] = set()

    words = message.get_args().split(',')
    for word in words:
        BAD_WORDS[chat_id].add(word.strip().lower())

    await message.reply(f"Added {len(words)} bad word(s) to the list.")

@dp.message_handler(commands=['delbw'])
async def delete_bad_words(message: types.Message):
    chat_id = message.chat.id

    if not await is_admin(chat_id, message.from_user.id):
        await message.reply("𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐬𝐞𝐝!")
        return

    if chat_id not in BAD_WORDS:
        await message.reply("No words to remove!")
        return

    words = message.get_args().split(',')
    removed_count = 0
    for word in words:
        word = word.strip().lower()
        if word in BAD_WORDS[chat_id]:
            BAD_WORDS[chat_id].remove(word)
            removed_count += 1

    await message.reply(f"Removed {removed_count} bad word(s) from the list.")

@dp.message_handler(commands=['bwords'])
async def list_bad_words(message: types.Message):
    chat_id = message.chat.id

    if BAD_WORDS.get(chat_id):
        await message.reply(", ".join(BAD_WORDS[chat_id]))
    else:
        await message.reply("No bad words in the list.")

@dp.message_handler(commands=['bcount'])
async def set_ban_count(message: types.Message):
    chat_id = message.chat.id

    if not await is_admin(chat_id, message.from_user.id):
        await message.reply("𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐬𝐞𝐝!")
        return

    count = message.get_args().split()
    if count and count[0].isdigit():
        global BAN_COUNT
        BAN_COUNT = int(count[0])
        await message.reply(f"Ban count set to {BAN_COUNT}.")
    else:
        await message.reply("Invalid count provided.")

@dp.message_handler(lambda message: any(word.lower() in message.text.lower().split() for word in BAD_WORDS.get(message.chat.id, {})))
async def check_bad_words(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Exclude admins from being checked
    if await is_admin(chat_id, user_id):
        return

    # Initialize group data if not present
    if chat_id not in USER_COUNTS:
        USER_COUNTS[chat_id] = {}

    user_count = USER_COUNTS[chat_id].get(user_id, 0) + 1
    USER_COUNTS[chat_id][user_id] = user_count

    await bot.delete_message(chat_id, message.message_id)
    
    # Send and then delete after 5 seconds
    msg = await bot.send_message(chat_id, f"@{message.from_user.username} used bad words\nCount: {user_count}/4 ")
    await asyncio.sleep(5)
    await bot.delete_message(chat_id, msg.message_id)

    if user_count >= BAN_COUNT:
        await bot.kick_chat_member(chat_id, user_id)
        
        # Send and then delete after 5 seconds
        msg = await message.reply(f"Banned @{message.from_user.username} for using bad words too many times.")
        await asyncio.sleep(5)
        await bot.delete_message(chat_id, msg.message_id)

        del USER_COUNTS[chat_id][user_id]  # Reset the count for the banned user


###Unban
@dp.message_handler(commands=['unban'])
async def unban_user(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        await message.reply("𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐬𝐞𝐝!")
        return

    args = message.get_args().split()
    target_user = None

    # Handling command with username (with or without '@')
    if args and (args[0].startswith("@") or not args[0].isdigit()):
        username = args[0].lstrip("@")
        user = await pyro_client.get_users(username)
        if user:
            target_user = user.id

    # Handling command with user ID
    elif args and args[0].isdigit():
        target_user = int(args[0])

    # Handling reply to a user's message
    elif message.reply_to_message:
        target_user = message.reply_to_message.from_user.id

    if target_user:
        await bot.unban_chat_member(message.chat.id, target_user)
        await message.reply(f"Unbanned user {target_user}")
    else:
        await message.reply("User not found!")

###Pin
@dp.message_handler(commands=['pin'])
async def pin_message(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        await message.reply("𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐬𝐞𝐝!")
        return

    # Pinning a message by replying to it
    if message.reply_to_message:
        await bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id)
        await message.reply("Pinned the message!")

###Unpin 
@dp.message_handler(commands=['unpin'])
async def unpin_message(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        await message.reply("𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐬𝐞𝐝!")
        return

    # Unpinning a message by replying to it
    if message.reply_to_message:
        await bot.unpin_chat_message(message.chat.id, message.reply_to_message.message_id)
        await message.reply("Unpinned the message!")
    else:
        await message.reply("Please reply to a message to unpin it!")

###Filter
@dp.message_handler(commands=['filter'])
async def add_filter(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not await is_admin(chat_id, user_id):
        await message.reply("𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐬𝐞𝐝!")
        return

    cmd, rest = message.text.split(None, 1)
    args = rest.split(',', 1)
    if len(args) < 2:
        await message.reply("You need to specify a trigger and a reply!")
        return

    trigger, reply = args[0].strip(), args[1].strip()
    if chat_id not in filters_db:
        filters_db[chat_id] = {}

    filters_db[chat_id][trigger.lower()] = reply
    await message.reply(f"Added filter for '{trigger}' in '{message.chat.title}'!")

@dp.message_handler(commands=['filters'])
async def list_filters(message: types.Message):
    chat_id = message.chat.id
    if chat_id not in filters_db or not filters_db[chat_id]:
        await message.reply(f"No filters in '{message.chat.title}'!")
        return

    msg = f"Filters in this '{message.chat.title}':\n"
    for trigger, reply in filters_db[chat_id].items():
        msg += f"- {trigger}: {reply}\n"
    
    await message.reply(msg, parse_mode=ParseMode.MARKDOWN)

@dp.message_handler(commands=['stop'])
async def remove_filter(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not await is_admin(chat_id, user_id):
        await message.reply("𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐬𝐞𝐝!")
        return

    args = message.text.split(None, 1)
    if len(args) < 2:
        await message.reply("You need to specify a trigger!")
        return

    trigger = args[1].lower()

    if chat_id in filters_db and trigger in filters_db[chat_id]:
        del filters_db[chat_id][trigger]
        await message.reply(f"Stopped replying to '{trigger}' in '{message.chat.title}'!")
    else:
        await message.reply(f"No filter for '{trigger}' in '{message.chat.title}'!")

@dp.message_handler(commands=['stopall'])
async def remove_all_filters(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not await is_admin(chat_id, user_id):
        await message.reply("𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐬𝐞𝐝!")
        return

    if chat_id in filters_db:
        del filters_db[chat_id]
        await message.reply(f"All filters have been removed in '{message.chat.title}'!")
    else:
        await message.reply(f"No filters in '{message.chat.title}' to remove!")

@dp.message_handler(has_trigger=True)
async def reply_filter(message: types.Message):
    await message.reply(filters_db[message.chat.id][message.text.lower()])

##Kick
@dp.message_handler(commands=['kick'])
async def kick_user(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        await message.reply("𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐬𝐞𝐝!")
        return

    args = message.get_args().split()
    target_user = None

    # Handling command with username (with or without '@')
    if args and (args[0].startswith("@") or not args[0].isdigit()):
        username = args[0].lstrip("@")
        user = await pyro_client.get_users(username)
        if user:
            target_user = user.id

    # Handling command with user ID
    elif args and args[0].isdigit():
        target_user = int(args[0])

    # Handling reply to a user's message
    elif message.reply_to_message:
        target_user = message.reply_to_message.from_user.id

    if target_user:
        # Ban the user
        await bot.kick_chat_member(message.chat.id, target_user)
        
        # Immediately unban the user, effectively "kicking" them
        await bot.unban_chat_member(message.chat.id, target_user)
        
        await message.reply(f"Kicked user {target_user}")
    else:
        await message.reply("User not found!")
		
####URLs
async def is_admin(chat_id, user_id):
    chat_member = await bot.get_chat_member(chat_id, user_id)
    return chat_member.status in ['administrator', 'creator']

@dp.message_handler(commands=['rmurl'])
async def rmurl_command(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        await message.reply("You are not authorized to use this command.")
        return

    args = message.text.split()
    if len(args) != 2 or args[1] not in ['on', 'off']:
        await message.reply("Usage: /rmurl <on/off>")
        return

    command = args[1]
    chat_url_detection[message.chat.id] = (command == 'on')
    await message.reply(f"URL detection turned {command}.")

@dp.message_handler(commands=['addurl'])
async def addurl_command(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        await message.reply("You are not authorized to use this command.")
        return
    
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: /addurl <url>")
        return
    
    url = args[1]
    with open('urls.txt', 'a') as f:
        f.write(f'\n{url}')
    whitelisted_urls.append(url)
    await message.reply(f"URL {url} added to the whitelist.")

@dp.message_handler(commands=['furls'])
async def furls_command(message: types.Message):
    urls = load_urls()
    formatted_urls = "\n".join([f"• <b>{url}</b>" for url in urls])
    await message.reply(f"Filtered URLs:\n{formatted_urls}", parse_mode='HTML')

@dp.message_handler(commands=['delurl'])
async def delurl_command(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        await message.reply("You are not authorized to use this command.")
        return

    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: /delurl <url>")
        return
    
    url = args[1]
    if url in whitelisted_urls:
        whitelisted_urls.remove(url)
        with open('urls.txt', 'w') as f:
            f.write('\n'.join(whitelisted_urls))
        await message.reply(f"URL {url} removed from the whitelist.")
    else:
        await message.reply(f"URL {url} not found in the whitelist.")

@dp.message_handler(content_types=['text'])
async def handle_text(message: types.Message):
    if not chat_url_detection.get(message.chat.id, True):
        return

    if await is_admin(message.chat.id, message.from_user.id):
        return

    if any(url in message.text for url in whitelisted_urls):
        return

    if contains_url(message.text):
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Increment the count for the user in the specified chat
        link_counts.setdefault(chat_id, {}).setdefault(user_id, 0)
        link_counts[chat_id][user_id] += 1

        await bot.delete_message(chat_id, message.message_id)
        
        # Send and then delete after 5 seconds
        msg = await bot.send_message(chat_id, f"Sending link is prohibited in this chat.\n@{message.from_user.username} sent link {link_counts[chat_id][user_id]}/4 times")
        await asyncio.sleep(5)
        await bot.delete_message(chat_id, msg.message_id)

        if link_counts[chat_id][user_id] >= LINK_BAN_COUNT:
            await bot.kick_chat_member(chat_id, user_id)
            await bot.send_message(chat_id, f"@{message.from_user.username} was banned for sending links too many times.")
            del link_counts[chat_id][user_id]  
        
if __name__ == '__main__':
    pyro_client.start()  # Start the Pyrogram client here
    executor.start_polling(dp, skip_updates=True)
