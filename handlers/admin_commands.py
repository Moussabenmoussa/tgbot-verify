"""Admin Command Handler"""
import asyncio
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_USER_ID
from database_mysql import Database
from utils.checks import reject_group_command

logger = logging.getLogger(__name__)


async def addbalance_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /addbalance command - Admin adds balance"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /addbalance <User ID> <Amount>\n\nExample: /addbalance 123456789 10"
        )
        return

    try:
        target_user_id = int(context.args[0])
        amount = int(context.args[1])

        if not db.user_exists(target_user_id):
            await update.message.reply_text("User does not exist.")
            return

        if db.add_balance(target_user_id, amount):
            user = db.get_user(target_user_id)
            await update.message.reply_text(
                f"✅ Successfully added {amount} balance to user {target_user_id}.\n"
                f"Current balance: {user['balance']}"
            )
        else:
            await update.message.reply_text("Operation failed, please try again later.")
    except ValueError:
        await update.message.reply_text("Parameter format error, please enter valid numbers.")


async def block_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /block command - Admin blocks user"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /block <User ID>\n\nExample: /block 123456789"
        )
        return

    try:
        target_user_id = int(context.args[0])

        if not db.user_exists(target_user_id):
            await update.message.reply_text("User does not exist.")
            return

        if db.block_user(target_user_id):
            await update.message.reply_text(f"✅ User {target_user_id} has been blocked.")
        else:
            await update.message.reply_text("Operation failed, please try again later.")
    except ValueError:
        await update.message.reply_text("Parameter format error, please enter a valid User ID.")


async def white_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /white command - Admin unblocks user"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /white <User ID>\n\nExample: /white 123456789"
        )
        return

    try:
        target_user_id = int(context.args[0])

        if not db.user_exists(target_user_id):
            await update.message.reply_text("User does not exist.")
            return

        if db.unblock_user(target_user_id):
            await update.message.reply_text(f"✅ User {target_user_id} has been removed from the blacklist.")
        else:
            await update.message.reply_text("Operation failed, please try again later.")
    except ValueError:
        await update.message.reply_text("Parameter format error, please enter a valid User ID.")


async def blacklist_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /blacklist command - View blacklist"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    blacklist = db.get_blacklist()

    if not blacklist:
        await update.message.reply_text("The blacklist is empty.")
        return

    msg = "📋 Blacklist:\n\n"
    for user in blacklist:
        msg += f"User ID: {user['user_id']}\n"
        msg += f"Username: @{user['username']}\n"
        msg += f"Name: {user['full_name']}\n"
        msg += "---\n"

    await update.message.reply_text(msg)


async def genkey_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /genkey command - Admin generates card key"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /genkey <Key Code> <Balance> [Uses] [Expiration Days]\n\n"
            "Example:\n"
            "/genkey wandouyu 20 - Generate a 20-balance key (single use, never expires)\n"
            "/genkey vip100 50 10 - Generate a 50-balance key (can be used 10 times, never expires)\n"
            "/genkey temp 30 1 7 - Generate a 30-balance key (single use, expires in 7 days)"
        )
        return

    try:
        key_code = context.args[0].strip()
        balance = int(context.args[1])
        max_uses = int(context.args[2]) if len(context.args) > 2 else 1
        expire_days = int(context.args[3]) if len(context.args) > 3 else None

        if balance <= 0:
            await update.message.reply_text("Balance amount must be greater than 0.")
            return

        if max_uses <= 0:
            await update.message.reply_text("Number of uses must be greater than 0.")
            return

        if db.create_card_key(key_code, balance, user_id, max_uses, expire_days):
            msg = (
                "✅ Key generated successfully!\n\n"
                f"Key: {key_code}\n"
                f"Balance: {balance}\n"
                f"Uses: {max_uses} times\n"
            )
            if expire_days:
                msg += f"Validity: {expire_days} days\n"
            else:
                msg += "Validity: Permanent\n"
            msg += f"\nUsage for users: /use {key_code}"
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("Key already exists or generation failed, please use a different key name.")
    except ValueError:
        await update.message.reply_text("Parameter format error, please enter valid numbers.")


async def listkeys_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /listkeys command - Admin views key list"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    keys = db.get_all_card_keys()

    if not keys:
        await update.message.reply_text("No keys available.")
        return

    msg = "📋 Key List:\n\n"
    for key in keys[:20]:  # Only show the first 20
        msg += f"Key: {key['key_code']}\n"
        msg += f"Balance: {key['balance']}\n"
        msg += f"Uses: {key['current_uses']}/{key['max_uses']}\n"

        if key["expire_at"]:
            expire_time = datetime.fromisoformat(key["expire_at"])
            if datetime.now() > expire_time:
                msg += "Status: Expired\n"
            else:
                days_left = (expire_time - datetime.now()).days
                msg += f"Status: Valid ({days_left} days remaining)\n"
        else:
            msg += "Status: Permanently valid\n"

        msg += "---\n"

    if len(keys) > 20:
        msg += f"\n(Showing only the first 20, total {len(keys)})"

    await update.message.reply_text(msg)


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /broadcast command - Admin broadcasts notification"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    text = " ".join(context.args).strip() if context.args else ""
    if not text and update.message.reply_to_message:
        text = update.message.reply_to_message.text or ""

    if not text:
        await update.message.reply_text("Usage: /broadcast <Text>, or reply to a message and send /broadcast")
        return

    user_ids = db.get_all_user_ids()
    success, failed = 0, 0

    status_msg = await update.message.reply_text(f"📢 Starting broadcast to {len(user_ids)} users...")

    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
            success += 1
            await asyncio.sleep(0.05)  # Apply appropriate rate limiting to avoid triggering restrictions
        except Exception as e:
            logger.warning("Broadcast to %s failed: %s", uid, e)
            failed += 1

    await status_msg.edit_text(f"✅ Broadcast complete!\nSuccess: {success}\nFailed: {failed}")
