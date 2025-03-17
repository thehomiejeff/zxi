#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Command handlers for lore-related features
"""

import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.logger import get_logger
from utils.fangen_lore_manager import FangenLoreManager
from utils.database import Database
from config import BOT_NAME, MAX_SEARCH_RESULTS

logger = get_logger(__name__)

class LoreCommandHandlers:
    """Command handlers for lore-related features."""
    
    def __init__(self, lore_manager: FangenLoreManager, db: Database):
        """Initialize lore command handlers."""
        self.lore_manager = lore_manager
        self.db = db
    
    async def lore_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /lore command to browse lore by category."""
        user_id = update.effective_user.id
        
        # Log user action
        self.db.execute_query(
            "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_id,)
        )
        
        # Get available categories
        categories = self.lore_manager.get_categories()
        
        # Create keyboard with categories
        keyboard = []
        for i in range(0, len(categories), 2):
            row = []
            row.append(InlineKeyboardButton(
                categories[i].capitalize(), 
                callback_data=f"lore_cat_{categories[i]}"
            ))
            if i + 1 < len(categories):
                row.append(InlineKeyboardButton(
                    categories[i+1].capitalize(), 
                    callback_data=f"lore_cat_{categories[i+1]}"
                ))
            keyboard.append(row)
        
        # Add search button
        keyboard.append([InlineKeyboardButton("🔍 Search", callback_data="lore_search")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📚 *Explore the Lore of Fangen* 📚\n\n"
            "What aspect of this mystical world would you like to discover?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /search command to find specific lore entries."""
        user_id = update.effective_user.id
        query = ' '.join(context.args) if context.args else None
        
        if not query:
            await update.message.reply_text(
                "Please provide a search term after the command.\n"
                "Example: `/search Diamond`",
                parse_mode='Markdown'
            )
            return
        
        # Perform search
        results = self.lore_manager.search_lore(query)
        
        if not results:
            await update.message.reply_text(
                f"No lore entries found for '{query}'.\n\n"
                f"Try a different search term or browse categories with /lore"
            )
            return
        
        # Create keyboard with results
        keyboard = []
        total_results = 0
        result_count = 0
        max_results = MAX_SEARCH_RESULTS if hasattr(context, 'MAX_SEARCH_RESULTS') else 10
        
        for category, entries in results.items():
            if entries:
                # Add category header
                keyboard.append([InlineKeyboardButton(
                    f"📖 {category.capitalize()} ({len(entries)})",
                    callback_data=f"search_cat_{category}"
                )])
                
                # Add up to 3 results per category
                for i, entry in enumerate(entries[:3]):
                    keyboard.append([InlineKeyboardButton(
                        entry,
                        callback_data=f"lore_entry_{entry}"
                    )])
                    result_count += 1
                    if result_count >= max_results:
                        break
                
                # Add "See more" if there are more results
                if len(entries) > 3:
                    keyboard.append([InlineKeyboardButton(
                        f"See all {len(entries)} results in {category}...",
                        callback_data=f"search_more_{category}_{query}"
                    )])
                
                total_results += len(entries)
                
                # Break if we've added enough results
                if result_count >= max_results:
                    break
        
        # Add back button
        keyboard.append([InlineKeyboardButton("« Back to Lore", callback_data="lore_back")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🔍 *Search Results for '{query}'* 🔍\n\n"
            f"Found {total_results} entries across {len(results)} categories."
            f"{' Showing top results.' if total_results > max_results else ''}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def discover_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /discover command to find something new in the world."""
        user_id = update.effective_user.id
        
        # Get discovered entries
        discovered = self.db.execute_query(
            "SELECT category, item_name FROM user_progress WHERE user_id = ? AND discovered = TRUE",
            (user_id,)
        )
        
        discovered_set = set()
        if discovered:
            for item in discovered:
                discovered_set.add(f"{item['category']}:{item['item_name']}")
        
        # Get all entries from all categories
        all_entries = []
        for category, entries in self.lore_manager.lore_data.items():
            for entry_name in entries.keys():
                entry_key = f"{category}:{entry_name}"
                if entry_key not in discovered_set:
                    all_entries.append((category, entry_name))
        
        if not all_entries:
            await update.message.reply_text(
                "You've discovered all there is to know about the world of Fangen... for now. "
                "New mysteries await in future updates!"
            )
            return
        
        # Select a random undiscovered entry
        random_entry = random.choice(all_entries)
        category, entry_name = random_entry
        
        # Mark as discovered
        self.db.execute_query(
            "INSERT OR IGNORE INTO user_progress (user_id, category, item_name, discovered, discovery_date) "
            "VALUES (?, ?, ?, TRUE, CURRENT_TIMESTAMP)",
            (user_id, category, entry_name)
        )
        
        # Get entry content
        entry_content = self.lore_manager.get_entry_content(entry_name)
        
        if isinstance(entry_content, dict):
            # Format dict content
            formatted_content = ""
            for key, value in entry_content.items():
                if key not in ["name", "title", "rarity"] and value:
                    formatted_content += f"*{key.capitalize()}*: {value}\n\n"
            entry_content = formatted_content
        
        # Create discovery message based on category
        discovery_intro = {
            "world": "You've uncovered new knowledge about the world!",
            "events": "A historical event has been revealed to you!",
            "themes": "You've gained insight into a mystical concept!",
            "characters": "You've learned about a notable figure!",
            "locations": "You've discovered a new location!",
            "factions": "You've learned about a group or faction!",
            "items": "You've uncovered a legendary item!"
        }.get(category, "You've discovered something new!")
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton(
                f"Learn more about {entry_name}",
                callback_data=f"lore_entry_{entry_name}"
            )],
            [InlineKeyboardButton(
                "Discover more",
                callback_data="discover_more"
            )],
            [InlineKeyboardButton(
                "« Back to Lore",
                callback_data="lore_back"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Truncate content if too long
        if entry_content and len(entry_content) > 200:
            display_content = f"{entry_content[:200]}..."
        else:
            display_content = entry_content if entry_content else "No detailed information available yet."
        
        await update.message.reply_text(
            f"✨ *{discovery_intro}* ✨\n\n"
            f"*{entry_name}*\n\n"
            f"{display_content}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /status command to show user progress."""
        user_id = update.effective_user.id
        
        # Get user stats
        user_stats = self.db.execute_query(
            "SELECT COUNT(*) as total, category FROM user_progress "
            "WHERE user_id = ? AND discovered = TRUE GROUP BY category",
            (user_id,)
        )
        
        # Get total entries in each category
        total_entries = {}
        for category in self.lore_manager.lore_data:
            total_entries[category] = len(self.lore_manager.lore_data[category])
        
        # Format progress message
        progress_lines = []
        total_discovered = 0
        total_available = 0
        
        for category, count in total_entries.items():
            if count > 0:
                discovered = next((item['total'] for item in user_stats if item['category'] == category), 0)
                total_discovered += discovered
                total_available += count
                percentage = (discovered / count * 100) if count > 0 else 0
                progress_lines.append(f"{category.capitalize()}: {discovered}/{count} ({percentage:.1f}%)")
        
        overall_percentage = (total_discovered / total_available * 100) if total_available > 0 else 0
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton(
                "View Collection",
                callback_data="view_collection"
            )],
            [InlineKeyboardButton(
                "Discover Something New",
                callback_data="discover_more"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📊 *Your Exploration Progress* 📊\n\n"
            f"Overall: {total_discovered}/{total_available} ({overall_percentage:.1f}%)\n\n"
            + "\n".join(progress_lines),
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def collection_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /collection command to view discovered lore entries."""
        user_id = update.effective_user.id
        
        # Get discovered entries
        discovered = self.db.execute_query(
            "SELECT category, item_name FROM user_progress WHERE user_id = ? AND discovered = TRUE "
            "ORDER BY category, item_name",
            (user_id,)
        )
        
        if not discovered:
            await update.message.reply_text(
                "Your collection is empty. Use /discover to find lore entries!"
            )
            return
        
        # Organize by category
        collection = {}
        for item in discovered:
            category = item['category']
            if category not in collection:
                collection[category] = []
            collection[category].append(item['item_name'])
        
        # Create keyboard
        keyboard = []
        for category, items in collection.items():
            keyboard.append([InlineKeyboardButton(
                f"{category.capitalize()} ({len(items)})",
                callback_data=f"collection_cat_{category}"
            )])
        
        keyboard.append([InlineKeyboardButton("« Back to Status", callback_data="status_back")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📚 *Your Lore Collection* 📚\n\n"
            f"You've discovered {len(discovered)} entries across {len(collection)} categories.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /settings command."""
        user_id = update.effective_user.id
        
        # Get current settings
        user_settings = self.db.execute_query(
            "SELECT settings FROM users WHERE user_id = ?",
            (user_id,)
        )
        
        # Parse settings JSON or use default
        settings = {}
        if user_settings and user_settings[0]['settings']:
            try:
                import json
                settings = json.loads(user_settings[0]['settings'])
            except:
                settings = {}
        
        # Default settings
        if 'notifications' not in settings:
            settings['notifications'] = True
        if 'discovery_frequency' not in settings:
            settings['discovery_frequency'] = 'daily'
        if 'theme' not in settings:
            settings['theme'] = 'default'
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton(
                f"Notifications: {'ON' if settings['notifications'] else 'OFF'}",
                callback_data="toggle_notifications"
            )],
            [InlineKeyboardButton(
                f"Discovery Frequency: {settings['discovery_frequency'].capitalize()}",
                callback_data="cycle_discovery_frequency"
            )],
            [InlineKeyboardButton(
                f"Theme: {settings['theme'].capitalize()}",
                callback_data="cycle_theme"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚙️ *Bot Settings* ⚙️\n\n"
            "Customize your experience in the world of Fangen:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries for lore-related features."""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        user_id = update.effective_user.id
        
        logger.debug(f"Callback data: {callback_data}")
        
        # Category browsing
        if callback_data.startswith("lore_cat_"):
            category = callback_data.replace("lore_cat_", "")
            entries = self.lore_manager.get_entries_by_category(category)
            
            keyboard = []
            # Add entries in groups of 2
            for i in range(0, len(entries), 2):
                row = []
                row.append(InlineKeyboardButton(
                    entries[i],
                    callback_data=f"lore_entry_{entries[i]}"
                ))
                if i + 1 < len(entries):
                    row.append(InlineKeyboardButton(
                        entries[i+1],
                        callback_data=f"lore_entry_{entries[i+1]}"
                    ))
                keyboard.append(row)
            
            keyboard.append([InlineKeyboardButton("« Back", callback_data="lore_back")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📖 *{category.capitalize()} Lore Entries* 📖\n\n"
                f"Select an entry to learn more:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        # View lore entry
        elif callback_data.startswith("lore_entry_"):
            entry_name = callback_data.replace("lore_entry_", "")
            entry_content = self.lore_manager.get_entry_content(entry_name)
            
            if not entry_content:
                await query.edit_message_text(
                    f"The information about {entry_name} seems to be missing from the archives."
                )
                return
            
            # Mark entry as discovered
            category = None
            for cat, entries in self.lore_manager.lore_data.items():
                if entry_name in entries:
                    category = cat
                    break
            
            if category:
                self.db.execute_query(
                    "INSERT OR IGNORE INTO user_progress (user_id, category, item_name, discovered, discovery_date) "
                    "VALUES (?, ?, ?, TRUE, CURRENT_TIMESTAMP)",
                    (user_id, category, entry_name)
                )
            
            # Format content based on type
            if isinstance(entry_content, dict):
                # Format dict content
                formatted_content = ""
                for key, value in entry_content.items():
                    if key not in ["name", "title", "rarity"] and value:
                        formatted_content += f"*{key.capitalize()}*: {value}\n\n"
                content = formatted_content
            else:
                content = entry_content
            
            # Get related entries
            related_chars = self.lore_manager.get_related_characters(entry_name) if hasattr(self.lore_manager, 'get_related_characters') else []
            
            # Create keyboard with related entries and back button
            keyboard = []
            if related_chars:
                for i in range(0, len(related_chars), 2):
                    row = []
                    row.append(InlineKeyboardButton(
                        f"👤 {related_chars[i]}",
                        callback_data=f"lore_entry_{related_chars[i]}"
                    ))
                    if i + 1 < len(related_chars):
                        row.append(InlineKeyboardButton(
                            f"👤 {related_chars[i+1]}",
                            callback_data=f"lore_entry_{related_chars[i+1]}"
                        ))
                    keyboard.append(row)
            
            keyboard.append([InlineKeyboardButton("« Back", callback_data="lore_back")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"*{entry_name}*\n\n{content}",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        # Handle search
        elif callback_data == "lore_search":
            await query.edit_message_text(
                "🔍 *Search the Lore* 🔍\n\n"
                "To search for lore entries, use the command:\n"
                "/search [your search term]\n\n"
                "Example: `/search Diamond`",
                parse_mode='Markdown'
            )
        
        # Back to lore menu
        elif callback_data == "lore_back":
            # Re-create lore menu
            categories = self.lore_manager.get_categories()
            
            keyboard = []
            for i in range(0, len(categories), 2):
                row = []
                row.append(InlineKeyboardButton(
                    categories[i].capitalize(), 
                    callback_data=f"lore_cat_{categories[i]}"
                ))
                if i + 1 < len(categories):
                    row.append(InlineKeyboardButton(
                        categories[i+1].capitalize(), 
                        callback_data=f"lore_cat_{categories[i+1]}"
                    ))
                keyboard.append(row)
            
            keyboard.append([InlineKeyboardButton("🔍 Search", callback_data="lore_search")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "📚 *Explore the Lore of Fangen* 📚\n\n"
                "What aspect of this mystical world would you like to discover?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        # View collection category
        elif callback_data.startswith("collection_cat_"):
            category = callback_data.replace("collection_cat_", "")
            
            # Get discovered entries in this category
            discovered = self.db.execute_query(
                "SELECT item_name FROM user_progress "
                "WHERE user_id = ? AND category = ? AND discovered = TRUE "
                "ORDER BY item_name",
                (user_id, category)
            )
            
            if not discovered:
                await query.edit_message_text(
                    f"You haven't discovered any {category} entries yet."
                )
                return
            
            # Create keyboard with entries
            keyboard = []
            for item in discovered:
                keyboard.append([InlineKeyboardButton(
                    item['item_name'],
                    callback_data=f"lore_entry_{item['item_name']}"
                )])
            
            keyboard.append([InlineKeyboardButton("« Back to Collection", callback_data="view_collection")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📚 *Your {category.capitalize()} Collection* 📚\n\n"
                f"You've discovered {len(discovered)} entries in this category:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        # View collection
        elif callback_data == "view_collection":
            await self.collection_command(update, context)
        
        # Discover more
        elif callback_data == "discover_more":
            await self.discover_command(update, context)
        
        # Back to status
        elif callback_data == "status_back":
            await self.status_command(update, context)
        
        # Toggle notifications
        elif callback_data == "toggle_notifications":
            # Get current settings
            user_settings = self.db.execute_query(
                "SELECT settings FROM users WHERE user_id = ?",
                (user_id,)
            )
            
            # Parse settings JSON or use default
            settings = {}
            if user_settings and user_settings[0]['settings']:
                try:
                    import json
                    settings = json.loads(user_settings[0]['settings'])
                except:
                    settings = {}
            
            # Toggle notifications
            if 'notifications' not in settings:
                settings['notifications'] = True
            settings['notifications'] = not settings['notifications']
            
            # Save settings
            import json
            self.db.execute_query(
                "UPDATE users SET settings = ? WHERE user_id = ?",
                (json.dumps(settings), user_id)
            )
            
            # Recreate settings menu
            await self.settings_command(update, context)
        
        # Other settings callbacks
        elif callback_data in ["cycle_discovery_frequency", "cycle_theme"]:
            # Get current settings
            user_settings = self.db.execute_query(
                "SELECT settings FROM users WHERE user_id = ?",
                (user_id,)
            )
            
            # Parse settings JSON or use default
            settings = {}
            if user_settings and user_settings[0]['settings']:
                try:
                    import json
                    settings = json.loads(user_settings[0]['settings'])
                except:
                    settings = {}
            
            # Default settings
            if 'discovery_frequency' not in settings:
                settings['discovery_frequency'] = 'daily'
            if 'theme' not in settings:
                settings['theme'] = 'default'
            
            # Cycle settings
            if callback_data == "cycle_discovery_frequency":
                frequencies = ['daily', 'weekly', 'monthly', 'never']
                current_index = frequencies.index(settings['discovery_frequency'])
                settings['discovery_frequency'] = frequencies[(current_index + 1) % len(frequencies)]
            elif callback_data == "cycle_theme":
                themes = ['default', 'dark', 'light', 'mystic']
                current_index = themes.index(settings['theme'])
                settings['theme'] = themes[(current_index + 1) % len(themes)]
            
            # Save settings
            import json
            self.db.execute_query(
                "UPDATE users SET settings = ? WHERE user_id = ?",
                (json.dumps(settings), user_id)
            )
            
            # Recreate settings menu
            await self.settings_command(update, context)
        
        # Search category
        elif callback_data.startswith("search_cat_"):
            category = callback_data.replace("search_cat_", "")
            entries = self.lore_manager.get_entries_by_category(category)
            
            keyboard = []
            for entry in entries:
                keyboard.append([InlineKeyboardButton(
                    entry,
                    callback_data=f"lore_entry_{entry}"
                )])
            
            keyboard.append([InlineKeyboardButton("« Back to Search", callback_data="search_back")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🔍 *Search Results in {category.capitalize()}* 🔍\n\n"
                f"Found {len(entries)} entries:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        # See more search results
        elif callback_data.startswith("search_more_"):
            parts = callback_data.replace("search_more_", "").split("_")
            category = parts[0]
            query_text = parts[1] if len(parts) > 1 else ""
            
            # Get all entries in this category
            entries = self.lore_manager.get_entries_by_category(category)
            
            # Filter by query if provided
            if query_text:
                entries = [e for e in entries if query_text.lower() in e.lower()]
            
            keyboard = []
            for entry in entries:
                keyboard.append([InlineKeyboardButton(
                    entry,
                    callback_data=f"lore_entry_{entry}"
                )])
            
            keyboard.append([InlineKeyboardButton("« Back to Search", callback_data="search_back")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🔍 *All {category.capitalize()} Results* 🔍\n\n"
                f"Found {len(entries)} entries:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        # Back to search
        elif callback_data == "search_back":
            await query.edit_message_text(
                "🔍 *Search the Lore* 🔍\n\n"
                "To search for lore entries, use the command:\n"
                "/search [your search term]\n\n"
                "Example: `/search Diamond`",
                parse_mode='Markdown'
            )