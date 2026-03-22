"""
Lost and Found Telegram Bot.
Allows users to post information about items they lost or found.
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from telegram import (
    Update, 
    ReplyKeyboardMarkup, 
    ReplyKeyboardRemove,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

import database

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(
    format=LOG_FORMAT,
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def _user_tag(update: Update) -> str:
    """Build a short 'user_id @username' tag for log messages."""
    user = update.effective_user
    if not user:
        return "unknown_user"
    parts = [f"user_id={user.id}"]
    if user.username:
        parts.append(f"@{user.username}")
    return " ".join(parts)

# Conversation states
(
    CHOOSING_TYPE,
    CATEGORY,
    DESCRIPTION,
    PHOTO,
    REWARD_OR_CONTACT,
    FOUND_MATCHING,
    LOST_MATCHING,
) = range(7)

# Item categories
CATEGORIES = [
    ["🧸 Toy", "📱 Phone", "💻 Laptop/Tablet"], 
    ["👜 Bag/Bagpack", "👝 Wallet", "⌚ Watches"],
    ["🎧 Earphones/Earbuds", "📄 Document"],
    ["👕 Clothing", "💍 Jewelry", "🕶 Glasses/Sunglasses"],
    ["🔑 Keys", "🐶 Pets", "Other"]
]

# Category emoji mapping for database storage
CATEGORY_MAP = {
    "🧸 Toy": "Toy",
    "💻 Laptop/Tablet": "Laptop or Tablet",
    "📱 Phone": "Phone",
    "👜 Bag/Bagpack": "Bag or Bagpack",
    "👝 Wallet": "Wallet",
    "🔑 Keys": "Keys",
    "📄 Document": "Document",
    "👕 Clothing": "Clothing",
    "💍 Jewelry": "Jewelry",
    "⌚ Watches": "Watches",
    "🕶 Glasses/Sunglasses": "Glasses or Sunglasses",
    "🎧 Earphones/Earbuds": "Earphones or Earbuds",
    "🐶 Pets": "Pets",
    "Other": "Other"
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask if user lost or found an item."""
    logger.info("[START] %s started the bot", _user_tag(update))
    user = update.effective_user
    if user:
        database.track_user(user.id, user.username)
    keyboard = [
        [
            InlineKeyboardButton("🔍 I Lost Something", callback_data="lost"),
            InlineKeyboardButton("📦 I Found Something", callback_data="found")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 *Welcome to Lost & Found Bot!*\n\n"
        "I can help you report lost items or items you've found.\n\n"
        "Please choose an option:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return CHOOSING_TYPE


async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the lost/found selection."""
    query = update.callback_query
    await query.answer()
    
    item_type = query.data
    context.user_data['item_type'] = item_type
    context.user_data.clear()
    context.user_data['item_type'] = item_type
    
    logger.info("[CHOOSE_TYPE] %s selected '%s'", _user_tag(update), item_type)
    
    type_text = "lost" if item_type == "lost" else "found"
    
    reply_markup = ReplyKeyboardMarkup(CATEGORIES, one_time_keyboard=True, resize_keyboard=True)
    
    await query.edit_message_text(
        f"📋 You selected: *I {type_text.upper()} something*\n\n"
        f"Now, please select the category of the item you {type_text}:",
        parse_mode='Markdown'
    )
    
    await query.message.reply_text(
        "Choose a category:",
        reply_markup=reply_markup
    )
    
    return CATEGORY


async def category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store category and ask for description."""
    user_category = update.message.text
    
    # Map the emoji category to clean category name
    if user_category in CATEGORY_MAP:
        context.user_data['category'] = CATEGORY_MAP[user_category]
    else:
        context.user_data['category'] = user_category
    
    item_type = context.user_data.get('item_type', 'lost')
    logger.info("[CATEGORY] %s chose category '%s' (type=%s)", _user_tag(update), context.user_data['category'], item_type)
    
    await update.message.reply_text(
        f"📝 *Category:* {user_category}\n\n"
        f"Now, please describe the item you {item_type} in detail.\n\n"
        "*Include:*\n"
        "• Color\n"
        "• Size\n"
        "• Brand (if applicable)\n"
        "• Any specific details or marks\n\n"
        f"• Write where did you {item_type} the item if you remember\n\n"
        "_Write your description in English:_",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    return DESCRIPTION


async def description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store description and ask for photo."""
    context.user_data['description'] = update.message.text
    item_type = context.user_data.get('item_type', 'lost')
    logger.info("[DESCRIPTION] %s entered description (len=%d, type=%s)", _user_tag(update), len(update.message.text), item_type)
    
    skip_button = KeyboardButton(text="⏭️ Skip Photo")
    keyboard = [[skip_button]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        f"📸 *Photo*\n\n"
        f"Please send a photo of the {item_type} item.\n"
        "If you don't have a photo, you can skip this step.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return PHOTO




async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store photo and ask for reward/contact info."""
    photo_file = update.message.photo[-1]
    context.user_data['photo_file_id'] = photo_file.file_id
    logger.info("[PHOTO] %s uploaded photo (file_id=%s)", _user_tag(update), photo_file.file_id[:20])
    
    return await ask_reward_or_contact(update, context, photo_saved=True)


async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle skip photo."""
    context.user_data['photo_file_id'] = None
    logger.info("[PHOTO] %s skipped photo", _user_tag(update))
    
    return await ask_reward_or_contact(update, context, photo_saved=False)


async def ask_reward_or_contact(update: Update, context: ContextTypes.DEFAULT_TYPE, photo_saved: bool) -> int:
    """Ask for reward (lost items) or contact info (found items)."""
    item_type = context.user_data.get('item_type', 'lost')
    photo_text = "📸 Photo saved!" if photo_saved else "📸 Photo skipped"
    
    if item_type == "lost":
        await update.message.reply_text(
            f"{photo_text}\n\n"
            "💰 *Reward*\n\n"
            "Would you like to offer a reward for finding your item?\n\n"
            "Enter the reward amount or type 'No reward':",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"{photo_text}\n\n"
            "📞 *Contact Information*\n\n"
            "Please provide your contact information so the owner can reach you.\n\n"
            "You can share:\n"
            "• Phone number\n"
            "• Email address\n"
            "• Telegram username\n"
            "• Any other contact method",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode='Markdown'
        )
    
    return REWARD_OR_CONTACT


async def reward_or_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store reward/contact info and save to database."""
    user_input = update.message.text
    item_type = context.user_data.get('item_type', 'lost')
    user_id = update.effective_user.id
    
    if item_type == "lost":
        context.user_data['reward'] = user_input
        logger.info("[REWARD] %s set reward='%s'", _user_tag(update), user_input)
        
        try:
            item_id = database.save_lost_item(
                user_id=user_id,
                category=context.user_data.get('category', ''),
                description=context.user_data.get('description', ''),
                photo_file_id=context.user_data.get('photo_file_id'),
                reward=context.user_data.get('reward')
            )
            logger.info("[SAVE] %s saved lost item #%d (category=%s)", _user_tag(update), item_id, context.user_data.get('category'))
        except Exception:
            logger.exception("[SAVE] %s failed to save lost item", _user_tag(update))
            await update.message.reply_text("⚠️ An error occurred while saving your item. Please try again with /start.")
            context.user_data.clear()
            return ConversationHandler.END
        
        summary = create_summary(context.user_data, item_type, item_id)
        
        await update.message.reply_text(
            "✅ *Your lost item has been registered!*\n\n"
            f"{summary}\n\n"
            "We hope you find your item soon! 🤞",
            parse_mode='Markdown'
        )
        
        return await start_lost_matching(update, context, item_id)
    else:
        context.user_data['contact_info'] = user_input
        logger.info("[CONTACT] %s provided contact info", _user_tag(update))
        
        try:
            item_id = database.save_found_item(
                user_id=user_id,
                category=context.user_data.get('category', ''),
                description=context.user_data.get('description', ''),
                photo_file_id=context.user_data.get('photo_file_id'),
                contact_info=context.user_data.get('contact_info')
            )
            logger.info("[SAVE] %s saved found item #%d (category=%s)", _user_tag(update), item_id, context.user_data.get('category'))
        except Exception:
            logger.exception("[SAVE] %s failed to save found item", _user_tag(update))
            await update.message.reply_text("⚠️ An error occurred while saving your item. Please try again with /start.")
            context.user_data.clear()
            return ConversationHandler.END
        
        summary = create_summary(context.user_data, item_type, item_id)
        
        await update.message.reply_text(
            "✅ *Your found item has been registered!*\n\n"
            f"{summary}\n\n"
            "Thank you for helping reunite items with their owners! 🙏",
            parse_mode='Markdown'
        )
        
        return await start_found_matching(update, context, item_id)


def create_summary(data: dict, item_type: str, item_id: int) -> str:
    """Create a summary of the reported item."""
    summary_lines = [
        f"*Report ID:* #{item_id}",
        f"*Type:* {'Lost Item' if item_type == 'lost' else 'Found Item'}",
        f"*Category:* {data.get('category', 'N/A')}",
        f"*Description:* {data.get('description', 'N/A')[:100]}{'...' if len(data.get('description', '')) > 100 else ''}",
    ]
    
    if data.get('photo_file_id'):
        summary_lines.append("*Photo:* ✅ Attached")
    else:
        summary_lines.append("*Photo:* Not provided")
    
    if item_type == "lost":
        reward = data.get('reward', 'No reward')
        summary_lines.append(f"*Reward:* {reward}")
    else:
        contact = data.get('contact_info', 'N/A')
        summary_lines.append(f"*Contact:* {contact[:50]}{'...' if len(contact) > 50 else ''}")
    
    return "\n".join(summary_lines)


async def start_found_matching(update: Update, context: ContextTypes.DEFAULT_TYPE, found_item_id: int) -> int:
    """After a found item is saved, search for similar lost items and start the review flow."""
    found_item = database.get_found_item_by_id(found_item_id)
    similar_items = database.find_similar_lost_items(found_item)

    logger.info("[MATCH] %s starting found-matching for found_item #%d, candidates=%d",
                _user_tag(update), found_item_id, len(similar_items))

    if not similar_items:
        await update.message.reply_text(
            "🔍 No similar lost items found at the moment.\n"
            "We'll keep your report on file.\n\n"
            "Use /start to report another item."
        )
        context.user_data.clear()
        return ConversationHandler.END

    context.user_data['matching_items'] = similar_items
    context.user_data['matching_index'] = 0
    context.user_data['found_item_id'] = found_item_id

    await update.message.reply_text("🔍 We found some lost items that might match yours. Let's check...")

    return await show_next_match(update, context)


async def show_next_match(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the next similar lost item to the finder for review."""
    items = context.user_data.get('matching_items', [])
    index = context.user_data.get('matching_index', 0)

    if index >= len(items):
        target = update.callback_query.message if update.callback_query else update.message
        await target.reply_text(
            "📭 No more similar items to show.\n"
            "We'll keep your report on file.\n\n"
            "Use /start to report another item."
        )
        context.user_data.clear()
        return ConversationHandler.END

    lost_item = items[index]
    lost_item_id = lost_item['id']

    keyboard = [[
        InlineKeyboardButton("✅ Yes", callback_data=f"finder_yes_{lost_item_id}"),
        InlineKeyboardButton("❌ No", callback_data=f"finder_no_{lost_item_id}"),
        InlineKeyboardButton("🤔 Not sure", callback_data=f"finder_unsure_{lost_item_id}"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"🔍 *Possible match ({index + 1}/{len(items)})*\n\n"
        f"*Category:* {lost_item.get('category', 'N/A')}\n"
        f"*Description:* {lost_item.get('description', 'N/A')}\n"
        f"*Reward:* {lost_item.get('reward', 'No reward')}\n\n"
        "Is this the item you found?"
    )

    target = update.callback_query.message if update.callback_query else update.message

    photo_id = lost_item.get('photo_file_id', '')
    if photo_id:
        await target.reply_photo(
            photo=photo_id,
            caption=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await target.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    return FOUND_MATCHING


async def handle_finder_match_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the finder's Yes / No / Not sure response to a potential match."""
    query = update.callback_query
    await query.answer()

    data = query.data
    found_item_id = context.user_data.get('found_item_id')
    lost_item_id = int(data.rsplit("_", 1)[-1])

    logger.info("[FINDER_RESPONSE] %s responded '%s' (found #%s -> lost #%d)",
                _user_tag(update), data.split("_")[1], found_item_id, lost_item_id)

    await query.edit_message_reply_markup(reply_markup=None)

    if data.startswith("finder_no_"):
        context.user_data['matching_index'] = context.user_data.get('matching_index', 0) + 1
        return await show_next_match(update, context)

    if data.startswith("finder_unsure_"):
        await notify_lost_item_owner(context, found_item_id, lost_item_id)
        await query.message.reply_text("📩 We've notified the person who lost a similar item.")
        context.user_data['matching_index'] = context.user_data.get('matching_index', 0) + 1
        return await show_next_match(update, context)

    if data.startswith("finder_yes_"):
        database.update_found_item_match(found_item_id, lost_item_id)
        logger.info("[MATCH_CONFIRMED] finder confirmed: found #%s matches lost #%d", found_item_id, lost_item_id)
        await notify_lost_item_owner(context, found_item_id, lost_item_id)
        await query.message.reply_text(
            "✅ *Great!* We've notified the person who lost this item.\n\n"
            "Thank you for helping! 🙏\n"
            "Use /start to report another item.",
            parse_mode='Markdown'
        )
        context.user_data.clear()
        return ConversationHandler.END

    return FOUND_MATCHING


async def notify_lost_item_owner(context: ContextTypes.DEFAULT_TYPE, found_item_id: int, lost_item_id: int):
    """Send the found item info (without finder's contacts) to the lost item owner."""
    found_item = database.get_found_item_by_id(found_item_id)
    lost_item = database.get_lost_item_by_id(lost_item_id)

    if not found_item or not lost_item:
        logger.warning("[NOTIFY] cannot notify owner: found_item #%s or lost_item #%s not found in DB",
                       found_item_id, lost_item_id)
        return

    owner_user_id = int(lost_item['user_id'])
    logger.info("[NOTIFY] sending match notification to lost-item owner user_id=%d (found #%s -> lost #%s)",
                owner_user_id, found_item_id, lost_item_id)

    keyboard = [[
        InlineKeyboardButton("✅ Yes", callback_data=f"owner_yes_F{found_item_id}_L{lost_item_id}"),
        InlineKeyboardButton("❌ No", callback_data=f"owner_no_F{found_item_id}_L{lost_item_id}"),
        InlineKeyboardButton("🤔 Not sure", callback_data=f"owner_unsure_F{found_item_id}_L{lost_item_id}"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "🔔 *Someone may have found your item!*\n\n"
        f"*Your lost item:* {lost_item.get('description', 'N/A')}\n\n"
        "*Found item details:*\n"
        f"*Category:* {found_item.get('category', 'N/A')}\n"
        f"*Description:* {found_item.get('description', 'N/A')}\n\n"
        "Is this your item?"
    )

    photo_id = found_item.get('photo_file_id', '')
    try:
        if photo_id:
            await context.bot.send_photo(
                chat_id=owner_user_id,
                photo=photo_id,
                caption=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_message(
                chat_id=owner_user_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error("Failed to notify owner %s: %s", owner_user_id, e)


async def handle_owner_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the lost item owner's Yes / No / Not sure response (standalone callback)."""
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split("_")
    action = parts[1]
    found_item_id = int(parts[2][1:])
    lost_item_id = int(parts[3][1:])

    logger.info("[OWNER_RESPONSE] %s responded '%s' (lost #%d, found #%d)",
                _user_tag(update), action, lost_item_id, found_item_id)

    found_item = database.get_found_item_by_id(found_item_id)
    if not found_item:
        logger.warning("[OWNER_RESPONSE] found item #%d no longer exists", found_item_id)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("⚠️ Sorry, this item is no longer available.")
        return

    contact_info = found_item.get('contact_info', 'N/A')

    await query.edit_message_reply_markup(reply_markup=None)

    if action == "no":
        await query.message.reply_text(
            "OK, thanks for checking! We'll keep looking. 🔍"
        )

    elif action == "unsure":
        await query.message.reply_text(
            "📞 *Here is the contact info of the person who found a similar item:*\n\n"
            f"{contact_info}\n\n"
            "You can reach out to them to verify.",
            parse_mode='Markdown'
        )

    elif action == "yes":
        database.update_lost_item_match(lost_item_id, found_item_id)
        logger.info("[MATCH_CONFIRMED] owner confirmed: lost #%d matches found #%d", lost_item_id, found_item_id)
        await query.message.reply_text(
            "🎉 *Great news!* We're glad you found your item!\n\n"
            "📞 *Contact information:*\n\n"
            f"{contact_info}\n\n"
            "Please reach out to them to arrange pickup.",
            parse_mode='Markdown'
        )


async def start_lost_matching(update: Update, context: ContextTypes.DEFAULT_TYPE, lost_item_id: int) -> int:
    """After a lost item is saved, search for similar found items and start the review flow."""
    lost_item = database.get_lost_item_by_id(lost_item_id)
    similar_items = database.find_similar_found_items(lost_item)

    logger.info("[MATCH] %s starting lost-matching for lost_item #%d, candidates=%d",
                _user_tag(update), lost_item_id, len(similar_items))

    if not similar_items:
        await update.message.reply_text(
            "🔍 No similar found items at the moment.\n"
            "We'll keep your report on file.\n\n"
            "Use /start to report another item."
        )
        context.user_data.clear()
        return ConversationHandler.END

    context.user_data['matching_found_items'] = similar_items
    context.user_data['matching_found_index'] = 0
    context.user_data['lost_item_id'] = lost_item_id

    await update.message.reply_text("🔍 We found some items that might be yours. Let's check...")

    return await show_next_lost_match(update, context)


async def show_next_lost_match(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the next similar found item to the loser for review."""
    items = context.user_data.get('matching_found_items', [])
    index = context.user_data.get('matching_found_index', 0)

    if index >= len(items):
        target = update.callback_query.message if update.callback_query else update.message
        await target.reply_text(
            "📭 No more similar items to show.\n"
            "We'll keep your report on file.\n\n"
            "Use /start to report another item."
        )
        context.user_data.clear()
        return ConversationHandler.END

    found_item = items[index]
    found_item_id = found_item['id']

    keyboard = [[
        InlineKeyboardButton("✅ Yes", callback_data=f"loser_yes_{found_item_id}"),
        InlineKeyboardButton("❌ No", callback_data=f"loser_no_{found_item_id}"),
        InlineKeyboardButton("🤔 Not sure", callback_data=f"loser_unsure_{found_item_id}"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"🔍 *Possible match ({index + 1}/{len(items)})*\n\n"
        f"*Category:* {found_item.get('category', 'N/A')}\n"
        f"*Description:* {found_item.get('description', 'N/A')}\n\n"
        "Is this the item you lost?"
    )

    target = update.callback_query.message if update.callback_query else update.message

    photo_id = found_item.get('photo_file_id', '')
    if photo_id:
        await target.reply_photo(
            photo=photo_id,
            caption=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await target.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    return LOST_MATCHING


async def handle_loser_match_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the loser's Yes / No / Not sure response to a potential found-item match."""
    query = update.callback_query
    await query.answer()

    data = query.data
    lost_item_id = context.user_data.get('lost_item_id')
    found_item_id = int(data.rsplit("_", 1)[-1])

    logger.info("[LOSER_RESPONSE] %s responded '%s' (lost #%s -> found #%d)",
                _user_tag(update), data.split("_")[1], lost_item_id, found_item_id)

    await query.edit_message_reply_markup(reply_markup=None)

    if data.startswith("loser_no_"):
        context.user_data['matching_found_index'] = context.user_data.get('matching_found_index', 0) + 1
        return await show_next_lost_match(update, context)

    if data.startswith("loser_unsure_"):
        await notify_found_item_owner(context, lost_item_id, found_item_id)
        await query.message.reply_text("📩 We've notified the person who found a similar item.")
        context.user_data['matching_found_index'] = context.user_data.get('matching_found_index', 0) + 1
        return await show_next_lost_match(update, context)

    if data.startswith("loser_yes_"):
        database.update_lost_item_match(lost_item_id, found_item_id)
        logger.info("[MATCH_CONFIRMED] loser confirmed: lost #%s matches found #%d", lost_item_id, found_item_id)
        await notify_found_item_owner(context, lost_item_id, found_item_id)
        await query.message.reply_text(
            "✅ *Great!* We've notified the person who found this item.\n\n"
            "We hope you get your item back soon! 🤞\n"
            "Use /start to report another item.",
            parse_mode='Markdown'
        )
        context.user_data.clear()
        return ConversationHandler.END

    return LOST_MATCHING


async def notify_found_item_owner(context: ContextTypes.DEFAULT_TYPE, lost_item_id: int, found_item_id: int):
    """Send the lost item info (without loser's contacts) to the found item owner (finder)."""
    lost_item = database.get_lost_item_by_id(lost_item_id)
    found_item = database.get_found_item_by_id(found_item_id)

    if not lost_item or not found_item:
        logger.warning("[NOTIFY] cannot notify finder: lost_item #%s or found_item #%s not found in DB",
                       lost_item_id, found_item_id)
        return

    finder_user_id = int(found_item['user_id'])
    logger.info("[NOTIFY] sending match notification to finder user_id=%d (lost #%s -> found #%s)",
                finder_user_id, lost_item_id, found_item_id)

    keyboard = [[
        InlineKeyboardButton("✅ Yes", callback_data=f"fowner_yes_L{lost_item_id}_F{found_item_id}"),
        InlineKeyboardButton("❌ No", callback_data=f"fowner_no_L{lost_item_id}_F{found_item_id}"),
        InlineKeyboardButton("🤔 Not sure", callback_data=f"fowner_unsure_L{lost_item_id}_F{found_item_id}"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "🔔 *Someone may have lost the item you found!*\n\n"
        f"*Your found item:* {found_item.get('description', 'N/A')}\n\n"
        "*Lost item details:*\n"
        f"*Category:* {lost_item.get('category', 'N/A')}\n"
        f"*Description:* {lost_item.get('description', 'N/A')}\n\n"
        "Is this the same item?"
    )

    photo_id = lost_item.get('photo_file_id', '')
    try:
        if photo_id:
            await context.bot.send_photo(
                chat_id=finder_user_id,
                photo=photo_id,
                caption=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_message(
                chat_id=finder_user_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error("Failed to notify finder %s: %s", finder_user_id, e)


async def handle_found_owner_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the found item owner's Yes / No / Not sure response (standalone callback)."""
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split("_")
    action = parts[1]
    lost_item_id = int(parts[2][1:])
    found_item_id = int(parts[3][1:])

    logger.info("[FOWNER_RESPONSE] %s responded '%s' (lost #%d, found #%d)",
                _user_tag(update), action, lost_item_id, found_item_id)

    lost_item = database.get_lost_item_by_id(lost_item_id)
    found_item = database.get_found_item_by_id(found_item_id)

    if not lost_item or not found_item:
        logger.warning("[FOWNER_RESPONSE] items not found in DB (lost #%d / found #%d)", lost_item_id, found_item_id)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("⚠️ Sorry, this item is no longer available.")
        return

    loser_user_id = int(lost_item['user_id'])
    contact_info = found_item.get('contact_info', 'N/A')

    await query.edit_message_reply_markup(reply_markup=None)

    if action == "no":
        await query.message.reply_text(
            "OK, thanks for checking! 🔍"
        )

    elif action == "unsure":
        try:
            await context.bot.send_message(
                chat_id=loser_user_id,
                text=(
                    "📞 *The person who found a similar item shared their contact:*\n\n"
                    f"{contact_info}\n\n"
                    "You can reach out to them to verify."
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error("Failed to send contact to loser %s: %s", loser_user_id, e)
        await query.message.reply_text(
            "📩 We've shared your contact information with the person who lost a similar item."
        )

    elif action == "yes":
        database.update_found_item_match(found_item_id, lost_item_id)
        logger.info("[MATCH_CONFIRMED] finder-owner confirmed: found #%d matches lost #%d", found_item_id, lost_item_id)
        try:
            await context.bot.send_message(
                chat_id=loser_user_id,
                text=(
                    "🎉 *Great news!* The person who found your item confirmed it's yours!\n\n"
                    "📞 *Contact information:*\n\n"
                    f"{contact_info}\n\n"
                    "Please reach out to them to arrange pickup."
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error("Failed to send contact to loser %s: %s", loser_user_id, e)
        await query.message.reply_text(
            "📩 We've shared your contact information with the person who lost this item. Thank you! 🙏"
        )


async def show_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the user's reported items one by one with delete/keep options."""
    user_id = update.effective_user.id
    logger.info("[SHOW] %s requested their item list", _user_tag(update))

    lost = database.get_user_lost_items(user_id)
    found = database.get_user_found_items(user_id)

    items = [("lost", i) for i in lost] + [("found", i) for i in found]

    if not items:
        await update.message.reply_text("📭 You don't have any reported items.")
        return

    context.user_data['_show_items'] = items
    context.user_data['_show_index'] = 0

    await _show_next_user_item(update.message, context)


async def _show_next_user_item(target, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the next item from the user's show-list."""
    items = context.user_data.get('_show_items', [])
    index = context.user_data.get('_show_index', 0)

    if index >= len(items):
        await target.reply_text(
            "📋 That's all your items!\n"
            "Use /start to report a new item."
        )
        context.user_data.pop('_show_items', None)
        context.user_data.pop('_show_index', None)
        return

    item_type, item = items[index]
    item_id = item['id']

    type_label = "🔍 Lost" if item_type == "lost" else "📦 Found"
    matched = item.get('is_matched', 'false')
    status = "✅ Matched" if matched != "false" else "🔎 Searching"

    text = (
        f"*{type_label} Item* ({index + 1}/{len(items)})\n\n"
        f"*ID:* #{item_id}\n"
        f"*Category:* {item.get('category', 'N/A')}\n"
        f"*Description:* {item.get('description', 'N/A')}\n"
        f"*Status:* {status}\n"
        f"*Date:* {item.get('created_at', 'N/A')[:10]}"
    )

    if item_type == "lost" and item.get('reward'):
        text += f"\n*Reward:* {item['reward']}"

    keyboard = [[
        InlineKeyboardButton("🗑 Delete", callback_data=f"show_del_{item_type}_{item_id}"),
        InlineKeyboardButton("➡️ Keep", callback_data=f"show_keep_{item_type}_{item_id}"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    photo_id = item.get('photo_file_id', '')
    if photo_id:
        await target.reply_photo(
            photo=photo_id,
            caption=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await target.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')


async def handle_show_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle delete/keep response for the /show flow."""
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split("_")
    action = parts[1]
    item_type = parts[2]
    item_id = int(parts[3])

    logger.info("[SHOW] %s action='%s' on %s item #%d",
                _user_tag(update), action, item_type, item_id)

    await query.edit_message_reply_markup(reply_markup=None)

    if action == "del":
        if item_type == "lost":
            ok = database.archive_lost_item(item_id)
        else:
            ok = database.archive_found_item(item_id)

        if ok:
            await query.message.reply_text(f"🗑 Item #{item_id} has been deleted and archived.")
        else:
            await query.message.reply_text(f"⚠️ Could not delete item #{item_id}.")

    context.user_data['_show_index'] = context.user_data.get('_show_index', 0) + 1
    await _show_next_user_item(query.message, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    logger.info("[CANCEL] %s cancelled the conversation", _user_tag(update))
    await update.message.reply_text(
        "❌ *Cancelled*\n\n"
        "Your report has been cancelled.\n"
        "Use /start to begin a new report.",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    context.user_data.clear()
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message."""
    logger.info("[HELP] %s requested help", _user_tag(update))
    await update.message.reply_text(
        "🆘 *Lost & Found Bot Help*\n\n"
        "*Commands:*\n"
        "/start - Start reporting a lost or found item\n"
        "/show - View and manage your reported items\n"
        "/cancel - Cancel current report\n"
        "/help - Show this help message\n\n"
        "*How it works:*\n"
        "1. Choose if you lost or found an item\n"
        "2. Select the category\n"
        "3. Describe the item in detail\n"
        "4. Add a photo (optional)\n"
        "5. For lost items: set a reward\n"
        "   For found items: provide contact info\n\n"
        "Your report will be saved!",
        parse_mode='Markdown'
    )


def main() -> None:
    """Run the bot."""
    TOKEN = os.getenv("BOT_TOKEN")
    
    if not TOKEN:
        logger.critical("BOT_TOKEN not found in environment variables")
        raise ValueError("BOT_TOKEN not found! Please add it to your .env file")
    
    logger.info("[STARTUP] Initializing bot application...")
    application = Application.builder().token(TOKEN).build()
    
    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_TYPE: [
                CallbackQueryHandler(choose_type, pattern="^(lost|found)$")
            ],
            CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, category)
            ],
            DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, description)
            ],
            PHOTO: [
                MessageHandler(filters.PHOTO, photo),
                MessageHandler(filters.Regex("^⏭️ Skip Photo$"), skip_photo)
            ],
            REWARD_OR_CONTACT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, reward_or_contact)
            ],
            FOUND_MATCHING: [
                CallbackQueryHandler(handle_finder_match_response, pattern="^finder_(yes|no|unsure)_")
            ],
            LOST_MATCHING: [
                CallbackQueryHandler(handle_loser_match_response, pattern="^loser_(yes|no|unsure)_")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("show", show_command))
    application.add_handler(
        CallbackQueryHandler(handle_owner_response, pattern="^owner_(yes|no|unsure)_"),
        group=1
    )
    application.add_handler(
        CallbackQueryHandler(handle_found_owner_response, pattern="^fowner_(yes|no|unsure)_"),
        group=1
    )
    application.add_handler(
        CallbackQueryHandler(handle_show_response, pattern="^show_(del|keep)_"),
        group=1
    )
    
    logger.info("[STARTUP] Bot is starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
