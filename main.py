import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# .env ഫയലിൽ നിന്ന് വേരിയബിളുകൾ ലോഡ് ചെയ്യുന്നു (ലോക്കൽ ടെസ്റ്റിങ്ങിന്)
load_dotenv()

# --- Config Variables ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PRIVATE_FILE_STORE = int(os.environ.get("PRIVATE_FILE_STORE"))
ADMINS = [int(admin.strip()) for admin in os.environ.get("ADMINS").split(',')]
DATABASE_URL = os.environ.get("DATABASE_URL")
FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL") # @Mala_Tv യിൽ നിന്ന് Mala_Tv മാത്രം മതി
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL"))

# --- MongoDB Setup ---
DB_CLIENT = AsyncIOMotorClient(DATABASE_URL)
DB = DB_CLIENT["AutoFilterBot"]
FILES_COLLECTION = DB["files"]

# --- Pyrogram Client ---
class AutoFilterBot(Client):
    def __init__(self):
        super().__init__(
            "AutoFilterBot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="plugins"),
            sleep=1,
        )

# --- Bot Instance ---
app = AutoFilterBot()

# --- Helpers ---

async def is_subscribed(client, user_id):
    """ഫോഴ്സ് സബ്സ്ക്രൈബ് ചാനലിൽ യൂസർ അംഗമാണോ എന്ന് പരിശോധിക്കുന്നു."""
    if not FORCE_SUB_CHANNEL:
        return True
    try:
        # get_chat_member ഉപയോഗിച്ച് യൂസർ സ്റ്റാറ്റസ് പരിശോധിക്കുന്നു
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except UserNotParticipant:
        return False
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return True # എറർ വന്നാൽ സബ്സ്ക്രൈബ്ഡ് ആയി കണക്കാക്കുന്നു

async def get_file_details(query):
    """ഡാറ്റാബേസിൽ നിന്ന് ഫയൽ വിവരങ്ങൾ തിരയുന്നു."""
    # കേസ് ഇൻസെൻസിറ്റീവ് ആയി തിരയാൻ $regex ഉപയോഗിക്കുന്നു
    # ടൈറ്റിലിലോ കാപ്ഷനിലോ കീവേഡ് ഉണ്ടോ എന്ന് നോക്കുന്നു
    cursor = FILES_COLLECTION.find({
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"caption": {"$regex": query, "$options": "i"}}
        ]
    }).limit(10) # ആദ്യത്തെ 10 ഫലങ്ങൾ മാത്രം
    
    files = await cursor.to_list(length=10)
    return files

# --- Handlers ---

@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    await message.reply_text(
        "👋 ഹായ്! ഞാൻ ഒരു ഓട്ടോ-ഫിൽട്ടർ ബോട്ടാണ്. എന്നെ നിങ്ങളുടെ ഗ്രൂപ്പിൽ ചേർത്ത് പ്രവർത്തിപ്പിക്കാം."
    )

@app.on_message(filters.command("index") & filters.user(ADMINS))
async def index_command(client, message: Message):
    """അഡ്മിൻമാർക്ക് ഫയൽ സ്റ്റോർ ചാനലിലെ ഫയലുകൾ ഇൻഡക്സ് ചെയ്യാനുള്ള കമാൻഡ്."""
    msg = await message.reply_text("ഫയലുകൾ ഇൻഡക്സ് ചെയ്യാൻ തുടങ്ങുന്നു...")
    
    # നിങ്ങൾ നൽകിയ ചാനലിന്റെ ID യിൽ നിന്ന് മെസ്സേജുകൾ എടുക്കുന്നു
    total_files = 0
    async for msg in client.search_messages(chat_id=PRIVATE_FILE_STORE, filter="document"):
        if msg.document:
            file_id = msg.document.file_id
            file_ref = msg.document.file_ref
            file_name = msg.document.file_name
            caption = msg.caption.html if msg.caption else None
            
            # ഡാറ്റാബേസിൽ ഫയൽ വിവരങ്ങൾ ചേർക്കുന്നു
            await FILES_COLLECTION.update_one(
                {"file_id": file_id},
                {
                    "$set": {
                        "title": file_name,
                        "caption": caption,
                        "file_id": file_id,
                        "file_ref": file_ref,
                        "chat_id": PRIVATE_FILE_STORE,
                        "message_id": msg.id,
                    }
                },
                upsert=True
            )
            total_files += 1
            
            # 100 ഫയലുകൾക്ക് ശേഷം അപ്ഡേറ്റ് മെസ്സേജ് അയക്കുന്നു
            if total_files % 100 == 0:
                 await msg.edit_text(f"✅ ഇൻഡക്സ് ചെയ്ത ഫയലുകൾ: {total_files}")
                 
    await msg.edit_text(f"🎉 ഇൻഡക്സിംഗ് പൂർത്തിയായി! ആകെ {total_files} ഫയലുകൾ ചേർത്തു.")


