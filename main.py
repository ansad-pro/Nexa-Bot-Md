import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import List, Dict, Any
from fastapi import FastAPI, Request, Response
from contextlib import asynccontextmanager
from http import HTTPStatus
import uvicorn

# .env ഫയലിൽ നിന്ന് വേരിയബിളുകൾ ലോഡ് ചെയ്യുന്നു (ലോക്കൽ ടെസ്റ്റിങ്ങിന്)
load_dotenv()

# --- Config Variables ---
# env വേരിയബിളുകൾ ഇല്ലെങ്കിൽ default വാല്യൂ നൽകുന്നു
# API_ID, BOT_TOKEN എന്നിവ integer ആണെന്ന് ഉറപ്പാക്കുന്നു
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
# PRIVATE_FILE_STORE, LOG_CHANNEL എന്നിവ integer ആണെന്ന് ഉറപ്പാക്കുന്നു
PRIVATE_FILE_STORE = int(os.environ.get("PRIVATE_FILE_STORE", -100))
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", -100))

# ADMINS ലിസ്റ്റ് ഉണ്ടാക്കുന്നു
ADMINS = []
admin_env = os.environ.get("ADMINS", "")
if admin_env:
    ADMINS = [int(admin.strip()) for admin in admin_env.split(',') if admin.strip().isdigit()]

DATABASE_URL = os.environ.get("DATABASE_URL", "mongodb://localhost:27017")
FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", None)

# Webhook Details
WEBHOOK_URL_BASE = os.environ.get("WEBHOOK_URL_BASE", None)
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_PATH = f"/{BOT_TOKEN}"

# --- MongoDB Setup ---

class Database:
    """ഡാറ്റാബേസ് പ്രവർത്തനങ്ങൾ കൈകാര്യം ചെയ്യുന്നു."""
    def __init__(self, uri: str, database_name: str):
        # ഇവിടെ database client initialize ചെയ്യുന്നു
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.files_col = self.db["files"] # ഫയൽ വിവരങ്ങൾ സൂക്ഷിക്കുന്ന Collection

    async def get_all_files(self) -> List[Dict[str, Any]]:
        """ഡാറ്റാബേസിലെ എല്ലാ ഫയൽ എൻട്രികളും ലിസ്റ്റ് ആയി തിരികെ നൽകുന്നു."""
        # Motor-ൽ നിന്നും Cursor-നെ ലിസ്റ്റ് ആയി മാറ്റാൻ to_list() ഉപയോഗിക്കുന്നു.
        cursor = self.files_col.find({})
        return await cursor.to_list(length=None)

    async def find_one(self, query: Dict[str, Any]) -> Dict[str, Any] | None:
        """ഒരു ഡോക്യുമെൻ്റ് തിരയുന്നു."""
        return await self.files_col.find_one(query)

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        """ഒരു ഡോക്യുമെൻ്റ് അപ്ഡേറ്റ് ചെയ്യുകയോ അല്ലെങ്കിൽ ചേർക്കുകയോ ചെയ്യുന്നു."""
        await self.files_col.update_one(query, update, upsert=upsert)

# ഡാറ്റാബേസ് ഇൻസ്റ്റൻസ്
db = Database(DATABASE_URL, "AutoFilterBot")

# --- Pyrogram Client ---
class AutoFilterBot(Client):
    def __init__(self):
        super().__init__(
            "AutoFilterBot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="plugins"), # പ്ലഗിനുകൾ ഇല്ലെങ്കിൽ ഇത് നീക്കം ചെയ്യാം
            sleep_threshold=30 # പ്രധാനമാണ്: കുറഞ്ഞ റിസോഴ്സ് ഉപയോഗത്തിനായി
        )

# --- Bot Instance (Global Pyrogram Client) ---
app = AutoFilterBot()

# --- Helpers ---

async def is_subscribed(client, user_id):
    """ഫോഴ്സ് സബ്സ്ക്രൈബ് ചാനലിൽ യൂസർ അംഗമാണോ എന്ന് പരിശോധിക്കുന്നു."""
    if not FORCE_SUB_CHANNEL:
        return True
    try:
        # get_chat_member-ന് യൂസർ ഐഡി വേണം, മെസ്സേജ് ഒബ്ജക്റ്റ് അല്ല
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id) 
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except UserNotParticipant:
        return False
    except Exception as e:
        print(f"Error checking subscription: {e}")
        # പിഴവുകൾ സംഭവിച്ചാൽ True നൽകി മുന്നോട്ട് പോകാൻ അനുവദിക്കുന്നു
        return True 

