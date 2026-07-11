import asyncio
import json
import os
import logging
import re
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telethon import TelegramClient, errors
from telethon.tl.types import SendMessageTypingAction

# ========== بيانات السيد ==========
BOT_TOKEN = "8934572996:AAH_EuDM_AeQOVzw7WPMf8qwNuNR7rl_qpc"
ADMIN_ID = 7863628255  # فقط للحذف ولوحة الأدمن
CONFIG_FILE = "sahar_config.json"
API_ID = 21243948
API_HASH = "24bb23cd54ce9cb9e5fe0c22dfe0a333"

# ========== إعدادات المحاكاة البشرية ==========
MIN_DELAY = 60
MAX_DELAY = 120
TYPING_MIN = 2
TYPING_MAX = 4
BREAK_AFTER = 6
BREAK_MIN = 240
BREAK_MAX = 720
SLEEP_HOUR_START = 2
SLEEP_HOUR_END = 7

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== إدارة الملفات ==========
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"groups": []}

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# ========== متغيرات عالمية ==========
login_states = {}
user_clients = {}
user_messages = {}      # {user_id: [كليشة1, كليشة2, كليشة3, كليشة4]}
user_loops = {}
user_counts = {}
user_running = {}
admin_states = {}
daily_sent = {}
user_setup_states = {}  # {user_id: {'step': 1-4, 'temp': []}}
add_group_states = {}   # {user_id: True} لمن يضغط إضافة جروب

# ========== دالة التحقق من وقت النوم ==========
def is_sleep_time():
    now = datetime.now().hour
    if SLEEP_HOUR_START <= SLEEP_HOUR_END:
        return SLEEP_HOUR_START <= now < SLEEP_HOUR_END
    else:
        return now >= SLEEP_HOUR_START or now < SLEEP_HOUR_END

# ========== دالة استخراج المعرف ==========
def extract_chat_id(text):
    text = text.strip()
    if re.match(r'^-?\d+$', text):
        return text
    match = re.search(r'(?:https?://)?(?:www\.)?t\.me/([a-zA-Z0-9_]+)', text)
    if match:
        return f"@{match.group(1)}"
    if text.startswith('@'):
        return text
    if re.match(r'^[a-zA-Z0-9_]+$', text):
        return f"@{text}"
    match = re.search(r'@([a-zA-Z0-9_]+)', text)
    if match:
        return f"@{match.group(1)}"
    return None

# ========== دالة محاكاة الكتابة ==========
async def simulate_typing(client, chat_id):
    try:
        duration = random.randint(TYPING_MIN, TYPING_MAX)
        if chat_id.lstrip('-').isdigit():
            await client.send_action(int(chat_id), SendMessageTypingAction())
        else:
            await client.send_action(chat_id, SendMessageTypingAction())
        await asyncio.sleep(duration)
        return True
    except Exception as e:
        logger.warning(f"فشلت محاكاة الكتابة: {e}")
        return False

# ========== دوال النشر ==========
async def send_telethon_message(client, chat_id, text, user_id):
    today = datetime.now().date().isoformat()
    if user_id not in daily_sent or daily_sent[user_id]['date'] != today:
        daily_sent[user_id] = {'count': 0, 'date': today}
    if daily_sent[user_id]['count'] >= 3000:
        logger.warning(f"⚠️ المستخدم {user_id} وصل للحد اليومي")
        return False

    try:
        await simulate_typing(client, chat_id)
        if chat_id.lstrip('-').isdigit():
            await client.send_message(int(chat_id), text)
        else:
            await client.send_message(chat_id, text)
        daily_sent[user_id]['count'] += 1
        logger.info(f"✅ أرسلت إلى {chat_id}")
        wait = random.randint(MIN_DELAY, MAX_DELAY)
        await asyncio.sleep(wait)
        return True
    except errors.FloodWaitError as e:
        wait = e.seconds + random.randint(10, 30)
        logger.warning(f"⏳ FloodWait! انتظار {wait} ثانية...")
        await asyncio.sleep(wait)
        return False
    except Exception as e:
        logger.error(f"❌ فشل الإرسال: {e}")
        return False