@app.on_message(filters.text & filters.private | filters.group & filters.text & filters.incoming & ~filters.command)
async def auto_filter_handler(client, message: Message):
    """ടെക്സ്റ്റ് മെസ്സേജുകൾ വരുമ്പോൾ ഫിൽട്ടർ ഫയലുകൾ തിരയുന്നു."""
    query = message.text.strip()
    
    # 1. ഫോഴ്സ് സബ്സ്ക്രൈബ് ചെക്ക്
    if message.chat.type != "private" or await is_subscribed(client, message.from_user.id):
        
        # 2. കോപ്പിറൈറ്റ് മെസ്സേജ് ഡിലീറ്റ് ലോജിക് (അഡ്മിൻമാർക്ക് മാത്രം)
        COPYRIGHT_KEYWORDS = ["copyright", "unauthorized", "DMCA", "piracy", "പകർപ്പവകാശം", "അനുമതിയില്ലാതെ"] 
        if any(keyword.lower() in query.lower() for keyword in COPYRIGHT_KEYWORDS):
             try:
                 # മെസ്സേജ് ഡിലീറ്റ് ചെയ്യാൻ Bot-ന് delete_messages പെർമിഷൻ വേണം.
                 await message.delete()
                 # ലോഗ് ചാനലിൽ ഒരു നോട്ടിഫിക്കേഷൻ അയക്കുന്നു
                 await client.send_message(LOG_CHANNEL, f"🚫 **കോപ്പിറൈറ്റ് സന്ദേശം നീക്കം ചെയ്തു!**\n\n**ചാറ്റ് ID:** `{message.chat.id}`\n**യൂസർ:** {message.from_user.mention}\n**സന്ദേശം:** `{query}`")
                 return # ഡിലീറ്റ് ചെയ്താൽ ഫിൽട്ടർ കണ്ടിന്യൂ ചെയ്യേണ്ട
             except Exception as e:
                 print(f"Error deleting message: {e}")
        
        # 3. ഓട്ടോ-ഫിൽട്ടർ തിരയൽ
        files = await get_file_details(query)
        
        if files:
            text = f"ഇതാ നിങ്ങൾ തിരഞ്ഞ **{query}**-യുമായി ബന്ധപ്പെട്ട ഫയലുകൾ:\n\n"
            buttons = []
            for file in files:
                # ഫയൽ ടൈറ്റിലിൽ നിന്ന് ഫയലിന്റെ പേര് മാത്രം എടുക്കുന്നു
                file_name = file.get("title", "File").split('.')[-2].strip() 
                
                # ഫയലിന്റെ പേരിലുള്ള ബട്ടൺ
                buttons.append([
                    InlineKeyboardButton(
                        text=file_name,
                        # ഫയൽ ഷെയർ ചെയ്യാൻ ഒരു കമാൻഡ് കോൾ ചെയ്യുന്നു
                        callback_data=f"getfile_{file.get('file_id')}" 
                    )
                ])
            
            await message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True
            )
        # else:
            # ഫലം ഇല്ലെങ്കിൽ മറുപടി നൽകേണ്ട കാര്യമില്ല (ഗ്രൂപ്പിൽ ആകുമ്പോൾ)
            # if message.chat.type == "private":
            #     await message.reply_text("സോറി, നിങ്ങൾ തിരഞ്ഞ ഫയൽ ലഭ്യമല്ല.")

    else:
        # ഫോഴ്സ് സബ്സ്ക്രൈബ് ചെയ്തിട്ടില്ലെങ്കിൽ
        join_button = [
            [InlineKeyboardButton("ചാനലിൽ ചേരുക", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]
        ]
        await message.reply_text(
            f"നിങ്ങൾക്ക് ഫയലുകൾ ലഭിക്കണമെങ്കിൽ ആദ്യം ഞങ്ങളുടെ ചാനലിൽ (@{FORCE_SUB_CHANNEL}) ചേരുക.",
            reply_markup=InlineKeyboardMarkup(join_button)
        )

# --- Callback Query Handler (Inline Button Click) ---

@app.on_callback_query(filters.regex("^getfile_"))
async def send_file_handler(client, callback):
    """ബട്ടണിൽ ക്ലിക്കുമ്പോൾ ഫയൽ അയക്കുന്നു."""
    
    # 1. ഫോഴ്സ് സബ്സ്ക്രൈബ് ചെക്ക്
    if not await is_subscribed(client, callback.from_user.id):
        # നേരത്തെ കണ്ട അതേ മറുപടി അയക്കുന്നു
        join_button = [
            [InlineKeyboardButton("ചാനലിൽ ചേരുക", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]
        ]
        await callback.answer("ഫയൽ ലഭിക്കാൻ ചാനലിൽ ചേരുക.", show_alert=True)
        await callback.message.reply_text(
            f"ഫയൽ ലഭിക്കണമെങ്കിൽ ആദ്യം ഞങ്ങളുടെ ചാനലിൽ (@{FORCE_SUB_CHANNEL}) ചേരുക.",
            reply_markup=InlineKeyboardMarkup(join_button)
        )
        return

    # 2. ഫയൽ അയക്കുന്നു
    file_id = callback.data.split("_")[1]
    file = await FILES_COLLECTION.find_one({"file_id": file_id})
    
    if file:
        try:
            # ഫയൽ ഫോർവേഡ് ചെയ്യുന്നു
            await client.forward_messages(
                chat_id=callback.message.chat.id,
                from_chat_id=file['chat_id'],
                message_ids=file['message_id']
            )
            await callback.answer("ഫയൽ അയച്ചിരിക്കുന്നു.", show_alert=False)
        except Exception as e:
            await callback.answer("ഫയൽ അയക്കുന്നതിൽ ഒരു പിഴവ് സംഭവിച്ചു.", show_alert=True)
            print(f"File forward error: {e}")
    else:
        await callback.answer("ഫയൽ ഡാറ്റാബേസിൽ നിന്ന് നീക്കം ചെയ്യപ്പെട്ടു.", show_alert=True)
    
    await callback.message.delete() # മെസ്സേജ് ഡിലീറ്റ് ചെയ്യുന്നു

# --- Render Webhook Setup (FastAPI for a scalable deployment) ---
# Pyrogram-നെ Webhook മോഡിൽ പ്രവർത്തിപ്പിക്കാൻ ഈ ഭാഗം ആവശ്യമാണ്

from fastapi import FastAPI, Request, Response
import uvicorn
from http import HTTPStatus
from contextlib import asynccontextmanager

WEBHOOK_PATH = f"/{BOT_TOKEN}"
WEBHOOK_URL_BASE = os.environ.get("WEBHOOK_URL_BASE")
PORT = int(os.environ.get("PORT", 8080))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Bot തുടങ്ങുമ്പോൾ Webhook സജ്ജമാക്കുക
    if WEBHOOK_URL_BASE:
        await app.set_webhook(url=f"{WEBHOOK_URL_BASE}{WEBHOOK_PATH}")
        print("Webhook set successfully.")
        await app.start()
    else:
        # ലോക്കൽ ടെസ്റ്റിങ്ങിനായി പൂളിംഗ് (Pooling) രീതിയിൽ തുടങ്ങുക
        await app.start()
        print("Starting in Polling Mode (for local testing only).")
        
    yield
    # Bot നിർത്തുക
    await app.stop()
    print("Application stopped.")

# FastAPI instance
api_app = FastAPI(lifespan=lifespan)

# Webhook endpoint for Telegram updates
@api_app.post(WEBHOOK_PATH)
async def process_update(request: Request):
    """Telegram അപ്ഡേറ്റുകൾ സ്വീകരിക്കുന്നു."""
    try:
        req = await request.json()
        await app.process_update(req) # Pyrogram അപ്ഡേറ്റ് പ്രോസസ്സ് ചെയ്യുന്നു
        return Response(status_code=HTTPStatus.OK)
    except Exception as e:
        print(f"Error processing update: {e}")
        return Response(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

# Health Check endpoint for Render
@api_app.get("/")
async def health_check():
    """Render-ന്റെ Health Check."""
    return {"status": "ok"}

# --- Main Entry Point (Local Testing) ---

if __name__ == "__main__":
    if WEBHOOK_URL_BASE:
        # Render-ൽ Webhook മോഡിൽ പ്രവർത്തിപ്പിക്കാൻ
        uvicorn.run("main:api_app", host="0.0.0.0", port=PORT, log_level="info")
    else:
        # ലോക്കൽ ടെസ്റ്റിങ്ങിനായി പൂളിംഗ് മോഡ്
        print("Starting Pyrogram in Polling Mode...")
        app.run()
