import json
import requests
import os
import re
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from pyrogram.enums import ParseMode

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

moderator_ids = [1902879847, 1097234204, 5543537764]
api_id = 29248158
api_hash = "75bb1a0bbeb8435a7904321df8782c8b"
bot_token = "6582993584:AAEwCvVXuDTAwcx7n8bjBdHxgiVwbX0wmvo"
app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
user_choices = {}

def get_github_raw_file_content_as_list(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return [line.split("#")[0].strip() for line in response.text.split("\n") if line.strip()]
    except Exception as e:
        logger.error(f"Error fetching file content from GitHub: {e}")
        return []

def is_user_registered(user_id):
    try:
        with open("users.txt", "r") as user_file:
            return str(user_id) in user_file.read().splitlines()
    except Exception as e:
        logger.error(f"Error checking user registration: {e}")
        return False

def load_user_usage():
    try:
        if os.path.exists("user_usage.json"):
            with open("user_usage.json", "r") as file:
                return json.load(file)
        else:
            return {}
    except Exception as e:
        logger.error(f"Error loading user usage: {e}")
        return {}

def save_user_usage(user_usage):
    try:
        with open("user_usage.json", "w") as file:
            json.dump(user_usage, file)
    except Exception as e:
        logger.error(f"Error saving user usage: {e}")

@app.on_message(filters.command('start'))
async def start(client, message):
    if not is_user_registered(message.from_user.id):
        try:
            with open("users.txt", "a") as user_file:
                user_file.write(str(message.from_user.id) + "\n")
            await message.reply_text("**Welcome! You are a free user. You get 2 free searches.**", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Error registering user: {e}")
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
    await message.reply_text(f"**Your User ID:**\n`{user_id}`\n\n**You can click to copy and send it to @deathmatix if you want to buy a subscription.**", parse_mode=ParseMode.MARKDOWN)

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
    await query.message.reply_text(f"**Please enter the {search_type} you want to search for (Reply to this message).**", parse_mode=ParseMode.MARKDOWN)

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

        caption = f"Logs by @Deathmatix - {search_term.capitalize()}"
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
        await message.reply_text("**You have reached your limit. Please subscribe to continue using the bot. Contact @deathmatix to get the subscription.**", parse_mode=ParseMode.MARKDOWN)

app.run()