async def user_repeat_task(user_id):
    logger.info(f"🔥 بدء مهمة النشر للمستخدم {user_id}")
    while True:
        try:
            if is_sleep_time():
                logger.info(f"💤 وقت النوم! التوقف من {SLEEP_HOUR_START} إلى {SLEEP_HOUR_END}")
                await asyncio.sleep(3600)
                continue
            if user_id not in user_clients or not user_running.get(user_id, False):
                logger.info(f"⏹️ إيقاف مهمة المستخدم {user_id}")
                break
            client = user_clients[user_id]
            if not client.is_connected():
                try:
                    await client.connect()
                except Exception as e:
                    logger.error(f"❌ فشل إعادة الاتصال: {e}")
                    await asyncio.sleep(30)
                    continue
            config = load_config()
            groups = config.get("groups", [])
            messages = user_messages.get(user_id, [])
            if len(messages) < 4:
                logger.warning(f"⚠️ المستخدم {user_id} لديه {len(messages)} كليشة فقط (يحتاج 4)")
                await asyncio.sleep(30)
                continue
            if not groups:
                await asyncio.sleep(30)
                continue
            shuffled_groups = groups.copy()
            random.shuffle(shuffled_groups)
            logger.info(f"📤 المستخدم {user_id} - إرسال إلى {len(groups)} جروب")
            for idx, gid in enumerate(shuffled_groups):
                if not user_running.get(user_id, False):
                    break
                selected_text = random.choice(messages)
                success = await send_telethon_message(client, gid, selected_text, user_id)
                if success:
                    user_counts[user_id] = user_counts.get(user_id, 0) + 1
                if (idx + 1) % BREAK_AFTER == 0 and idx + 1 < len(shuffled_groups):
                    break_duration = random.randint(BREAK_MIN, BREAK_MAX)
                    logger.info(f"☕ استراحة قصيرة لمدة {break_duration} ثانية...")
                    await asyncio.sleep(break_duration)
            if user_running.get(user_id, False):
                await asyncio.sleep(random.randint(30, 60))
        except asyncio.CancelledError:
            logger.info(f"⏹️ تم إلغاء مهمة المستخدم {user_id}")
            break
        except Exception as e:
            logger.error(f"💥 خطأ: {e}")
            await asyncio.sleep(30)

