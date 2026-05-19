# Copyright (c) 2025 devgagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

import asyncio
import psutil
from datetime import timedelta, datetime
from shared_client import client as bot_client
from telethon import events
from utils.func import get_premium_details, is_private_chat, get_display_name, get_user_data, premium_users_collection, is_premium_user, users_collection
from config import OWNER_ID
import logging
logging.basicConfig(format=
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger('teamspy')


@bot_client.on(events.NewMessage(pattern='/status'))
async def status_handler(event):
    if not await is_private_chat(event):
        await event.respond("This command can only be used in private chats for security reasons.")
        return
    
    """Handle /status command to check user session and bot status"""
    user_id = event.sender_id
    user_data = await get_user_data(user_id)
    
    session_active = False
    bot_active = False
    
    if user_data and "session_string" in user_data:
            session_active = True
    
    # Check if user has a custom bot
    if user_data and "bot_token" in user_data:
        bot_active = True
    
    # Add premium status check
    premium_status = "❌ Not a premium member"
    premium_details = await get_premium_details(user_id)
    if premium_details:
        # Convert to IST timezone
        expiry_utc = premium_details["subscription_end"]
        expiry_ist = expiry_utc + timedelta(hours=5, minutes=30)
        formatted_expiry = expiry_ist.strftime("%d-%b-%Y %I:%M:%S %p")
        premium_status = f"✅ Premium until {formatted_expiry} (IST)"
    
    await event.respond(
        "**Your current status:**\n\n"
        f"**Login Status:** {'✅ Active' if session_active else '❌ Inactive'}\n"
        f"**Premium:** {premium_status}"
    )

@bot_client.on(events.NewMessage(pattern='/transfer'))
async def transfer_premium_handler(event):
    if not await is_private_chat(event):
        await event.respond(
            'This command can only be used in private chats for security reasons.'
            )
        return
    user_id = event.sender_id
    sender = await event.get_sender()
    sender_name = get_display_name(sender)
    if not await is_premium_user(user_id):
        await event.respond(
            "❌ You don't have a premium subscription to transfer.")
        return
    args = event.text.split()
    if len(args) != 2:
        await event.respond(
            'Usage: /transfer user_id\nExample: /transfer 123456789')
        return
    try:
        target_user_id = int(args[1])
    except ValueError:
        await event.respond(
            '❌ Invalid user ID. Please provide a valid numeric user ID.')
        return
    if target_user_id == user_id:
        await event.respond('❌ You cannot transfer premium to yourself.')
        return
    if await is_premium_user(target_user_id):
        await event.respond(
            '❌ The target user already has a premium subscription.')
        return
    try:
        premium_details = await get_premium_details(user_id)
        if not premium_details:
            await event.respond('❌ Error retrieving your premium details.')
            return
        target_name = 'Unknown'
        try:
            target_entity = await bot_client.get_entity(target_user_id)
            target_name = get_display_name(target_entity)
        except Exception as e:
            logger.warning(f'Could not get target user name: {e}')
        now = datetime.now()
        expiry_date = premium_details['subscription_end']
        await premium_users_collection.update_one({'user_id':
            target_user_id}, {'$set': {'user_id': target_user_id,
            'subscription_start': now, 'subscription_end': expiry_date,
            'expireAt': expiry_date, 'transferred_from': user_id,
            'transferred_from_name': sender_name}}, upsert=True)
        await premium_users_collection.delete_one({'user_id': user_id})
        expiry_ist = expiry_date + timedelta(hours=5, minutes=30)
        formatted_expiry = expiry_ist.strftime('%d-%b-%Y %I:%M:%S %p')
        await event.respond(
            f'✅ Premium subscription successfully transferred to {target_name} ({target_user_id}). Your premium access has been removed.'
            )
        try:
            await bot_client.send_message(target_user_id,
                f'🎁 You have received a premium subscription transfer from {sender_name} ({user_id}). Your premium is valid until {formatted_expiry} (IST).'
                )
        except Exception as e:
            logger.error(f'Could not notify target user {target_user_id}: {e}')
        try:
            owner_id = int(OWNER_ID) if isinstance(OWNER_ID, str
                ) else OWNER_ID[0] if isinstance(OWNER_ID, list) else OWNER_ID
            await bot_client.send_message(owner_id,
                f'♻️ Premium Transfer: {sender_name} ({user_id}) has transferred their premium to {target_name} ({target_user_id}). Expiry: {formatted_expiry}'
                )
        except Exception as e:
            logger.error(f'Could not notify owner about premium transfer: {e}')
        return
    except Exception as e:
        logger.error(
            f'Error transferring premium from {user_id} to {target_user_id}: {e}'
            )
        await event.respond(f'❌ Error transferring premium: {str(e)}')
        return
@bot_client.on(events.NewMessage(pattern='/rem'))
async def remove_premium_handler(event):
    user_id = event.sender_id
    if not await is_private_chat(event):
        return
    if user_id not in OWNER_ID:
        return
    args = event.text.split()
    if len(args) != 2:
        await event.respond('Usage: /rem user_id\nExample: /rem 123456789')
        return
    try:
        target_user_id = int(args[1])
    except ValueError:
        await event.respond(
            '❌ Invalid user ID. Please provide a valid numeric user ID.')
        return
    if not await is_premium_user(target_user_id):
        await event.respond(
            f'❌ User {target_user_id} does not have a premium subscription.')
        return
    try:
        target_name = 'Unknown'
        try:
            target_entity = await bot_client.get_entity(target_user_id)
            target_name = get_display_name(target_entity)
        except Exception as e:
            logger.warning(f'Could not get target user name: {e}')
        result = await premium_users_collection.delete_one({'user_id':
            target_user_id})
        if result.deleted_count > 0:
            await event.respond(
                f'✅ Premium subscription successfully removed from {target_name} ({target_user_id}).'
                )
            try:
                await bot_client.send_message(target_user_id,
                    '⚠️ Your premium subscription has been removed by the administrator.'
                    )
            except Exception as e:
                logger.error(
                    f'Could not notify user {target_user_id} about premium removal: {e}'
                    )
        else:
            await event.respond(
                f'❌ Failed to remove premium from user {target_user_id}.')
        return
    except Exception as e:
        logger.error(f'Error removing premium from {target_user_id}: {e}')
        await event.respond(f'❌ Error removing premium: {str(e)}')
        return

def get_readable_size(size_in_bytes):
    power = 2**10
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size_in_bytes > power and n < 4:
        size_in_bytes /= power
        n += 1
    return f"{size_in_bytes:.2f} {power_labels[n]}"

@bot_client.on(events.NewMessage(pattern='/stats'))
async def stats_handler(event):
    if not await is_private_chat(event):
        await event.respond("This command can only be used in private chats.")
        return

    user_id = event.sender_id
    is_owner = user_id in OWNER_ID
    
    # Calculate stats
    total_users = await users_collection.count_documents()
    total_premium = await premium_users_collection.count_documents()
    
    try:
        from plugins.batch import ACTIVE_USERS
        active_batches = len(ACTIVE_USERS)
    except Exception:
        active_batches = 0
    
    if is_owner:
        # System Stats
        cpu_usage = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        ram_usage = ram.percent
        ram_total = get_readable_size(ram.total)
        ram_used = get_readable_size(ram.used)
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent
        disk_total = get_readable_size(disk.total)
        disk_used = get_readable_size(disk.used)
        
        stats_text = (
            "📊 **Bot Server Statistics (Admin View)**\n\n"
            f"👥 **Total Registered Users:** {total_users}\n"
            f"⭐ **Premium Members:** {total_premium}\n"
            f"🔄 **Active Batches:** {active_batches}\n\n"
            "💻 **System Info:**\n"
            f"🖥️ **CPU Usage:** {cpu_usage}%\n"
            f"💾 **RAM Usage:** {ram_usage}% ({ram_used}/{ram_total})\n"
            f"📁 **Disk Usage:** {disk_usage}% ({disk_used}/{disk_total})\n"
        )
    else:
        stats_text = (
            "📊 **Bot Statistics**\n\n"
            f"👥 **Total Registered Users:** {total_users}\n"
            f"⭐ **Premium Members:** {total_premium}\n"
            f"🔄 **Active Batches:** {active_batches}\n\n"
            "Enjoy using the bot! Use `/status` to check your personal plan."
        )
        
    await event.respond(stats_text)

@bot_client.on(events.NewMessage(pattern='/broadcast'))
async def broadcast_handler(event):
    if not await is_private_chat(event):
        await event.respond("This command can only be used in private chats.")
        return

    user_id = event.sender_id
    if user_id not in OWNER_ID:
        await event.respond("❌ This command is restricted to the bot owner.")
        return
        
    # Get the message to broadcast
    if not event.reply_to_msg_id and len(event.text.split()) < 2:
        await event.respond("Usage: Reply to a message with `/broadcast` or use `/broadcast <text>`")
        return
        
    broadcast_msg = None
    if event.reply_to_msg_id:
        broadcast_msg = await event.get_reply_message()
    else:
        broadcast_msg = event.text.split(" ", 1)[1]
        
    status_msg = await event.respond("🔄 Broadcasting message to all users...")
    
    # Find all users
    users = await users_collection.find()
    success = 0
    failed = 0
    
    for u in users:
        uid = u.get("user_id")
        if not uid or uid == user_id:
            continue
        try:
            await bot_client.send_message(uid, broadcast_msg)
            success += 1
            await asyncio.sleep(0.3)  # Rate limit prevention
        except Exception:
            failed += 1
            
    await status_msg.edit(
        "✅ **Broadcast Completed!**\n\n"
        f"🟢 **Successful:** {success}\n"
        f"🔴 **Failed/Blocked:** {failed}\n"
        f"👥 **Total Users:** {len(users)}"
    )