async def get_file_details(query):
    """ഡാറ്റാബേസിൽ നിന്ന് ഫയൽ വിവരങ്ങൾ തിരയുന്നു."""
    # 'i' case-insensitive search
    # file title, file caption എന്നിവയിൽ തിരയുന്നു
    cursor = db.files_col.find({ 
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"caption": {"$regex": query, "$options": "i"}}
        ]
    }).limit(10)
    
    files = await cursor.to_list(length=10)
    return files

# --- Handlers ---

@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    await message.reply_text(
        "👋 ഹായ്! ഞാൻ ഒരു ഓട്ടോ-ഫിൽട്ടർ ബോട്ടാണ്. എന്നെ നിങ്ങളുടെ ഗ്രൂപ്പിൽ ചേർത്താൽ, ഗ്രൂപ്പിൽ തിരയുന്ന ഫയലുകൾ ഞാൻ അയച്ചുതരും. കൂടുതൽ വിവരങ്ങൾക്ക് ഡെവലപ്പറെ ബന്ധപ്പെടുക."
    )

@app.on_message(filters.command("index") & filters.user(ADMINS))
async def index_command(client, message: Message):
    """അഡ്മിൻമാർക്ക് ഫയൽ സ്റ്റോർ ചാനലിലെ ഫയലുകൾ ഇൻഡക്സ് ചെയ്യാനുള്ള കമാൻഡ്."""
    if PRIVATE_FILE_STORE == -100:
        await message.reply_text("PRIVATE_FILE_STORE ID ENV വേരിയബിളിൽ നൽകിയിട്ടില്ല. ഇൻഡക്സിംഗ് സാധ്യമല്ല.")
        return

    msg = await message.reply_text("ഫയലുകൾ ഇൻഡക്സ് ചെയ്യാൻ തുടങ്ങുന്നു...")
    
    total_files = 0
    # chat_id-യിൽ നിന്നുള്ള എല്ലാ ഡോക്യുമെന്റുകളും തിരയുന്നു
    async for chat_msg in client.search_messages(chat_id=PRIVATE_FILE_STORE, filter="document"):
        if chat_msg.document:
            file_id = chat_msg.document.file_id
            file_name = chat_msg.document.file_name
            # caption ഉണ്ടെങ്കിൽ HTML ഫോർമാറ്റ് ഉപയോഗിക്കുന്നു
            caption = chat_msg.caption.html if chat_msg.caption else None 
            
            # ഡാറ്റാബേസിൽ ഫയൽ വിവരങ്ങൾ ചേർക്കുന്നു (title ഉപയോഗിച്ച്)
            await db.files_col.update_one( 
                {"file_id": file_id},
                {
                    "$set": {
                        "title": file_name,
                        "caption": caption,
                        "file_id": file_id,
                        "chat_id": PRIVATE_FILE_STORE,
                        "message_id": chat_msg.id,
                    }
                },
                upsert=True # ഫയൽ ഇല്ലെങ്കിൽ പുതിയതായി ചേർക്കുന്നു
            )
            total_files += 1
            
            if total_files % 100 == 0:
                 # 100 ഫയലുകൾ കഴിയുമ്പോൾ സ്റ്റാറ്റസ് അപ്ഡേറ്റ് ചെയ്യുന്നു
                 await msg.edit_text(f"✅ ഇൻഡക്സ് ചെയ്ത ഫയലുകൾ: {total_files}")
                 
    await msg.edit_text(f"🎉 ഇൻഡക്സിംഗ് പൂർത്തിയായി! ആകെ {total_files} ഫയലുകൾ ചേർത്തു.")


