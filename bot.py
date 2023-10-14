import json
import requests
import os
import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from pyrogram.enums import ParseMode

moderator_ids = [1902879847, 1097234204, 5543537764, 6212030865]
api_id = 13340341
api_hash = "e83570d934a86b99cc9bdd3210c1d269"
bot_token = "6628987065:AAHhoQxS1ZVX35I2dv8CwaKlv32f9DESGZw"
app = Client("botop", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
user_choices = {}

def get_github_raw_file_content_as_list(url):
    response = requests.get(url)
    response.raise_for_status()
    content_list = response.text.split("\n")
    user_list = []
    for line in content_list:
        line = line.strip() 
        if "#" in line:
            line = line.split("#")[0].strip()
        user_list.append(line)
    return user_list

def is_user_registered(user_id):
    with open("users.txt", "r") as user_file:
        user_list = user_file.read().splitlines()
    return str(user_id) in user_list

def load_user_usage():
    with open("user_usage.json", "r") as file:
        return json.load(file)

def save_user_usage(user_usage):
    with open("user_usage.json", "w") as file:
        json.dump(user_usage, file)


broadcast_text = None
broadcast_type = None

@app.on_message(filters.command('broadcast') & filters.user(moderator_ids))
async def broadcast_command(client, message: Message):
    global broadcast_text
    if len(message.command) < 2:
        await message.reply_text("**Usage: /broadcast [message]**", parse_mode=ParseMode.MARKDOWN)
        return
    broadcast_text = message.text.split(None, 1)[1]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Text", callback_data="text"), InlineKeyboardButton("Image or GIF", callback_data="media")]
    ])
    await message.reply_text("**Choose the type of broadcast:**", reply_markup=keyboard)

@app.on_callback_query(filters.user(moderator_ids) & filters.regex("^text$"))
async def broadcast_text_callback(client, callback_query: CallbackQuery):
    global broadcast_type, broadcast_text
    broadcast_type = "text"
    with open("users.txt", "r") as user_file:
        user_list = user_file.read().splitlines()
    total_users = len(user_list)
    successful_messages = 0
    for user_id in user_list:
        try:
            await client.send_message(int(user_id), broadcast_text, parse_mode=ParseMode.MARKDOWN)
            successful_messages += 1
        except Exception as e:
            pass
    await callback_query.message.reply_text(f"**Broadcasted message to {successful_messages}/{total_users} users.**", parse_mode=ParseMode.MARKDOWN)
    broadcast_text = None
    broadcast_type = None

@app.on_callback_query(filters.user(moderator_ids) & filters.regex("^media$"))
async def broadcast_media_callback(client, callback_query: CallbackQuery):
    global broadcast_type
    broadcast_type = "media"
    await callback_query.message.reply_text("**Now send the image or gif you want to broadcast.**", parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.user(moderator_ids) & (filters.photo | filters.animation))
async def broadcast_message(client, message: Message):
    global broadcast_text, broadcast_type
    if broadcast_type != "media" or broadcast_text is None:
        return
    with open("users.txt", "r") as user_file:
        user_list = user_file.read().splitlines()
    total_users = len(user_list)
    successful_messages = 0
    for user_id in user_list:
        try:
            if message.photo:
                await client.send_photo(int(user_id), photo=message.photo.file_id, caption=broadcast_text, parse_mode=ParseMode.MARKDOWN)
            elif message.animation:
                await client.send_animation(int(user_id), animation=message.animation.file_id, caption=broadcast_text, parse_mode=ParseMode.MARKDOWN)
            successful_messages += 1
        except Exception as e:
            pass
    await message.reply_text(f"**Broadcasted message to {successful_messages}/{total_users} users.**", parse_mode=ParseMode.MARKDOWN)
    broadcast_text = None
    broadcast_type = None

@app.on_message(filters.command('start'))
async def start(client, message):
    if not is_user_registered(message.from_user.id):
        with open("users.txt", "a") as user_file:
            user_file.write(str(message.from_user.id) + "\n")
    user_s = get_github_raw_file_content_as_list("https://raw.githubusercontent.com/Deathmatix/verify-logsearch/main/users.txt")
    if str(message.from_user.id) not in user_s:
        await message.reply_text("**Welcome! You are a free user. You get 2 free searches.**", parse_mode=ParseMode.MARKDOWN)
    search_button = InlineKeyboardButton("Search", callback_data="search_options")
    keyboard = InlineKeyboardMarkup([[search_button]])
    await message.reply_text("**This bot helps by searching logs database and find data you ask.**\n"
                            "**Made by - @Deathmatix \n\nTo search for something, simply click the 'Search' button below.**", reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command('search'))
async def search_command(client, message):
    search_button = InlineKeyboardButton("Search", callback_data="search_options")
    keyboard = InlineKeyboardMarkup([[search_button]])
    await message.reply_text("**To search for something, simply click the 'Search' button below.**", reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command('id'))
