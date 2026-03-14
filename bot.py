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

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(
    CHOOSING_TYPE,
    CATEGORY,
    DESCRIPTION,
    PHOTO,
    REWARD_OR_CONTACT
) = range(5)

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
    
    return await ask_reward_or_contact(update, context, photo_saved=True)


async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle skip photo."""
    context.user_data['photo_file_id'] = None
    
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
        
        # Save to LOST_ITEMS database
        item_id = database.save_lost_item(
            user_id=user_id,
            category=context.user_data.get('category', ''),
            description=context.user_data.get('description', ''),
            photo_file_id=context.user_data.get('photo_file_id'),
            reward=context.user_data.get('reward')
        )
        
        # Create summary
        summary = create_summary(context.user_data, item_type, item_id)
        
        await update.message.reply_text(
            "✅ *Your lost item has been registered!*\n\n"
            f"{summary}\n\n"
            "We hope you find your item soon! 🤞\n\n"
            "Use /start to report another item.",
            parse_mode='Markdown'
        )
    else:
        context.user_data['contact_info'] = user_input
        
        # Save to FOUND_ITEMS database
        item_id = database.save_found_item(
            user_id=user_id,
            category=context.user_data.get('category', ''),
            description=context.user_data.get('description', ''),
            photo_file_id=context.user_data.get('photo_file_id'),
            contact_info=context.user_data.get('contact_info')
        )
        
        # Create summary
        summary = create_summary(context.user_data, item_type, item_id)
        
        await update.message.reply_text(
            "✅ *Your found item has been registered!*\n\n"
            f"{summary}\n\n"
            "Thank you for helping reunite items with their owners! 🙏\n\n"
            "Use /start to report another item.",
            parse_mode='Markdown'
        )
    
    # Clear user data
    context.user_data.clear()
    
    return ConversationHandler.END


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


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
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
    await update.message.reply_text(
        "🆘 *Lost & Found Bot Help*\n\n"
        "*Commands:*\n"
        "/start - Start reporting a lost or found item\n"
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
    # Load bot token from environment variable
    TOKEN = os.getenv("BOT_TOKEN")
    
    if not TOKEN:
        raise ValueError("BOT_TOKEN not found! Please add it to your .env file")
    
    # Create the Application
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
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    
    # Run the bot
    print("🤖 Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