# Auto-Filter Handler
@app.on_message(filters.text & filters.private | filters.group & filters.text & filters.incoming & ~filters.command(["start", "index"])) 
async def auto_filter_handler(client, message: Message):
    """ടെക്സ്റ്റ് മെസ്സേജുകൾ വരുമ്പോൾ ഫിൽട്ടർ ഫയലുകൾ തിരയുന്നു."""
    query = message.text.strip()
    
    # 1. ഫോഴ്സ് സബ്സ്ക്രൈബ് ചെക്ക്
    is_private = message.chat.type == "private"
    if not is_private or await is_subscribed(client, message.from_user.id):
        
        # 2. കോപ്പിറൈറ്റ് മെസ്സേജ് ഡിലീറ്റ് ലോജിക് (അഡ്മിൻ ഗ്രൂപ്പിൽ മാത്രമേ പ്രവർത്തിക്കൂ)
        COPYRIGHT_KEYWORDS = ["copyright", "unauthorized", "DMCA", "piracy", "പകർപ്പവകാശം", "അനുമതിയില്ലാതെ"] 
        if message.chat.type in ["group", "supergroup"] and message.chat.id in ADMINS and any(keyword.lower() in query.lower() for keyword in COPYRIGHT_KEYWORDS):
             try:
                 await message.delete()
                 await client.send_message(LOG_CHANNEL, f"🚫 **കോപ്പിറൈറ്റ് സന്ദേശം നീക്കം ചെയ്തു!**\n\n**ചാറ്റ് ID:** `{message.chat.id}`\n**യൂസർ:** {message.from_user.mention}\n**സന്ദേശം:** `{query}`")
                 return
             except Exception as e:
                 print(f"Error deleting copyright message: {e}")
        
        # 3. ഓട്ടോ-ഫിൽട്ടർ തിരയൽ
        files = await get_file_details(query)
        
        if files:
            # ഫയൽ കണ്ടെത്തിയാൽ ഇൻലൈൻ ബട്ടണുകൾ അയക്കുന്നു
            text = f"ഇതാ നിങ്ങൾ തിരഞ്ഞ **{query}**-യുമായി ബന്ധപ്പെട്ട ഫയലുകൾ:\n\n"
            buttons = []
            for file in files:
                file_name = file.get("title", "File").rsplit('.', 1)[0].strip() # Extension ഒഴിവാക്കുന്നു
                
                buttons.append([
                    InlineKeyboardButton(
                        text=file_name,
                        callback_data=f"getfile_{file.get('file_id')}" 
                    )
                ])
            
            # ഒരു ബട്ടൺ 'കൂടുതൽ' എന്ന് ചേർക്കുന്നു
            if len(files) == 10:
                 buttons.append([InlineKeyboardButton("കൂടുതൽ ഫലങ്ങൾ", url="https://t.me/your_search_group")]) # ഒരു സപ്പോർട്ട് ഗ്രൂപ്പ് ലിങ്ക് ചേർക്കുക

            await message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True
            )

    elif is_private:
        # ഫോഴ്സ് സബ്സ്ക്രൈബ് ചെയ്തിട്ടില്ലെങ്കിൽ
        if not FORCE_SUB_CHANNEL: return # ചാനൽ ഇല്ലെങ്കിൽ ഒന്നും ചെയ്യേണ്ട
        
        join_button = [
            [InlineKeyboardButton("ചാനലിൽ ചേരുക", url=f"https://t.me/{FORCE_SUB_CHANNEL.replace('@', '')}")]
        ]
        await message.reply_text(
            f"നിങ്ങൾക്ക് ഫയലുകൾ ലഭിക്കണമെങ്കിൽ ആദ്യം ഞങ്ങളുടെ ചാനലിൽ ചേരുക.",
            reply_markup=InlineKeyboardMarkup(join_button)
        )

# --- Callback Query Handler (Inline Button Click) ---