async def id_command(client, message):
    user_id = message.from_user.id
    await message.reply_text(f"**Your User ID:**\n`user_id`\n\n**You can click to copy and send it to @deathmatix if you want to buy a subscription.**", parse_mode=ParseMode.MARKDOWN)

@app.on_callback_query(filters.regex("search_options"))
async def search_options_callback_handler(client, query: CallbackQuery):
    await query.answer()
    options = InlineKeyboardMarkup([
        [InlineKeyboardButton("Username", callback_data="search_type_username")],
        [InlineKeyboardButton("Email", callback_data="search_type_email")],
        [InlineKeyboardButton("Last IP", callback_data="search_type_lastip")],
        [InlineKeyboardButton("Hash", callback_data="search_type_hash")],
        [InlineKeyboardButton("Name", callback_data="search_type_name")],
        [InlineKeyboardButton("Password", callback_data="search_type_password")],
    ])
    await query.message.reply_text("**Please choose one search type:**", reply_markup=options, parse_mode=ParseMode.MARKDOWN)

@app.on_callback_query(filters.regex("search_type_"))
async def search_type_callback_handler(client, query: CallbackQuery):
    await query.answer()
    search_type = query.data.replace("search_type_", "")
    user_choices[query.from_user.id] = search_type
    await query.message.reply_text(f"**Please enter the search_type you want to search for (Reply to this message).**", parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.text & filters.reply)
async def handle_search_query(client, message: Message):
    user_list = get_github_raw_file_content_as_list("https://raw.githubusercontent.com/Deathmatix/verify-logsearch/main/users.txt")
    user_usage = load_user_usage()
    user_id = str(message.from_user.id)
    
    if str(message.from_user.id) in user_list or user_usage.get(user_id, 0) < 2:
        search_term = message.text
        sanitized_search_term = re.sub(r'[\\/:*?"<>|]', '_', search_term)
        await message.reply_text("**Fetching results...**", parse_mode=ParseMode.MARKDOWN)
        headers = {
            "X-Auth-Code": "mOaOUyxvBvyHJlpRz6",
            "Content-Type": "application/json",
        }
        data = {
            "searchterm": search_term
        }
        search_option = user_choices.get(message.from_user.id)
        if search_option == "password":
            response = requests.post("https://serval-smart-troll.ngrok-free.app/search", headers=headers, json=data)
            formatted_text = json.dumps(response.json(), indent=2)
        elif search_option == "username" or search_option == "email" or search_option == "lastip" or search_option == "hash" or search_option == "name":
            snusbase_auth = 'sbl5auwa0Sm6LjSgyLLWvU3NfDyRMI'
            snusbase_api = 'https://api-experimental.snusbase.com/'

            def send_request(url, body=None):
                headers = {
                    'Auth': snusbase_auth,
                    'Content-Type': 'application/json',
                }
                method = 'POST' if body else 'GET'
                data = json.dumps(body) if body else None
                response = requests.request(method, snusbase_api + url, headers=headers, data=data)
                return response.json()

            search_type = user_choices.get(message.from_user.id, "username") 
            search_response = send_request('data/search', {
                'terms': [search_term],
                'types': [search_type],
                'wildcard': False,
            })  
            formatted_text = json.dumps(search_response, indent=2)

        caption = f"Logs by @Deathmatix - search_term.capitalize()"
        formatted_text = caption + "\n\n" + formatted_text
        result_file_name = f"{message.from_user.id}_{sanitized_search_term}.txt"
        
        with open(result_file_name, "w", encoding="utf-8") as text_file:
            text_file.write(formatted_text)
        
        if str(message.from_user.id) not in user_list:
            with open(result_file_name, "r", encoding="utf-8") as text_file:
                file_content = text_file.read()
            truncated_content = file_content[:2048]
            with open(result_file_name, "w", encoding="utf-8") as text_file:
                text_file.write(truncated_content)
        
        await message.reply_text("**Downloading/uploading file...**", parse_mode=ParseMode.MARKDOWN)
        await message.reply_document(result_file_name, caption=caption)
        os.remove(result_file_name)
        
        if str(message.from_user.id) not in user_list:
            user_usage[user_id] = user_usage.get(user_id, 0) + 1
            save_user_usage(user_usage)
            remaining_searches = 2 - user_usage[user_id]
            await message.reply_text(f"**You are a free user. You have used one of your free searches. You have {remaining_searches} searches remaining.**", parse_mode=ParseMode.MARKDOWN)
            
    else:
        await message.reply_text("**You have reached your limit. Please subscribe to continue using this bot. Contact @deathmatix to buy a subscription.**", parse_mode=ParseMode.MARKDOWN)

app.run()
