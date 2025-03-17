#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ZXI: The Lore-Driven Telegram Companion for the World of Fangen
Main entry point for the Telegram bot
"""

import logging
import os
import sys
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN, ADMIN_IDS, LOG_LEVEL
from utils.logger import setup_logger
from utils.database import Database
from utils.fangen_lore_manager import FangenLoreManager
from utils.quest_manager import QuestManager
from handlers.lore_handlers import LoreCommandHandlers
from handlers.quest_handlers import QuestCommandHandlers

# Set up logging
logger = setup_logger(__name__, LOG_LEVEL)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued.
    
    Welcomes the user to the bot, registers them in the database if they're new,
    and presents the main menu options.
    
    Args:
        update: The update containing the command
        context: The context object for the bot
    """
    user = update.effective_user
    logger.info(f"User {user.id} started the bot")
    
    # Register user in database if not exists
    db = context.bot_data['db']
    db.execute_query(
        "INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
        (user.id, user.username, user.first_name, user.last_name)
    )
    
    # Update last active timestamp
    db.execute_query(
        "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
        (user.id,)
    )
    
    # Create main menu
    keyboard = [
        [InlineKeyboardButton("📜 Quests", callback_data="quests_menu")],
        [InlineKeyboardButton("👥 Characters", callback_data="characters_menu")],
        [InlineKeyboardButton("🎒 Inventory", callback_data="inventory_menu")],
        [InlineKeyboardButton("📚 Lore", callback_data="lore_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Welcome to the world of Fangen, {user.mention_html()}! I am ZXI, your guide to this mystical realm.\n\n"
        f"In a world where elemental forces are living essences interwoven with destiny, you'll discover ancient empires, "
        f"legendary beings, and the continuous struggle between order and chaos.\n\n"
        f"What would you like to explore today?",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued.
    
    Provides the user with a comprehensive list of available commands
    and their descriptions.
    
    Args:
        update: The update containing the command
        context: The context object for the bot
    """
    user = update.effective_user
    logger.info(f"User {user.id} requested help")
    
    help_text = (
        "🌟 *ZXI: Your Guide to the World of Fangen* 🌟\n\n"
        "Here are the commands you can use:\n\n"
        "📜 *Quest Commands*\n"
        "/quests - Browse available quests\n"
        "/startquest [name] - Begin a specific quest\n"
        "/currentquest - View your active quest\n"
        "/abandonquest - Abandon your current quest\n\n"
        
        "👥 *Character Interactions*\n"
        "/interact - Speak with characters from Fangen\n"
        "/interact [name] - Speak with a specific character\n\n"
        
        "🎒 *Inventory & Crafting*\n"
        "/inventory - View your collected items\n"
        "/craft - View available crafting recipes\n"
        "/craft [item] - Craft a specific item\n\n"
        
        "📚 *Lore Exploration*\n"
        "/lore - Browse the world's lore by category\n"
        "/search [query] - Search for specific lore entries\n"
        "/discover - Find something new in the world\n\n"
        
        "📊 *User Features*\n"
        "/status - Check your exploration progress\n"
        "/collection - View lore entries you've discovered\n"
        "/settings - Adjust your preferences"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user messages.
    
    Processes incoming user messages, checking if they're for character interaction
    or lore queries. Provides helpful responses based on message content.
    
    Args:
        update: The update containing the message
        context: The context object for the bot
    """
    # First check if message is for character interaction
    quest_handlers = context.bot_data['quest_handlers']
    character_handled = await quest_handlers.handle_character_message(update, context)
    
    if character_handled:
        return
    
    # Otherwise treat as a general message/lore query
    user_id = update.effective_user.id
    message = update.message.text
    
    # Get lore manager
    lore_manager = context.bot_data['lore_manager']
    
    # Try to interpret as a lore query
    search_results = lore_manager.search_lore(message)
    
    if search_results:
        # Found something related in the lore
        total_results = sum(len(entries) for entries in search_results.values())
        
        if total_results == 1:
            # If only one result, show it directly
            for category, entries in search_results.items():
                if entries:
                    entry_name = entries[0]
                    entry_content = lore_manager.get_entry_content(entry_name)
                    
                    if isinstance(entry_content, dict):
                        # Format based on content type
                        content_text = ""
                        for key, value in entry_content.items():
                            if key not in ["name", "rarity"]:
                                content_text += f"*{key.capitalize()}*: {value}\n\n"
                    else:
                        content_text = entry_content
                    
                    keyboard = [[InlineKeyboardButton(
                        "« Back to Lore",
                        callback_data="lore_back"
                    )]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    # Log the successful lore retrieval
                    logger.info(f"User {user_id} retrieved lore entry: {entry_name}")
                    
                    await update.message.reply_text(
                        f"I found this in the lore:\n\n*{entry_name}*\n\n{content_text}",
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                    return
        
        # Create response for multiple results
        response = f"I found {total_results} entries related to '{message}' in the lore. You can view them with:\n\n/search {message}"
        # Log multiple results found
        logger.info(f"User {user_id} found {total_results} lore entries for query: {message}")
        await update.message.reply_text(response, parse_mode='Markdown')
    else:
        # No direct lore matches, give a helpful response
        suggestions = [
            "Try using /lore to browse all categories.",
            "Use /search followed by keywords to find specific lore.",
            "Try /discover to find something new!",
            "Use /interact to speak with characters from the world.",
            "Check your progress with /status.",
            "View your collection with /collection.",
            "Adjust your settings with /settings."
        ]
        
        import random
        # Log failed query attempt
        logger.info(f"User {user_id} query not matched: {message}")
        await update.message.reply_text(
            f"I'm not sure how to respond to that. {random.choice(suggestions)}\n\n"
            f"Use /help to see all available commands.",
            parse_mode='Markdown'
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboards.
    
    Processes callback data from inline keyboards and routes to appropriate handlers
    based on the callback prefix.
    
    Args:
        update: The update containing the callback query
        context: The context object for the bot
    """
    query = update.callback_query
    
    # Get handlers
    quest_handlers = context.bot_data['quest_handlers']
    lore_handlers = context.bot_data['lore_handlers']
    
    # Check prefix to determine correct handler
    if query.data.startswith(("quest_", "craft_", "inventory_", "item_", "interact_", "end_interaction_")):
        await quest_handlers.handle_callback(update, context)
    elif query.data.startswith(("lore_", "search_", "collection_", "discover_")):
        await lore_handlers.handle_callback(update, context)
    elif query.data == "main_menu":
        # Recreate main menu
        keyboard = [
            [InlineKeyboardButton("📜 Quests", callback_data="quests_menu")],
            [InlineKeyboardButton("👥 Characters", callback_data="characters_menu")],
            [InlineKeyboardButton("🎒 Inventory", callback_data="inventory_menu")],
            [InlineKeyboardButton("📚 Lore", callback_data="lore_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"Welcome to the world of Fangen! I am ZXI, your guide through this mystical realm.\n\n"
            f"What would you like to explore today?",
            reply_markup=reply_markup
        )
    elif query.data == "quests_menu":
        await quest_handlers.quests_command(update, context)
    elif query.data == "characters_menu":
        await quest_handlers.interact_command(update, context)
    elif query.data == "inventory_menu":
        await quest_handlers.inventory_command(update, context)
    elif query.data == "lore_menu":
        await lore_handlers.lore_command(update, context)
    else:
        await query.answer("Unknown callback data")

async def post_init(application: Application) -> None:
    """Post-initialization callback for Application."""
    logger.info("Bot initialized successfully!")
    await application.bot.set_my_commands([
        ('start', 'Start the bot'),
        ('help', 'Get help'),
        ('lore', 'Explore the lore'),
        ('quests', 'Browse available quests'),
        ('interact', 'Speak with characters'),
        ('inventory', 'View your inventory'),
        ('discover', 'Discover new lore')
    ])

def main() -> None:
    """Start the bot."""
    try:
        # Initialize components
        db = Database()
        db.setup()
        
        lore_manager = FangenLoreManager()
        quest_manager = QuestManager(db, lore_manager)
        
        # Initialize handlers
        lore_handlers = LoreCommandHandlers(lore_manager, db)
        quest_handlers = QuestCommandHandlers(lore_manager, db, quest_manager)
        
        # Create the Application instance with explicit post_init parameter
        application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
        
        # Store shared components in bot_data
        application.bot_data['db'] = db
        application.bot_data['lore_manager'] = lore_manager
        application.bot_data['quest_manager'] = quest_manager
        application.bot_data['lore_handlers'] = lore_handlers
        application.bot_data['quest_handlers'] = quest_handlers
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        
        # Lore commands
        application.add_handler(CommandHandler("lore", lore_handlers.lore_command))
        application.add_handler(CommandHandler("search", lore_handlers.search_command))
        application.add_handler(CommandHandler("discover", lore_handlers.discover_command))
        application.add_handler(CommandHandler("status", lore_handlers.status_command))
        application.add_handler(CommandHandler("collection", lore_handlers.collection_command))
        application.add_handler(CommandHandler("settings", lore_handlers.settings_command))
        
        # Quest commands
        application.add_handler(CommandHandler("quests", quest_handlers.quests_command))
        application.add_handler(CommandHandler("startquest", quest_handlers.start_quest_command))
        application.add_handler(CommandHandler("currentquest", quest_handlers.current_quest_command))
        application.add_handler(CommandHandler("abandonquest", quest_handlers.abandon_quest_command))
        application.add_handler(CommandHandler("inventory", quest_handlers.inventory_command))
        application.add_handler(CommandHandler("craft", quest_handlers.craft_command))
        application.add_handler(CommandHandler("interact", quest_handlers.interact_command))
        
        # Add callback query handler
        application.add_handler(CallbackQueryHandler(handle_callback))
        
        # Add message handler
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Log startup
        logger.info("Bot started at %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Run the bot with explicit parameters to avoid compatibility issues
        application.run_polling(
            drop_pending_updates=True, 
            poll_interval=1.0,
            allowed_updates=Update.ALL_TYPES
        )
    
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()