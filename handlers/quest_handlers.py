#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Command handlers for ChuzoBot's Quest System
"""

import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.logger import get_logger
from utils.fangen_lore_manager import FangenLoreManager
from utils.database import Database
from utils.quest_manager import QuestManager
from config import BOT_NAME

logger = get_logger(__name__)

class QuestCommandHandlers:
    """Command handlers for quest-related features."""
    
    def __init__(self, lore_manager: FangenLoreManager, db: Database, quest_manager: QuestManager):
        """Initialize quest command handlers."""
        self.lore_manager = lore_manager
        self.db = db
        self.quest_manager = quest_manager
    
    async def quests_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /quests command to view available quests."""
        user_id = update.effective_user.id
        
        # Log user action
        self.db.execute_query(
            "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_id,)
        )
        
        # Get available quests
        available_quests = self.quest_manager.get_available_quests(user_id)
        
        if not available_quests:
            await update.message.reply_text(
                "No quests are available at the moment. "
                "Continue exploring the world of Fangen to unlock new adventures."
            )
            return
        
        # Create keyboard with available quests
        keyboard = []
        for quest in available_quests:
            status = "✅" if quest["completed"] else "⏳"
            keyboard.append([InlineKeyboardButton(
                f"{status} {quest['name']}",
                callback_data=f"quest_view_{quest['name']}"
            )])
        
        keyboard.append([InlineKeyboardButton("« Back to Main Menu", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📜 *Available Quests* 📜\n\n"
            "Select a quest to view its details or begin the adventure:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def start_quest_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /startquest command to begin a specific quest."""
        user_id = update.effective_user.id
        quest_name = ' '.join(context.args) if context.args else None
        
        if not quest_name:
            # If no quest name provided, show available quests
            await self.quests_command(update, context)
            return
        
        # Start the quest
        success, message, scene_data = self.quest_manager.start_quest(user_id, quest_name)
        
        if not success:
            await update.message.reply_text(message)
            return
        
        # Format scene for display
        narrative = scene_data.get("narrative", "")
        choices = scene_data.get("choices", [])
        
        # Create choice buttons
        keyboard = []
        for choice in choices:
            keyboard.append([InlineKeyboardButton(
                choice["text"],
                callback_data=f"quest_choice_{choice['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("Abandon Quest", callback_data="quest_abandon")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"{message}\n\n{narrative}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def current_quest_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /currentquest command to view the current quest status."""
        user_id = update.effective_user.id
        
        # Get current quest
        success, message, scene_data = self.quest_manager.get_current_quest(user_id)
        
        if not success:
            await update.message.reply_text(message)
            return
        
        # Format scene for display
        narrative = scene_data.get("narrative", "")
        choices = scene_data.get("choices", [])
        
        # Create choice buttons
        keyboard = []
        for choice in choices:
            keyboard.append([InlineKeyboardButton(
                choice["text"],
                callback_data=f"quest_choice_{choice['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("Abandon Quest", callback_data="quest_abandon")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"{message}\n\n{narrative}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def abandon_quest_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /abandonquest command to abandon the current quest."""
        user_id = update.effective_user.id
        
        # Abandon the quest
        success, message = self.quest_manager.abandon_quest(user_id)
        
        await update.message.reply_text(message)
    
    async def inventory_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /inventory command to view the user's inventory."""
        user_id = update.effective_user.id
        
        # Get inventory
        inventory = self.quest_manager.get_inventory(user_id)
        
        if not inventory:
            await update.message.reply_text(
                "Your inventory is empty. Complete quests and collect items to fill it."
            )
            return
        
        # Format inventory for display
        inventory_text = "🎒 *Your Inventory* 🎒\n\n"
        
        # Group by rarity
        rarities = {"Legendary": [], "Rare": [], "Normal": []}
        
        for item in inventory:
            rarities[item["rarity"]].append(item)
        
        # Display Legendary items first, then Rare, then Normal
        for rarity, items in rarities.items():
            if items:
                if rarity == "Legendary":
                    inventory_text += "✨ *LEGENDARY ITEMS* ✨\n"
                elif rarity == "Rare":
                    inventory_text += "🔹 *RARE ITEMS* 🔹\n"
                else:
                    inventory_text += "📦 *NORMAL ITEMS* 📦\n"
                
                for item in items:
                    inventory_text += f"• {item['name']} (x{item['quantity']})\n"
                
                inventory_text += "\n"
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton("View Item Details", callback_data="inventory_details")],
            [InlineKeyboardButton("Craft Items", callback_data="inventory_craft")],
            [InlineKeyboardButton("« Back to Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            inventory_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def craft_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /craft command to craft items."""
        user_id = update.effective_user.id
        item_name = ' '.join(context.args) if context.args else None
        
        if not item_name:
            # Show available recipes
            recipes = self.db.execute_query(
                "SELECT result_item, result_rarity, description FROM crafting_recipes"
            )
            
            if not recipes:
                await update.message.reply_text(
                    "No crafting recipes are available. Discover more recipes by exploring the world."
                )
                return
            
            # Create recipe buttons
            keyboard = []
            for recipe in recipes:
                rarity_symbol = "✨" if recipe["result_rarity"] == "Legendary" else "🔹" if recipe["result_rarity"] == "Rare" else "📦"
                keyboard.append([InlineKeyboardButton(
                    f"{rarity_symbol} {recipe['result_item']}",
                    callback_data=f"craft_check_{recipe['result_item']}"
                )])
            
            keyboard.append([InlineKeyboardButton("« Back to Inventory", callback_data="inventory_back")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "🔨 *Crafting Workshop* 🔨\n\n"
                "Select an item to craft:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        # Check if user can craft the item
        can_craft, message, details = self.db.can_craft_item(user_id, item_name)
        
        if not can_craft:
            missing_items = details.get("missing", [])
            missing_text = "\n".join([f"• {item}" for item in missing_items])
            
            await update.message.reply_text(
                f"{message}\n\n{missing_text}\n\nContinue your adventures to gather the required components."
            )
            return
        
        # Create confirmation button
        keyboard = [
            [InlineKeyboardButton("Craft Now", callback_data=f"craft_confirm_{item_name}")],
            [InlineKeyboardButton("Cancel", callback_data="craft_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        recipe = details.get("recipe", {})
        requirements = json.loads(recipe.get("requirements", "{}"))
        req_text = "\n".join([f"• {item} x{qty}" for item, qty in requirements.items()])
        
        await update.message.reply_text(
            f"📜 *Crafting {item_name}* 📜\n\n"
            f"Description: {recipe.get('description', '')}\n\n"
            f"Required Components:\n{req_text}\n\n"
            f"This will create: 1x {item_name} ({recipe.get('result_rarity', 'Normal')})\n\n"
            f"Proceed with crafting?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def interact_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /interact command to speak with characters."""
        user_id = update.effective_user.id
        character_name = ' '.join(context.args) if context.args else None
        
        # Log user action
        self.db.execute_query(
            "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_id,)
        )
        
        if not character_name:
            # Show available characters
            characters = self.lore_manager.get_characters()
            
            if not characters:
                await update.message.reply_text(
                    "No characters are available for interaction at the moment. "
                    "Check back later as the world of Fangen continues to unfold."
                )
                return
            
            # Create keyboard with characters
            keyboard = []
            for i in range(0, len(characters), 2):
                row = []
                row.append(InlineKeyboardButton(
                    characters[i], 
                    callback_data=f"interact_{characters[i]}"
                ))
                if i + 1 < len(characters):
                    row.append(InlineKeyboardButton(
                        characters[i+1], 
                        callback_data=f"interact_{characters[i+1]}"
                    ))
                keyboard.append(row)
            
            # Add back button
            keyboard.append([InlineKeyboardButton("« Back to Main Menu", callback_data="main_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "👥 *Characters of Fangen* 👥\n\n"
                "Who would you like to interact with?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        # Start interaction with the character
        # Mark character as discovered
        self.db.execute_query(
            "INSERT OR IGNORE INTO user_progress (user_id, category, item_name, discovered, discovery_date) "
            "VALUES (?, 'characters', ?, TRUE, CURRENT_TIMESTAMP)",
            (user_id, character_name)
        )
        
        # Store the active character in user context
        context.user_data['active_character'] = character_name
        
        # Get character info
        character_info = self.lore_manager.get_character_info(character_name)
        
        if not character_info:
            await update.message.reply_text(
                f"Character '{character_name}' not found. Use /interact to see available characters."
            )
            return
        
        # Create introduction message
        backstory = character_info.get("backstory", "")
        personality = character_info.get("personality", "")
        role = character_info.get("role", "")
        
        intro = f"You are now speaking with *{character_name}*.\n\n"
        
        if role:
            intro += f"*Role*: {role}\n\n"
        
        if isinstance(personality, str) and personality:
            intro += f"*{character_name}* stands before you, their demeanor suggesting someone who is {personality.lower()}.\n\n"
        
        intro += "You may now speak with them. Type your message to continue the conversation."
        
        # Add end conversation button
        keyboard = [[InlineKeyboardButton(
            "End Conversation", 
            callback_data=f"end_interaction_{character_name}"
        )]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            intro,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_character_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle messages sent to characters."""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Check if user is in an active character interaction
        active_character = context.user_data.get('active_character')
        
        if not active_character:
            # Not in a character interaction, handle as normal message
            return False
        
        # Get character response
        response = self.quest_manager.get_character_response(user_id, active_character, message_text)
        
        # Update character relationship
        self.db.execute_query(
            "INSERT OR IGNORE INTO character_relationships (user_id, character_name, relationship_level, last_interaction) "
            "VALUES (?, ?, 0, CURRENT_TIMESTAMP)",
            (user_id, active_character)
        )
        
        self.db.execute_query(
            "UPDATE character_relationships SET last_interaction = CURRENT_TIMESTAMP WHERE user_id = ? AND character_name = ?",
            (user_id, active_character)
        )
        
        # Add end conversation button
        keyboard = [[InlineKeyboardButton(
            "End Conversation", 
            callback_data=f"end_interaction_{active_character}"
        )]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"*{active_character}*: {response}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return True  # Message handled
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries from inline keyboards."""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        user_id = update.effective_user.id
        
        logger.debug(f"Callback data: {callback_data}")
        
        # Quest view callbacks
        if callback_data.startswith("quest_view_"):
            quest_name = callback_data.replace("quest_view_", "")
            quest_info = self.lore_manager.get_quest_info(quest_name)
            
            if not quest_info:
                await query.edit_message_text(
                    f"Details for quest '{quest_name}' not found."
                )
                return
            
            # Check if quest is completed
            completed = self.db.execute_query(
                "SELECT * FROM user_progress WHERE user_id = ? AND category = 'quests' AND item_name = ? AND discovered = TRUE",
                (user_id, quest_name)
            )
            
            status = "✅ Completed" if completed else "⏳ Available"
            
            # Create keyboard
            keyboard = [
                [InlineKeyboardButton(
                    "Start Quest" if not completed else "Replay Quest",
                    callback_data=f"quest_start_{quest_name}"
                )],
                [InlineKeyboardButton("« Back to Quests", callback_data="quests_back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📜 *{quest_name}* 📜\n\n"
                f"Status: {status}\n\n"
                f"{quest_info.get('description', '')}\n\n"
                f"Are you ready to embark on this adventure?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        # Quest start callbacks
        elif callback_data.startswith("quest_start_"):
            quest_name = callback_data.replace("quest_start_", "")
            
            # Start the quest
            success, message, scene_data = self.quest_manager.start_quest(user_id, quest_name)
            
            if not success:
                await query.edit_message_text(message)
                return
            
            # Format scene for display
            narrative = scene_data.get("narrative", "")
            choices = scene_data.get("choices", [])
            
            # Create choice buttons
            keyboard = []
            for choice in choices:
                keyboard.append([InlineKeyboardButton(
                    choice["text"],
                    callback_data=f"quest_choice_{choice['id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("Abandon Quest", callback_data="quest_abandon")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"{message}\n\n{narrative}",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        # Quest choice callbacks
        elif callback_data.startswith("quest_choice_"):
            choice_id = callback_data.replace("quest_choice_", "")
            
            # Process the choice
            success, message, scene_data = self.quest_manager.make_choice(user_id, choice_id)
            
            if not success:
                await query.edit_message_text(message)
                return
            
            # Check if quest ended
            if scene_data.get("type") == "quest_end":
                title = scene_data.get("title", "")
                text = scene_data.get("text", "")
                
                # Create end buttons
                keyboard = [
                    [InlineKeyboardButton("View Rewards", callback_data="quest_rewards")],
                    [InlineKeyboardButton("« Back to Quests", callback_data="quests_back")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"*{title}*\n\n{text}",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return
            
            # Format scene for display
            narrative = scene_data.get("narrative", "")
            choices = scene_data.get("choices", [])
            
            # Create choice buttons
            keyboard = []
            for choice in choices:
                keyboard.append([InlineKeyboardButton(
                    choice["text"],
                    callback_data=f"quest_choice_{choice['id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("Abandon Quest", callback_data="quest_abandon")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"{message}\n\n{narrative}",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        # Quest abandon callback
        elif callback_data == "quest_abandon":
            # Abandon the quest
            success, message = self.quest_manager.abandon_quest(user_id)
            
            # Create back button
            keyboard = [[InlineKeyboardButton("« Back to Quests", callback_data="quests_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup
            )
        
        # Quest rewards callback
        elif callback_data == "quest_rewards":
            # Get inventory updates from recently completed quest
            if user_id in self.quest_manager.active_quests:
                quest_state = self.quest_manager.active_quests[user_id]
                inventory_updates = quest_state.get("inventory_updates", [])
                
                updates_text = "\n".join([f"• {update}" for update in inventory_updates]) if inventory_updates else "No rewards found."
                
                # Create back button
                keyboard = [[InlineKeyboardButton("« Back to Quests", callback_data="quests_back")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"🏆 *Quest Rewards* 🏆\n\n{updates_text}",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    "No active quest found.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back to Quests", callback_data="quests_back")]])
                )
        
        # Back to quests callback
        elif callback_data == "quests_back":
            await self.quests_command(update, context)
        
        # Interact callbacks
        elif callback_data.startswith("interact_"):
            character_name = callback_data.replace("interact_", "")
            
            # Store the active character in user context
            context.user_data['active_character'] = character_name
            
            # Get character info
            character_info = self.lore_manager.get_character_info(character_name)
            
            if not character_info:
                await query.edit_message_text(
                    f"Character '{character_name}' not found."
                )
                return
            
            # Mark character as discovered
            self.db.execute_query(
                "INSERT OR IGNORE INTO user_progress (user_id, category, item_name, discovered, discovery_date) "
                "VALUES (?, 'characters', ?, TRUE, CURRENT_TIMESTAMP)",
                (user_id, character_name)
            )
            
            # Create introduction message
            backstory = character_info.get("backstory", "")
            personality = character_info.get("personality", "")
            role = character_info.get("role", "")
            
            intro = f"You are now speaking with *{character_name}*.\n\n"
            
            if role:
                intro += f"*Role*: {role}\n\n"
            
            if isinstance(personality, str) and personality:
                intro += f"*{character_name}* stands before you, their demeanor suggesting someone who is {personality.lower()}.\n\n"
            
            intro += "You may now speak with them. Type your message to continue the conversation."
            
            # Add end conversation button
            keyboard = [[InlineKeyboardButton(
                "End Conversation", 
                callback_data=f"end_interaction_{character_name}"
            )]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                intro,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        # End interaction callbacks
        elif callback_data.startswith("end_interaction_"):
            character_name = callback_data.replace("end_interaction_", "")
            
            # Clear active character
            if 'active_character' in context.user_data:
                del context.user_data['active_character']
            
            # Create back button
            keyboard = [[InlineKeyboardButton("« Back to Characters", callback_data="interact_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"Your conversation with *{character_name}* has ended.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        # Back to characters callback
        elif callback_data == "interact_back":
            await self.interact_command(update, context)
        
        # Crafting callbacks
        elif callback_data.startswith("craft_check_"):
            item_name = callback_data.replace("craft_check_", "")
            
            # Check if user can craft the item
            can_craft, message, details = self.db.can_craft_item(user_id, item_name)
            
            if not can_craft:
                missing_items = details.get("missing", [])
                missing_text = "\n".join([f"• {item}" for item in missing_items]) if missing_items else "No specific requirements found."
                
                # Create back button
                keyboard = [[InlineKeyboardButton("« Back to Crafting", callback_data="inventory_craft")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"{message}\n\n{missing_text}\n\nContinue your adventures to gather the required components.",
                    reply_markup=reply_markup
                )
                return
            
            # Create confirmation button
            keyboard = [
                [InlineKeyboardButton("Craft Now", callback_data=f"craft_confirm_{item_name}")],
                [InlineKeyboardButton("Cancel", callback_data="craft_cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            recipe = details.get("recipe", {})
            requirements = json.loads(recipe.get("requirements", "{}"))
            req_text = "\n".join([f"• {item} x{qty}" for item, qty in requirements.items()]) if requirements else "No requirements needed."
            
            await query.edit_message_text(
                f"📜 *Crafting {item_name}* 📜\n\n"
                f"Description: {recipe.get('description', '')}\n\n"
                f"Required Components:\n{req_text}\n\n"
                f"This will create: 1x {item_name} ({recipe.get('result_rarity', 'Normal')})\n\n"
                f"Proceed with crafting?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        # Craft confirm callbacks
        elif callback_data.startswith("craft_confirm_"):
            item_name = callback_data.replace("craft_confirm_", "")
            
            # Craft the item
            success, message = self.db.craft_item(user_id, item_name)
            
            # Create back button
            keyboard = [[InlineKeyboardButton("« Back to Inventory", callback_data="inventory_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup
            )
        
        # Craft cancel callback
        elif callback_data == "craft_cancel":
            # Create back button
            keyboard = [[InlineKeyboardButton("« Back to Crafting", callback_data="inventory_craft")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Crafting canceled.",
                reply_markup=reply_markup
            )
        
        # Inventory details callback
        elif callback_data == "inventory_details":
            # Get inventory
            inventory = self.quest_manager.get_inventory(user_id)
            
            if not inventory:
                await query.edit_message_text(
                    "Your inventory is empty.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back to Main Menu", callback_data="main_menu")]])
                )
                return
            
            # Create item buttons
            keyboard = []
            for item in inventory:
                keyboard.append([InlineKeyboardButton(
                    f"{item['name']} (x{item['quantity']})",
                    callback_data=f"item_view_{item['name']}"
                )])
            
            keyboard.append([InlineKeyboardButton("« Back to Inventory", callback_data="inventory_back")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🔍 *Item Details* 🔍\n\n"
                "Select an item to view its details:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        # Item view callbacks
        elif callback_data.startswith("item_view_"):
            item_name = callback_data.replace("item_view_", "")
            
            # Get item details
            item_info = self.lore_manager.get_item_info(item_name)
            
            if not item_info:
                await query.edit_message_text(
                    f"Details for item '{item_name}' not found.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back to Inventory", callback_data="inventory_details")]])
                )
                return
            
            # Get item quantity
            item_quantity = 0
            inventory = self.quest_manager.get_inventory(user_id)
            for item in inventory:
                if item['name'] == item_name:
                    item_quantity = item['quantity']
                    break
            
            # Format item details
            rarity = "Normal"
            description = ""
            
            if isinstance(item_info, dict):
                rarity = item_info.get("rarity", "Normal")
                description = item_info.get("description", "")
            else:
                description = item_info
            
            # Create back button
            keyboard = [[InlineKeyboardButton("« Back to Items", callback_data="inventory_details")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📦 *{item_name}* 📦\n\n"
                f"Rarity: {rarity}\n"
                f"Quantity: {item_quantity}\n\n"
                f"Description: {description}",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        # Back to inventory callback
        elif callback_data == "inventory_back":
            await self.inventory_command(update, context)
        
        # Inventory craft callback
        elif callback_data == "inventory_craft":
            await self.craft_command(update, context)
        
        # Main menu callback
        elif callback_data == "main_menu":
            # Create main menu
            keyboard = [
                [InlineKeyboardButton("📜 Quests", callback_data="quests_menu")],
                [InlineKeyboardButton("👥 Characters", callback_data="characters_menu")],
                [InlineKeyboardButton("🎒 Inventory", callback_data="inventory_menu")],
                [InlineKeyboardButton("📚 Lore", callback_data="lore_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"Welcome to the world of Fangen! I am {BOT_NAME}, your guide through this mystical realm.\n\n"
                f"What would you like to explore today?",
                reply_markup=reply_markup
            )
        
        # Menu redirects
        elif callback_data == "quests_menu":
            await self.quests_command(update, context)
        elif callback_data == "characters_menu":
            await self.interact_command(update, context)
        elif callback_data == "inventory_menu":
            await self.inventory_command(update, context)
        elif callback_data == "lore_menu":
            # Redirect to lore command
            # This would be handled by another class
            pass