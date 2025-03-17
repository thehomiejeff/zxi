#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Quest Manager for ChuzoBot
Handles quest progression, dialogue choices, and inventory integration
"""

import json
import random
from typing import Dict, List, Optional, Any, Tuple

from utils.logger import get_logger
from utils.database import Database
from utils.fangen_lore_manager import FangenLoreManager

logger = get_logger(__name__)

class QuestManager:
    """Manages quests, dialogues, and player progression."""
    
    def __init__(self, db: Database, lore_manager: FangenLoreManager):
        """Initialize the QuestManager."""
        self.db = db
        self.lore_manager = lore_manager
        self.active_quests = {}  # user_id -> active_quest_info
    
    def get_available_quests(self, user_id: int) -> List[Dict]:
        """Get available quests for a user."""
        # Get user progress data
        user_progress = self.db.execute_query(
            "SELECT * FROM user_progress WHERE user_id = ?",
            (user_id,)
        )
        
        completed_quests = [
            item['item_name'] for item in user_progress 
            if item['category'] == 'quests' and item['discovered']
        ]
        
        # Get all quests from lore manager
        all_quests = []
        for quest_name in self.lore_manager.get_quests():
            quest_info = self.lore_manager.get_quest_info(quest_name)
            if quest_info:
                quest = {
                    "name": quest_name,
                    "description": quest_info.get("description", ""),
                    "completed": quest_name in completed_quests
                }
                all_quests.append(quest)
        
        return all_quests
    
    def start_quest(self, user_id: int, quest_name: str) -> Tuple[bool, str, Dict]:
        """Start a quest for a user.
        
        Initializes a new quest for the user if they are not already on one,
        sets up the initial quest state, and returns the first scene.
        
        Args:
            user_id: The user ID starting the quest
            quest_name: The name of the quest to start
            
        Returns:
            Tuple containing (success, message, scene_data)
        """
        quest_info = self.lore_manager.get_quest_info(quest_name)
        if not quest_info:
            return False, f"Quest '{quest_name}' not found.", {}
        
        # Check if user is already on a quest
        if user_id in self.active_quests:
            return False, "You are already on a quest. Use /abandonquest to abandon your current quest.", {}
        
        # Set up initial quest state
        quest_state = {
            "quest_name": quest_name,
            "current_scene": 1,
            "choices_made": [],
            "inventory_updates": [],
            "dialogue_history": []
        }
        
        self.active_quests[user_id] = quest_state
        
        # Log quest start
        self.db.execute_query(
            "INSERT INTO quest_logs (user_id, quest_name, status, started_at) VALUES (?, ?, 'in_progress', CURRENT_TIMESTAMP)",
            (user_id, quest_name)
        )
        
        # Get first scene
        scenes = quest_info.get("scenes", [])
        if not scenes:
            return False, f"Quest '{quest_name}' has no scenes defined.", {}
        
        first_scene = next((s for s in scenes if s["number"] == "1"), None)
        if not first_scene:
            return False, f"First scene of quest '{quest_name}' not found.", {}
        
        # Format scene for display
        scene_data = self._format_scene_for_display(first_scene)
        
        return True, f"You have started the quest: {quest_name}", scene_data
    
    def make_choice(self, user_id: int, choice_id: str) -> Tuple[bool, str, Dict]:
        """Process a user's choice in a quest.
        
        Handles the user's decision in the current quest scene, updates quest state,
        processes inventory changes, and determines the next scene.
        
        Args:
            user_id: The user ID making the choice
            choice_id: The ID of the choice selected
            
        Returns:
            Tuple containing (success, message, scene_data)
        """
        if user_id not in self.active_quests:
            return False, "You are not currently on a quest.", {}
        
        quest_state = self.active_quests[user_id]
        quest_name = quest_state["quest_name"]
        quest_info = self.lore_manager.get_quest_info(quest_name)
        
        if not quest_info:
            return False, f"Quest '{quest_name}' not found.", {}
        
        # Find current scene
        current_scene_num = quest_state["current_scene"]
        scenes = quest_info.get("scenes", [])
        current_scene = next((s for s in scenes if s["number"] == str(current_scene_num)), None)
        
        if not current_scene:
            return False, f"Scene {current_scene_num} of quest '{quest_name}' not found.", {}
        
        # Find choice
        choice = next((c for c in current_scene["choices"] if c["id"] == choice_id), None)
        if not choice:
            return False, f"Choice '{choice_id}' not found in current scene.", {}
        
        # Process choice
        quest_state["choices_made"].append({
            "scene": current_scene_num,
            "choice_id": choice_id,
            "description": choice["description"]
        })
        
        # Add to dialogue history
        if choice["player_dialogue"]:
            quest_state["dialogue_history"].append({
                "speaker": "player",
                "text": choice["player_dialogue"]
            })
        
        # Process inventory updates
        for update in choice["inventory_updates"]:
            if "Add" in update:
                item_name = update.replace("Add ", "").split(" (")[0]
                rarity = "Normal"
                if "(" in update and ")" in update:
                    rarity_match = update.split("(")[1].split(")")[0]
                    if rarity_match in ["Normal", "Rare", "Legendary"]:
                        rarity = rarity_match
                
                # Add item to user inventory
                self.db.execute_query(
                    "INSERT OR IGNORE INTO user_inventory (user_id, item_name, rarity, quantity, acquired_at) "
                    "VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)",
                    (user_id, item_name, rarity)
                )
                
                # Increment if already exists
                self.db.execute_query(
                    "UPDATE user_inventory SET quantity = quantity + 1 WHERE user_id = ? AND item_name = ?",
                    (user_id, item_name)
                )
                
                quest_state["inventory_updates"].append(f"Added {item_name} ({rarity})")
            
            elif "Consume" in update or "Remove" in update:
                items = update.replace("Consume ", "").replace("Remove ", "").split(" and ")
                for item in items:
                    item_name = item.strip()
                    
                    # Remove item from user inventory
                    self.db.execute_query(
                        "UPDATE user_inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_name = ? AND quantity > 0",
                        (user_id, item_name)
                    )
                    
                    quest_state["inventory_updates"].append(f"Consumed {item_name}")
        
        # Determine next scene
        next_scene_num = current_scene_num + 1
        next_scene = next((s for s in scenes if s["number"] == str(next_scene_num)), None)
        
        if next_scene:
            # Move to next scene
            quest_state["current_scene"] = next_scene_num
            scene_data = self._format_scene_for_display(next_scene)
            return True, f"You chose: {choice['description']}", scene_data
        else:
            # End of quest
            self._complete_quest(user_id, quest_name)
            return True, f"Quest '{quest_name}' completed!", {
                "type": "quest_end",
                "title": f"Quest Completed: {quest_name}",
                "text": "Congratulations! You have completed the quest.",
                "choices_made": quest_state["choices_made"],
                "inventory_updates": quest_state["inventory_updates"]
            }
    
    def _complete_quest(self, user_id: int, quest_name: str) -> None:
        """Mark a quest as completed for a user."""
        # Update quest log
        self.db.execute_query(
            "UPDATE quest_logs SET status = 'completed', completed_at = CURRENT_TIMESTAMP "
            "WHERE user_id = ? AND quest_name = ? AND status = 'in_progress'",
            (user_id, quest_name)
        )
        
        # Update user progress
        self.db.execute_query(
            "INSERT OR IGNORE INTO user_progress (user_id, category, item_name, discovered, discovery_date) "
            "VALUES (?, 'quests', ?, TRUE, CURRENT_TIMESTAMP)",
            (user_id, quest_name)
        )
        
        # Remove from active quests
        if user_id in self.active_quests:
            del self.active_quests[user_id]
    
    def abandon_quest(self, user_id: int) -> Tuple[bool, str]:
        """Abandon a user's current quest."""
        if user_id not in self.active_quests:
            return False, "You are not currently on a quest."
        
        quest_name = self.active_quests[user_id]["quest_name"]
        
        # Update quest log
        self.db.execute_query(
            "UPDATE quest_logs SET status = 'abandoned', completed_at = CURRENT_TIMESTAMP "
            "WHERE user_id = ? AND quest_name = ? AND status = 'in_progress'",
            (user_id, quest_name)
        )
        
        # Remove from active quests
        del self.active_quests[user_id]
        
        return True, f"You have abandoned the quest: {quest_name}"
    
    def get_current_quest(self, user_id: int) -> Tuple[bool, str, Dict]:
        """Get the current quest state for a user.
        
        Retrieves the active quest information for a user, including
        the current scene and available choices.
        
        Args:
            user_id: The user ID to check for active quests
            
        Returns:
            Tuple containing (success, message, scene_data)
        """
        if user_id not in self.active_quests:
            return False, "You are not currently on a quest.", {}
        
        quest_state = self.active_quests[user_id]
        quest_name = quest_state["quest_name"]
        quest_info = self.lore_manager.get_quest_info(quest_name)
        
        if not quest_info:
            return False, f"Quest '{quest_name}' not found.", {}
        
        # Find current scene
        current_scene_num = quest_state["current_scene"]
        scenes = quest_info.get("scenes", [])
        current_scene = next((s for s in scenes if s["number"] == str(current_scene_num)), None)
        
        if not current_scene:
            return False, f"Scene {current_scene_num} of quest '{quest_name}' not found.", {}
        
        # Format scene for display
        scene_data = self._format_scene_for_display(current_scene)
        
        return True, f"Current quest: {quest_name} (Scene {current_scene_num})", scene_data
    
    def _format_scene_for_display(self, scene: Dict) -> Dict:
        """Format a scene for display to the user.
        
        Converts the internal scene representation into a format suitable
        for display to the user in the Telegram interface.
        
        Args:
            scene: Dictionary containing scene data
            
        Returns:
            Dictionary with formatted scene content for display
        """
        # Build narrative text
        narrative = f"**Scene {scene['number']}: {scene['title']}**\n\n"
        
        if scene['setting']:
            narrative += f"*{scene['setting']}\n\n"
        
        # Add NPC dialogues
        for npc, dialogue in scene.get('npc_dialogues', {}).items():
            narrative += f"**{npc}**: \"{dialogue}\"\n\n"
        
        # Format choices
        choices = []
        for choice in scene.get('choices', []):
            choices.append({
                "id": choice['id'],
                "text": choice['description']
            })
        
        return {
            "type": "scene",
            "narrative": narrative,
            "choices": choices
        }
    
    def get_character_response(self, user_id: int, character_name: str, message: str) -> str:
        """Generate a response from a character based on the user's message."""
        character_info = self.lore_manager.get_character_info(character_name)
        if not character_info:
            return f"I am {character_name}, but I don't seem to have much to say right now."
        
        # Log interaction in database
        self.db.execute_query(
            "INSERT INTO interactions (user_id, character, message, timestamp) "
            "VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            (user_id, character_name, message)
        )
        
        # Extract character traits and info
        personality = character_info.get("personality", "")
        backstory = character_info.get("backstory", "")
        
        # Look for keywords in the user's message that might match character lore
        keywords = [word.lower() for word in message.split() if len(word) > 3]
        
        # Find relevant information based on keywords
        relevant_info = []
        
        # Check in backstory
        for keyword in keywords:
            if keyword in backstory.lower():
                sentences = backstory.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        relevant_info.append(sentence.strip())
        
        # Check in personality if needed
        if not relevant_info:
            for keyword in keywords:
                if keyword in personality.lower():
                    sentences = personality.split('.')
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            relevant_info.append(sentence.strip())
        
        # Generate response based on character info
        if relevant_info:
            # Create character-specific response incorporating relevant info
            intro_phrases = self._get_character_intros(character_name, character_info)
            return f"{random.choice(intro_phrases)} {random.choice(relevant_info)}."
        else:
            # Generate generic response based on character traits
            return self._generate_generic_response(character_name, character_info, message)
    
    def _get_character_intros(self, character_name: str, character_info: Dict) -> List[str]:
        """Get character-specific introduction phrases."""
        # Define default intros
        default_intros = [
            "Indeed,",
            "As you may know,",
            "I must tell you that",
            "It is known that",
            "Let me share with you,"
        ]
        
        # Check personality traits for character-specific intros
        personality = character_info.get("personality", "").lower()
        
        if "arrogant" in personality or "cunning" in personality:
            return [
                "Obviously, for one of my standing,",
                "Few would understand this, but",
                "Let me enlighten you with this knowledge:",
                "I suppose I can share this with you:",
                "How interesting that you should ask about that."
            ]
        elif "stoic" in personality or "cold" in personality:
            return [
                "Consider this information carefully:",
                "These are the facts:",
                "Without embellishment, I will tell you:",
                "It is simply thus:",
                "The truth of the matter is"
            ]
        elif "playful" in personality or "eccentric" in personality:
            return [
                "Ooh! That's a good question!",
                "Isn't it fascinating that",
                "Well, here's something delightful:",
                "Ha! You're curious about that?",
                "Oh, I've got a story about that!"
            ]
        elif "fierce" in personality or "protective" in personality:
            return [
                "Listen well, for this is important:",
                "I will tell you this only once:",
                "Stand firm as I reveal that",
                "This knowledge is worth defending:",
                "As one who has fought for this truth:"
            ]
        
        return default_intros
    
    def _generate_generic_response(self, character_name: str, character_info: Dict, message: str) -> str:
        """Generate a generic response based on character traits."""
        personality = character_info.get("personality", "").lower()
        role = character_info.get("role", "").lower()
        
        # Character-specific generic responses
        if character_name == "Hand of Diamond":
            return f"The Element of Diamond resonates with courage and unity. Your question about '{message}' touches on matters of great importance to the balance of power."
        
        elif character_name == "Zero":
            return f"My visions show many possible futures. The path you seek regarding '{message}' is but one of many, yet it could be crucial to preventing catastrophe."
        
        elif character_name == "Wagami":
            return f"*adjusts glasses excitedly* Oh! That's an interesting query about '{message}'! It reminds me of an experiment I was conducting just last week with the wormhole dynamics!"
        
        elif character_name == "Anko":
            return f"*flips kunai knife casually* You want to know about '{message}'? Well, I could tell you... but then I'd have to... you know the rest. *smirks*"
        
        # Generic responses based on personality types
        elif "arrogant" in personality or "cunning" in personality:
            return f"Your curiosity about '{message}' is... quaint. Perhaps someday you'll understand the true significance of what you ask."
        
        elif "stoic" in personality or "cold" in personality:
            return f"I have witnessed much regarding '{message}'. Whether you are ready for such knowledge remains to be seen."
        
        elif "playful" in personality or "eccentric" in personality:
            return f"*eyes light up* '{message}'? Now that's a topic full of surprises! Just when you think you understand it, everything turns upside down!"
        
        elif "fierce" in personality or "protective" in personality:
            return f"I would guard the truth about '{message}' with my life. It is not knowledge to be taken lightly."
        
        # Default response if no specific patterns match
        return f"You ask about '{message}'? That is a matter that intersects with my experiences in ways you might not expect."
    
    def get_inventory(self, user_id: int) -> List[Dict]:
        """Get the user's inventory."""
        items = self.db.execute_query(
            "SELECT item_name, rarity, quantity FROM user_inventory WHERE user_id = ? AND quantity > 0",
            (user_id,)
        )
        
        inventory = []
        for item in items:
            item_info = self.lore_manager.get_item_info(item['item_name'])
            description = ""
            if item_info and isinstance(item_info, dict):
                description = item_info.get("description", "")
            
            inventory.append({
                "name": item['item_name'],
                "rarity": item['rarity'],
                "quantity": item['quantity'],
                "description": description
            })
        
        return inventory