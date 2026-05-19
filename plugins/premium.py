# Copyright (c) 2025 Gagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

from shared_client import client as bot_client, app
from telethon import events
from datetime import timedelta
import string
import random
from config import OWNER_ID
from utils.func import add_premium_user, is_private_chat, codedb
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton as IK, InlineKeyboardMarkup as IKM
from config import OWNER_ID, JOIN_LINK as JL , ADMIN_CONTACT as AC
import base64 as spy
from utils.func import a1, a2, a3, a4, a5, a7, a8, a9, a10, a11
from plugins.start import subscribe


@bot_client.on(events.NewMessage(pattern='/add'))
async def add_premium_handler(event):
    if not await is_private_chat(event):
        await event.respond(
            'This command can only be used in private chats for security reasons.'
            )
        return
    """Handle /add command to add premium users (owner only)"""
    user_id = event.sender_id
    if user_id not in OWNER_ID:
        await event.respond('This command is restricted to the bot owner.')
        return
    text = event.message.text.strip()
    parts = text.split(' ')
    if len(parts) != 4:
        await event.respond(
            """Invalid format. Use: /add user_id duration_value duration_unit
Example: /add 123456 1 week"""
            )
        return
    try:
        target_user_id = int(parts[1])
        duration_value = int(parts[2])
        duration_unit = parts[3].lower()
        valid_units = ['min', 'hours', 'days', 'weeks', 'month', 'year',
            'decades']
        if duration_unit not in valid_units:
            await event.respond(
                f"Invalid duration unit. Choose from: {', '.join(valid_units)}"
                )
            return
        success, result = await add_premium_user(target_user_id,
            duration_value, duration_unit)
        if success:
            expiry_utc = result
            expiry_ist = expiry_utc + timedelta(hours=5, minutes=30)
            formatted_expiry = expiry_ist.strftime('%d-%b-%Y %I:%M:%S %p')
            await event.respond(
                f"""✅ User {target_user_id} added as premium member
Subscription valid until: {formatted_expiry} (IST)"""
                )
            await bot_client.send_message(target_user_id,
                f"""✅ Your have been added as premium member
**Validity upto**: {formatted_expiry} (IST)"""
                )
        else:
            await event.respond(f'❌ Failed to add premium user: {result}')
    except ValueError:
        await event.respond(
            'Invalid user ID or duration value. Both must be integers.')
    except Exception as e:
        await event.respond(f'Error: {str(e)}')
        
        
attr1 = spy.b64encode("photo".encode()).decode()
attr2 = spy.b64encode("file_id".encode()).decode()

@app.on_message(filters.command(spy.b64decode(a5.encode()).decode()))
async def start_handler(client, message):
    subscription_status = await subscribe(client, message)
    if subscription_status == 1:
        return

    b1 = spy.b64decode(a1).decode()
    b2 = int(spy.b64decode(a2).decode())
    b3 = spy.b64decode(a3).decode()
    b4 = spy.b64decode(a4).decode()
    b6 = spy.b64decode(a7).decode()
    b7 = spy.b64decode(a8).decode()
    b8 = spy.b64decode(a9).decode()
    b9 = spy.b64decode(a10).decode()
    b10 = spy.b64decode(a11).decode()

    tm = await getattr(app, b3)(b1, b2)

    pb = getattr(tm, spy.b64decode(attr1.encode()).decode())
    fd = getattr(pb, spy.b64decode(attr2.encode()).decode())

    kb = IKM([
        [IK(b7, url=JL)],
        [IK(b8, url=AC)]
    ])

    await getattr(message, b4)(
        fd,
        caption=b6,
        reply_markup=kb
    )

def generate_random_code(length=12):
    chars = string.ascii_uppercase + string.digits
    return "SPY-" + "".join(random.choice(chars) for _ in range(length))

@bot_client.on(events.NewMessage(pattern='/gencode'))
async def gencode_handler(event):
    if not await is_private_chat(event):
        await event.respond("This command can only be used in private chats.")
        return
        
    user_id = event.sender_id
    if user_id not in OWNER_ID:
        await event.respond("❌ This command is restricted to the bot owner.")
        return
        
    text = event.message.text.strip()
    parts = text.split(' ')
    if len(parts) != 3:
        await event.respond(
            "Invalid format. Use: `/gencode value unit`\n"
            "Example: `/gencode 30 days` or `/gencode 1 weeks` or `/gencode 1 month`"
        )
        return
        
    try:
        duration_value = int(parts[1])
        duration_unit = parts[2].lower()
        valid_units = ['min', 'hours', 'days', 'weeks', 'month', 'year']
        if duration_unit not in valid_units:
            await event.respond(f"Invalid duration unit. Choose from: {', '.join(valid_units)}")
            return
            
        code = generate_random_code()
        
        await codedb.update_one(
            {"user_id": code},
            {"$set": {
                "code": code,
                "duration_value": duration_value,
                "duration_unit": duration_unit,
                "used": False
            }},
            upsert=True
        )
        
        await event.respond(
            f"✅ **Promo Code Generated!**\n\n"
            f"🔑 **Code:** `{code}`\n"
            f"📅 **Duration:** {duration_value} {duration_unit}\n\n"
            f"Send this code to a user. They can redeem it using `/redeem <code>`."
        )
        
    except ValueError:
        await event.respond("Invalid duration value. It must be an integer.")
    except Exception as e:
        await event.respond(f"Error: {e}")

@bot_client.on(events.NewMessage(pattern='/redeem'))
async def redeem_handler(event):
    if not await is_private_chat(event):
        await event.respond("This command can only be used in private chats.")
        return
        
    user_id = event.sender_id
    text = event.message.text.strip()
    parts = text.split(' ')
    if len(parts) != 2:
        await event.respond("Usage: `/redeem CODE` or `/redeem SPY-XXXX`")
        return
        
    code_to_redeem = parts[1].strip()
    
    try:
        code_data = await codedb.find_one({"user_id": code_to_redeem})
        
        if not code_data or code_data.get("used", False):
            await event.respond("❌ Invalid or already used promo code.")
            return
            
        duration_value = code_data["duration_value"]
        duration_unit = code_data["duration_unit"]
        
        await codedb.update_one(
            {"user_id": code_to_redeem},
            {"$set": {"used": True}}
        )
        
        success, result = await add_premium_user(user_id, duration_value, duration_unit)
        if success:
            expiry_utc = result
            expiry_ist = expiry_utc + timedelta(hours=5, minutes=30)
            formatted_expiry = expiry_ist.strftime('%d-%b-%Y %I:%M:%S %p')
            
            await event.respond(
                f"🎉 **Premium Activated!**\n\n"
                f"✅ Code `{code_to_redeem}` redeemed successfully.\n"
                f"💎 Subscription valid until: **{formatted_expiry}** (IST)"
            )
            
            for owner in OWNER_ID:
                try:
                    await bot_client.send_message(owner, f"🔔 User {user_id} redeemed code `{code_to_redeem}` for {duration_value} {duration_unit} premium.")
                except Exception:
                    pass
        else:
            await codedb.update_one(
                {"user_id": code_to_redeem},
                {"$set": {"used": False}}
            )
            await event.respond(f"❌ Failed to activate premium: {result}")
            
    except Exception as e:
        await event.respond(f"Error: {e}")