# ========== القائمة الرئيسية (أزرار مختصرة جداً) ==========
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    user_id = update.effective_user.id
    is_logged = user_id in user_clients and user_clients[user_id].is_connected()
    status = "🟢" if is_logged else "🔴"
    messages = user_messages.get(user_id, [])
    msg_preview = f"{len(messages)} ك" if messages else "0"
    is_running = user_running.get(user_id, False)
    config = load_config()
    groups_count = len(config.get("groups", []))
    sent_count = user_counts.get(user_id, 0)

    # أزرار مختصرة جداً
    keyboard = [
        [InlineKeyboardButton(f"{'🔐' if not is_logged else '🔓'} الحساب", callback_data='toggle_login')],
        [InlineKeyboardButton("📝 كليشاتي", callback_data='setup_messages')],
        [InlineKeyboardButton("📋 عرض ك", callback_data='show_messages')],
        [InlineKeyboardButton("▶️ تشغيل", callback_data='start_loop') if not is_running else InlineKeyboardButton("⏹️ إيقاف", callback_data='stop_loop')],
        [InlineKeyboardButton("🚀 نشر فوري", callback_data='publish_now')],
        [InlineKeyboardButton("➕ إضافة جروب", callback_data='add_group')],
        [InlineKeyboardButton("📋 جروباتي", callback_data='list_groups')],
    ]
    # لوحة الأدمن للمدير فقط
    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ إدارة", callback_data='admin_panel')])
    keyboard.append([InlineKeyboardButton("🚪 خروج", callback_data='logout')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    sleep_status = "💤" if is_sleep_time() else "🟢"
    text = (
        f"🔥 **النشر الذكي**\n"
        f"{status} {msg_preview} ك | {groups_count} ج | {sent_count} رسالة\n"
        f"{'🔄 يعمل' if is_running else '⏸️ متوقف'} | {sleep_status}\n\n"
        f"اختر:"
    )
    if edit and update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# ========== لوحة الأدمن ==========
async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ للمدير فقط.")
        return
    config = load_config()
    groups = config.get("groups", [])
    keyboard = [
        [InlineKeyboardButton("🗑️ حذف جروب", callback_data='admin_remove_group')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"⚙️ **إدارة الجروبات**\n📊 المحفوظة: {len(groups)}"
    if edit and update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# ========== أوامر البوت ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_admin_panel(update, context)

# ========== تسجيل الدخول/الخروج ==========
async def toggle_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id in user_clients and user_clients[user_id].is_connected():
        # تسجيل خروج
        if user_running.get(user_id, False):
            user_running[user_id] = False
            if user_id in user_loops and not user_loops[user_id].done():
                user_loops[user_id].cancel()
        try:
            await user_clients[user_id].disconnect()
        except:
            pass
        del user_clients[user_id]
        await query.edit_message_text("🚪 تم الخروج.")
        await show_main_menu(update, context, edit=True)
    else:
        # بدء تسجيل الدخول
        login_states[user_id] = {'step': 'phone'}
        await query.edit_message_text("📱 أدخل رقم الهاتف مع رمز الدولة:")

async def handle_login_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in login_states:
        return
    state = login_states[user_id]
    text = update.message.text.strip()
    
    if state['step'] == 'phone':
        state['phone'] = text
        state['step'] = 'code'
        login_states[user_id] = state
        try:
            session_file = f"session_{user_id}.session"
            client = TelegramClient(session_file, API_ID, API_HASH)
            await client.connect()
            if not await client.is_user_authorized():
                result = await client.send_code_request(text)
                state['phone_code_hash'] = result.phone_code_hash
                login_states[user_id] = state
                await update.message.reply_text("✅ أرسل الكود:")
            else:
                await client.start(phone=text)
                user_clients[user_id] = client
                user_running[user_id] = False
                await update.message.reply_text("✅ تم الدخول.")
                del login_states[user_id]
                await show_main_menu(update, context)
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ: {e}")
            del login_states[user_id]
    
    elif state['step'] == 'code':
        try:
            session_file = f"session_{user_id}.session"
            client = TelegramClient(session_file, API_ID, API_HASH)
            await client.connect()
            await client.sign_in(state['phone'], code=text, phone_code_hash=state.get('phone_code_hash'))
            user_clients[user_id] = client
            user_running[user_id] = False
            await update.message.reply_text("✅ تم الدخول!")
            del login_states[user_id]
            await show_main_menu(update, context)
        except errors.SessionPasswordNeededError:
            state['step'] = 'password'
            login_states[user_id] = state
            await update.message.reply_text("🔐 أدخل كلمة المرور:")
        except errors.PhoneCodeInvalidError:
            await update.message.reply_text("❌ كود خاطئ، حاول مرة أخرى:")
            state['step'] = 'code'
            login_states[user_id] = state
        except Exception as e:
            await update.message.reply_text(f"❌ فشل: {e}")
            del login_states[user_id]
    
    elif state['step'] == 'password':
        try:
            session_file = f"session_{user_id}.session"
            client = TelegramClient(session_file, API_ID, API_HASH)
            await client.connect()
            await client.sign_in(password=text)
            user_clients[user_id] = client
            user_running[user_id] = False
            await update.message.reply_text("✅ تم الدخول!")
            del login_states[user_id]
            await show_main_menu(update, context)
        except Exception as e:
            await update.message.reply_text(f"❌ كلمة مرور خاطئة: {e}")
            state['step'] = 'password'
            login_states[user_id] = state

# ========== نظام إدخال الـ 4 كليشات ==========
async def setup_messages_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_setup_states[user_id] = {'step': 1, 'temp': []}
    await query.edit_message_text("✏️ **أدخل الكليشة 1 من 4**\nمثال: `توفر لدينا حسابات`")

async def handle_setup_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_setup_states:
        return
    state = user_setup_states[user_id]
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("❌ النص فارغ.")
        return
    state['temp'].append(text)
    state['step'] += 1
    if state['step'] <= 4:
        await update.message.reply_text(f"✏️ **أدخل الكليشة {state['step']} من 4**")
    else:
        user_messages[user_id] = state['temp']
        del user_setup_states[user_id]
        await update.message.reply_text(
            "✅ **تم حفظ 4 كليشات!**\n"
            f"1️⃣ {state['temp'][0]}\n2️⃣ {state['temp'][1]}\n3️⃣ {state['temp'][2]}\n4️⃣ {state['temp'][3]}"
        )
        await show_main_menu(update, context)

async def show_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    messages = user_messages.get(user_id, [])
    if len(messages) < 4:
        await query.edit_message_text("📭 لا توجد 4 كليشات كاملة.")
        return
    text = "📌 **كليشاتك:**\n" + "\n".join([f"{i}️⃣ {m}" for i, m in enumerate(messages, 1)])
    await query.edit_message_text(text, parse_mode='Markdown')

# ========== إضافة جروب (لأي مستخدم) ==========
async def add_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    add_group_states[user_id] = True
    await query.edit_message_text("➕ أرسل رابط أو معرف الجروب (مثال: t.me/username أو -100123)")

async def handle_add_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in add_group_states:
        return
    text = update.message.text.strip()
    chat_id = extract_chat_id(text)
    if not chat_id:
        await update.message.reply_text("❌ رابط أو معرف غير صالح.")
        return
    config = load_config()
    if chat_id not in config["groups"]:
        config["groups"].append(chat_id)
        save_config(config)
        await update.message.reply_text(f"✅ تم إضافة {chat_id}")
    else:
        await update.message.reply_text("⚠️ موجود مسبقاً.")
    del add_group_states[user_id]
    await show_main_menu(update, context)

async def list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    config = load_config()
    groups = config.get("groups", [])
    if groups:
        await query.edit_message_text("📋 الجروبات:\n" + "\n".join(groups), parse_mode='Markdown')
    else:
        await query.edit_message_text("📭 لا توجد جروبات.")

# ========== معالجة الأزرار ==========
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == 'toggle_login':
        await toggle_login(update, context)
    elif data == 'setup_messages':
        await setup_messages_start(update, context)
    elif data == 'show_messages':
        await show_messages(update, context)
    elif data == 'start_loop':
        if user_id not in user_clients or not user_clients[user_id].is_connected():
            await query.edit_message_text("❌ سجل الدخول أولاً.")
            return
        if user_running.get(user_id, False):
            await query.edit_message_text("⚠️ يعمل مسبقاً.")
            return
        if len(user_messages.get(user_id, [])) < 4:
            await query.edit_message_text("⚠️ أدخل 4 كليشات أولاً.")
            return
        user_counts[user_id] = 0
        user_running[user_id] = True
        task = asyncio.create_task(user_repeat_task(user_id))
        user_loops[user_id] = task
        await query.edit_message_text("🚀 تم التشغيل.")
        await show_main_menu(update, context, edit=True)
    elif data == 'stop_loop':
        if user_running.get(user_id, False):
            user_running[user_id] = False
            if user_id in user_loops and not user_loops[user_id].done():
                user_loops[user_id].cancel()
            await query.edit_message_text("⏹️ تم الإيقاف.")
        else:
            await query.edit_message_text("⚠️ غير مفعل.")
        await show_main_menu(update, context, edit=True)
    elif data == 'publish_now':
        if user_id not in user_clients or not user_clients[user_id].is_connected():
            await query.edit_message_text("❌ سجل الدخول أولاً.")
            return
        client = user_clients[user_id]
        config = load_config()
        groups = config.get("groups", [])
        messages = user_messages.get(user_id, [])
        if not groups or len(messages) < 4:
            await query.edit_message_text("⚠️ لا توجد جروبات أو 4 كليشات.")
            return
        await query.edit_message_text("⏳ جاري...")
        success = 0
        for gid in groups:
            selected = random.choice(messages)
            if await send_telethon_message(client, gid, selected, user_id):
                success += 1
                user_counts[user_id] = user_counts.get(user_id, 0) + 1
        await query.edit_message_text(f"✅ تم النشر في {success} من {len(groups)} جروب.")
        await show_main_menu(update, context, edit=True)
    elif data == 'add_group':
        await add_group_start(update, context)
    elif data == 'list_groups':
        await list_groups(update, context)
    elif data == 'logout':
        if user_running.get(user_id, False):
            user_running[user_id] = False
            if user_id in user_loops and not user_loops[user_id].done():
                user_loops[user_id].cancel()
        if user_id in user_clients:
            try:
                await user_clients[user_id].disconnect()
            except:
                pass
            del user_clients[user_id]
        if user_id in user_messages:
            del user_messages[user_id]
        if user_id in user_counts:
            del user_counts[user_id]
        if user_id in user_running:
            del user_running[user_id]
        if user_id in user_setup_states:
            del user_setup_states[user_id]
        if user_id in add_group_states:
            del add_group_states[user_id]
        await query.edit_message_text("🚪 خروج.")
        await show_main_menu(update, context, edit=True)
    elif data == 'admin_panel':
        await show_admin_panel(update, context, edit=True)
    elif data == 'back_to_main':
        await show_main_menu(update, context, edit=True)
    elif data == 'admin_remove_group':
        config = load_config()
        groups = config.get("groups", [])
        if not groups:
            await query.edit_message_text("📭 لا توجد جروبات.")
            return
        keyboard = [[InlineKeyboardButton(f"🗑️ {g}", callback_data=f'remove_{g}')] for g in groups]
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')])
        await query.edit_message_text("اختر جروباً للحذف:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data.startswith('remove_'):
        gid = data.replace('remove_', '')
        config = load_config()
        if gid in config["groups"]:
            config["groups"].remove(gid)
            save_config(config)
            await query.edit_message_text(f"✅ تم حذف {gid}")
            await show_admin_panel(update, context, edit=True)

# ========== معالجة الرسائل النصية ==========
async def handle_message_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if user_id in login_states:
        await handle_login_input(update, context)
        return
    if user_id in user_setup_states:
        await handle_setup_messages(update, context)
        return
    if user_id in add_group_states:
        await handle_add_group(update, context)
        return
    # أي رسالة أخرى
    await update.message.reply_text("استخدم الأزرار.")

# ========== التشغيل ==========
def main():
    try:
        from telegram.ext import JobQueue
    except ImportError:
        logger.error("⚠️ يرجى تثبيت job-queue: pip install 'python-telegram-bot[job-queue]'")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_input))
    
    logger.info("🔥 البوت شغال - أزرار مختصرة وإضافة جروبات للجميع.")
    app.run_polling()

if __name__ == "__main__":
    main()