@app.on_callback_query(filters.regex("^getfile_"))
async def send_file_handler(client, callback):
    """ബട്ടണിൽ ക്ലിക്കുമ്പോൾ ഫയൽ അയക്കുന്നു."""
    
    # ഫോഴ്സ് സബ്സ്ക്രൈബ് ചെക്ക്
    if FORCE_SUB_CHANNEL and not await is_subscribed(client, callback.from_user.id):
        await callback.answer("ഫയൽ ലഭിക്കാൻ ചാനലിൽ ചേരുക.", show_alert=True)
        return

    file_id = callback.data.split("_")[1]
    file = await db.files_col.find_one({"file_id": file_id}) 
    
    if file:
        try:
            # ഫയൽ ഒറിജിനൽ സ്റ്റോർ ചാനലിൽ നിന്ന് ഫോർവേഡ് ചെയ്യുന്നു
            await client.forward_messages(
                chat_id=callback.message.chat.id,
                from_chat_id=file['chat_id'],
                message_ids=file['message_id']
            )
            await callback.answer("ഫയൽ അയച്ചിരിക്കുന്നു.", show_alert=False)
        except Exception as e:
            # പലപ്പോഴും ഫോർവേഡ് ചെയ്യുമ്പോൾ പിശക് വരാറുണ്ട് (പ്രൈവറ്റ് ചാനലുകൾ കാരണം)
            await callback.answer("ഫയൽ അയക്കുന്നതിൽ ഒരു പിഴവ് സംഭവിച്ചു. ബോട്ടിന് ആക്സസ് ഉണ്ടോയെന്ന് പരിശോധിക്കുക.", show_alert=True)
            print(f"File forward error: {e}")
    else:
        await callback.answer("ഫയൽ ഡാറ്റാബേസിൽ നിന്ന് നീക്കം ചെയ്യപ്പെട്ടു.", show_alert=True)
    
    # തിരയൽ ഫലം കാണിച്ച മെസ്സേജ് ഡിലീറ്റ് ചെയ്യുന്നു (ഓപ്ഷണൽ)
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Error deleting inline message: {e}")

# --- Render Webhook Setup (FastAPI for a scalable deployment) ---

# --- STARTUP/SHUTDOWN Lifecycle ---
async def startup_initial_checks():
    """തുടങ്ങുമ്പോൾ ചെയ്യേണ്ട ചെക്കുകൾ."""
    print("Running initial startup checks...")
    try:
        # DB connection test
        files_count = len(await db.get_all_files())
        print(f"Database check completed. Found {files_count} files in the database.")
    except Exception as e:
        print(f"Warning: Database check failed during startup: {e}")


@asynccontextmanager
async def lifespan(web_app: FastAPI):
    # 'web_app' എന്നത് FastAPI ഇൻസ്റ്റൻസ് ആണ്. Pyrogram client 'app' എന്ന ഗ്ലോബൽ വേരിയബിളാണ്.

    # 1. പ്രധാനപ്പെട്ട startup ചെക്കുകൾ റൺ ചെയ്യുന്നു
    await startup_initial_checks()
    
    # 2. Pyrogram client തുടങ്ങുന്നു
    if WEBHOOK_URL_BASE:
        # ഇത് Render-ൽ വെബ്ഹുക്ക് വഴി പ്രവർത്തിക്കാൻ: Pyrogram client നെ സ്റ്റാർട്ട് ചെയ്യുക
        await app.start() 
        
        # Pyrogram client ഉപയോഗിച്ച് Webhook സജ്ജമാക്കുക
        await app.set_webhook(url=f"{WEBHOOK_URL_BASE}{WEBHOOK_PATH}")
        print(f"Webhook set successfully to: {WEBHOOK_URL_BASE}{WEBHOOK_PATH}")
    else:
        # ലോക്കൽ ടെസ്റ്റിങ്ങിനായി പൂളിംഗ് (Pooling) രീതിയിൽ തുടങ്ങുക (Render-ൽ ഈ ഭാഗം റൺ ചെയ്യില്ല)
        await app.start()
        print("Starting in Polling Mode (for local testing only).")
        
    yield
    # 3. Bot നിർത്തുക
    await app.stop() # Pyrogram client (global 'app') നെ നിർത്തുക
    print("Application stopped.")

# FastAPI instance (Global variable 'api_app' used in uvicorn command)
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

# --- Main Entry Point ---

if __name__ == "__main__":
    if WEBHOOK_URL_BASE:
        # Render-ൽ Webhook മോഡിൽ പ്രവർത്തിപ്പിക്കാൻ (uvicorn main:api_app)
        uvicorn.run("main:api_app", host="0.0.0.0", port=PORT, log_level="info")
    else:
        # ലോക്കൽ ടെസ്റ്റിങ്ങിനായി പൂളിംഗ് മോഡ്
        print("Starting Pyrogram in Polling Mode...")
        asyncio.run(startup_initial_checks())
        app.run()
