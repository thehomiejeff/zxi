#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fangen Lore Manager for ChuzoBot
Handles loading, parsing, and retrieving the rich world of Fangen
"""

import os
import re
import json
from typing import Dict, List, Optional, Tuple, Any

from utils.logger import get_logger
from config import LORE_FILE

logger = get_logger(__name__)

class FangenLoreManager:
    """Manages lore content for the Fangen universe."""
    
    def __init__(self, lore_file: str = LORE_FILE):
        """Initialize the LoreManager."""
        self.lore_file = lore_file
        self.lore_data = {
            "world": {},
            "events": {},
            "themes": {},
            "characters": {},
            "locations": {},
            "factions": {},
            "items": {},
            "quests": {}
        }
        self.characters = []
        self.items = []
        self.quests = []
        self.load_lore()
    
    def load_lore(self) -> None:
        """Load lore from the specified file."""
        try:
            if not os.path.exists(self.lore_file):
                logger.warning(f"Lore file not found: {self.lore_file}")
                return
            
            with open(self.lore_file, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            # Parse the lore content
            self._parse_lore_content(raw_content)
            logger.info(f"Fangen lore loaded successfully from {self.lore_file}")
            
        except Exception as e:
            logger.error(f"Error loading lore: {e}", exc_info=True)
    
    def _parse_lore_content(self, content: str) -> None:
        """
        Parse the lore content into structured data.
        Handles hierarchical format with main categories and subcategories.
        """
        # Process character profiles
        self._parse_character_profiles(content)
        
        # Process world history and lore
        self._parse_world_history(content)
        
        # Process items and quests
        self._parse_items_and_quests(content)
    
    def _parse_character_profiles(self, content: str) -> None:
        """Parse character profiles from the content.
        
        Extracts character information including name, backstory, personality,
        and their connections to items and quests.
        
        Args:
            content: Raw lore text content to parse
        """
        # Look for character profile sections with more flexible pattern matching
        # This improved pattern handles both uppercase and mixed case character names
        # and accounts for variations in formatting
        character_pattern = r'([A-Z][A-Za-z, ]+)\n•\s*Backstory\s*&?\s*Role:\s*(.*?)•\s*Personality\s*&?\s*Motivations:\s*(.*?)(?:•\s*Item\s*&?\s*Quest Connections:|•\s*Relationships:)'
        character_sections = re.findall(character_pattern, content, re.DOTALL)
        
        for name, backstory, personality in character_sections:
            name = name.strip()
            backstory = backstory.strip()
            personality = personality.strip()
            
            # Extract item and quest connections if available
            # Improved pattern with more flexible matching for section headers
            item_quest_pattern = r'•\s*Item\s*&?\s*Quest Connections:(.*?)(?:_{10,}|$)'
            # Use a safer approach to find content after the character name
            name_pos = content.find(name)
            if name_pos >= 0:
                search_content = content[name_pos:]
                item_quest_match = re.search(item_quest_pattern, search_content, re.DOTALL)
            else:
                item_quest_match = None
            
            item_connections = ""
            quest_connections = ""
            if item_quest_match:
                item_quest_text = item_quest_match.group(1).strip()
                
                # Further parse items and quests
                item_pattern = r'•\s*Potential Items:(.*?)(?:•\s*Quests:|$)'
                item_match = re.search(item_pattern, item_quest_text, re.DOTALL)
                if item_match:
                    item_connections = item_match.group(1).strip()
                
                quest_pattern = r'•\s*Quests:(.*?)(?:$)'
                quest_match = re.search(quest_pattern, item_quest_text, re.DOTALL)
                if quest_match:
                    quest_connections = quest_match.group(1).strip()
            
            # Create character profile
            self.lore_data["characters"][name] = {
                "backstory": backstory,
                "personality": personality,
                "item_connections": item_connections,
                "quest_connections": quest_connections
            }
            
            self.characters.append(name)
        
        # Also look for more comprehensive character profiles
        expanded_char_pattern = r'([A-Za-z, ]+)\n•\s*Role:\s*(.*?)•\s*Backstory:\s*(.*?)•\s*Personality:\s*(.*?)•\s*Relationships:\s*(.*?)•\s*Significance in Lore:\s*(.*?)(?:_{10,}|$)'
        expanded_char_sections = re.findall(expanded_char_pattern, content, re.DOTALL)
        
        for name, role, backstory, personality, relationships, significance in expanded_char_sections:
            name = name.strip()
            
            # If character already exists from first pass, enhance it
            if name in self.lore_data["characters"]:
                self.lore_data["characters"][name].update({
                    "role": role.strip(),
                    "relationships": relationships.strip(),
                    "significance": significance.strip()
                })
            else:
                # Create new character entry
                self.lore_data["characters"][name] = {
                    "role": role.strip(),
                    "backstory": backstory.strip(),
                    "personality": personality.strip(),
                    "relationships": relationships.strip(),
                    "significance": significance.strip()
                }
                
                if name not in self.characters:
                    self.characters.append(name)
    
    def _parse_world_history(self, content: str) -> None:
        """Parse world history and lore from the content."""
        # Look for world overview
        world_pattern = r'The World of Fangen\n•\s*Overview:\s*(.*?)(?:Key Historical Events|\n\n)'
        world_match = re.search(world_pattern, content, re.DOTALL)
        if world_match:
            self.lore_data["world"]["Overview"] = world_match.group(1).strip()
        
        # Parse historical events
        events_pattern = r'Key Historical Events\n(•\s*[^•]+)'
        events_match = re.search(events_pattern, content, re.DOTALL)
        if events_match:
            events_text = events_match.group(1)
            event_items = re.findall(r'•\s*([^:]+):\s*([^•]+)', events_text, re.DOTALL)
            
            for event_name, event_desc in event_items:
                self.lore_data["events"][event_name.strip()] = event_desc.strip()
        
        # Parse elemental and mystical themes
        themes_pattern = r'Elemental and Mystical Themes\n(•\s*[^•]+)'
        themes_match = re.search(themes_pattern, content, re.DOTALL)
        if themes_match:
            themes_text = themes_match.group(1)
            theme_items = re.findall(r'•\s*([^:]+):\s*([^•]+)', themes_text, re.DOTALL)
            
            for theme_name, theme_desc in theme_items:
                self.lore_data["themes"][theme_name.strip()] = theme_desc.strip()
        
        # Parse cultural and social dynamics
        culture_pattern = r'Cultural and Social Dynamics\n(•\s*[^•]+)'
        culture_match = re.search(culture_pattern, content, re.DOTALL)
        if culture_match:
            culture_text = culture_match.group(1)
            culture_items = re.findall(r'•\s*([^:]+):\s*([^•]+)', culture_text, re.DOTALL)
            
            for faction_name, faction_desc in culture_items:
                self.lore_data["factions"][faction_name.strip()] = faction_desc.strip()
    
    def _parse_items_and_quests(self, content: str) -> None:
        """Parse items and quests from the content."""
        # Look for item crafting sections
        item_pattern = r'Item Crafting & Evolution:\s*(.*?)(?:\d\.\s*Quest Narratives:|$)'
        item_match = re.search(item_pattern, content, re.DOTALL)
        if item_match:
            item_text = item_match.group(1)
            
            # Parse item tiers
            tier_pattern = r'•\s*([^:]+):\s*([^•]+)'
            tier_items = re.findall(tier_pattern, item_text, re.DOTALL)
            
            for tier_name, tier_desc in tier_items:
                self.lore_data["items"][tier_name.strip()] = tier_desc.strip()
            
            # Extract specific item examples from the text
            item_examples = re.findall(r'((?:Ape\'s Wrath|Wagami\'s Catalyst|Shokei\'s Maw|Moon Blade|Seigo\'s Rampart|Miyou\'s Insight Amulet|Kagitada\'s Lock|Paper\'s Edge|Paper Reaver|Alpha Empress\'s Sigil|Voidforged Relic|Inferno Fang|Emberdust Vial|Solar Fang)[^,.]*)', content)
            
            for item in item_examples:
                if item.strip() not in self.items:
                    self.items.append(item.strip())
                    
                    # Try to determine rarity
                    rarity = "Normal"
                    if "Legendary" in content[content.find(item)-100:content.find(item)+100]:
                        rarity = "Legendary"
                    elif "Rare" in content[content.find(item)-100:content.find(item)+100]:
                        rarity = "Rare"
                    
                    self.lore_data["items"][item.strip()] = {
                        "name": item.strip(),
                        "rarity": rarity,
                        "description": "An item from the world of Fangen."
                    }
        
        # Look for quest narrative sections
        quest_pattern = r'Quest Narratives:\s*(.*?)(?:\d\.\s*|$)'
        quest_match = re.search(quest_pattern, content, re.DOTALL)
        if quest_match:
            quest_text = quest_match.group(1)
            
            # Parse quest themes
            theme_pattern = r'•\s*([^:]+):\s*([^•]+)'
            theme_items = re.findall(theme_pattern, quest_text, re.DOTALL)
            
            for theme_name, theme_desc in theme_items:
                self.lore_data["quests"][theme_name.strip()] = theme_desc.strip()
        
        # Look for specific quest examples
        quest_titles = re.findall(r'Quest: ([^\n]+)', content)
        for title in quest_titles:
            if title.strip() not in self.quests:
                self.quests.append(title.strip())
                
                # Try to find quest description
                quest_desc_pattern = f'Quest: {re.escape(title)}(.*?)(?:Scene \d+:|$)'
                quest_desc_match = re.search(quest_desc_pattern, content, re.DOTALL)
                
                if quest_desc_match:
                    self.lore_data["quests"][title.strip()] = {
                        "title": title.strip(),
                        "description": quest_desc_match.group(1).strip(),
                        "scenes": self._parse_quest_scenes(content, title)
                    }
    
    def _parse_quest_scenes(self, content: str, quest_title: str) -> List[Dict]:
        """Parse quest scenes for a specific quest.
        
        Extracts scene information including settings, dialogues, and player choices
        for a given quest from the lore content.
        
        Args:
            content: Raw lore text content to parse
            quest_title: Title of the quest to parse scenes for
            
        Returns:
            List of dictionaries containing scene data
        """
        scenes = []
        
        # Find all scenes in this quest with improved pattern matching
        # This pattern is more robust to variations in formatting and handles scene transitions better
        scene_pattern = f'Quest:\\s*{re.escape(quest_title)}.*?Scene\\s*(\\d+):\\s*([^\n]+)(.*?)(?:Scene\\s*\\d+:|Your\\s*Choice:|Epilogue:|$)'
        scene_matches = re.findall(scene_pattern, content, re.DOTALL)
        
        for scene_num, scene_title, scene_content in scene_matches:
            # Parse scene setting with improved pattern
            setting_pattern = r'Setting:\s*(.*?)(?:[A-Z][a-z]+\s*:|$)'
            setting_match = re.search(setting_pattern, scene_content, re.DOTALL)
            setting = setting_match.group(1).strip() if setting_match else ""
            
            # Parse NPC dialogues with improved pattern
            npc_dialogues = {}
            npc_pattern = r'([A-Za-z, ]+)(?:\(.*?\))?:\s*"([^"]+)"'
            npc_matches = re.findall(npc_pattern, scene_content, re.DOTALL)
            
            for npc, dialogue in npc_matches:
                npc_dialogues[npc.strip()] = dialogue.strip()
            
            # Parse player choices with improved pattern
            choices = []
            choice_pattern = r'•\s*Option\s*(\d+[A-Z]?):\s*([^\n]+)(?:\nPlayer:\s*"([^"]+)")?\s*Outcome:(.*?)(?:•\s*Option\s*\d+[A-Z]?:|$)'
            choice_matches = re.findall(choice_pattern, content, re.DOTALL)
            
            for choice_id, choice_desc, player_dialogue, outcome in choice_matches:
                # Parse inventory updates
                inv_updates = []
                inv_pattern = r'\[INV_UPDATE: ([^\]]+)\]'
                inv_matches = re.findall(inv_pattern, outcome, re.DOTALL)
                
                for inv_update in inv_matches:
                    inv_updates.append(inv_update.strip())
                
                choices.append({
                    "id": choice_id,
                    "description": choice_desc.strip(),
                    "player_dialogue": player_dialogue.strip(),
                    "outcome": outcome.strip(),
                    "inventory_updates": inv_updates
                })
            
            scenes.append({
                "number": scene_num,
                "title": scene_title.strip(),
                "setting": setting,
                "npc_dialogues": npc_dialogues,
                "choices": choices
            })
        
        return scenes
    
    def get_categories(self) -> List[str]:
        """Get all available lore categories."""
        # Return only categories that have content
        return [category for category, entries in self.lore_data.items() if entries]
    
    def get_characters(self) -> List[str]:
        """Get all available characters."""
        return sorted(self.characters)
    
    def get_items(self) -> List[str]:
        """Get all available items."""
        return sorted(self.items)
    
    def get_quests(self) -> List[str]:
        """Get all available quests."""
        return sorted(self.quests)
    
    def get_entries_by_category(self, category: str) -> List[str]:
        """Get all entries for a specific category."""
        if category.lower() in self.lore_data:
            return sorted(list(self.lore_data[category.lower()].keys()))
        return []
    
    def get_entry_content(self, entry_name: str) -> Optional[Dict]:
        """Get the content of a specific lore entry."""
        for category, entries in self.lore_data.items():
            if entry_name in entries:
                return entries[entry_name]
        return None
    
    def get_character_info(self, character_name: str) -> Optional[Dict]:
        """Get information about a specific character."""
        if character_name in self.lore_data["characters"]:
            return self.lore_data["characters"][character_name]
        return None
    
    def get_item_info(self, item_name: str) -> Optional[Dict]:
        """Get information about a specific item."""
        if item_name in self.lore_data["items"]:
            return self.lore_data["items"][item_name]
        return None
    
    def get_quest_info(self, quest_name: str) -> Optional[Dict]:
        """Get information about a specific quest."""
        if quest_name in self.lore_data["quests"]:
            return self.lore_data["quests"][quest_name]
        return None
    
    def search_lore(self, query: str) -> Dict[str, List[str]]:
        """Search the lore for entries matching the query."""
        results = {}
        
        for category, entries in self.lore_data.items():
            category_results = []
            for name, content in entries.items():
                # For string content
                if isinstance(content, str) and query.lower() in content.lower():
                    category_results.append(name)
                # For dictionary content
                elif isinstance(content, dict):
                    found = False
                    for key, value in content.items():
                        if isinstance(value, str) and query.lower() in value.lower():
                            found = True
                            break
                    if found or query.lower() in name.lower():
                        category_results.append(name)
            
            if category_results:
                results[category] = category_results
        
        return results
    
    def get_character_dialogue(self, character_name: str, context: str) -> str:
        """Generate a contextual dialogue for a character based on their personality."""
        if character_name not in self.lore_data["characters"]:
            return f"I am {character_name}. What do you want to know?"
        
        character = self.lore_data["characters"][character_name]
        
        # Extract personality traits
        personality = character.get("personality", "")
        if isinstance(personality, str):
            traits = re.findall(r'([a-z]+)', personality.lower())
        else:
            traits = []
        
        # Generate dialogue based on traits and context
        if "playful" in traits or "quirky" in traits or "eccentric" in traits:
            return f"*with a mischievous grin* Ah, curious about {context}, are you? Well, let me tell you something interesting..."
        elif "stoic" in traits or "cold" in traits or "methodical" in traits:
            return f"*stares intently* {context}? I will speak of it, though few deserve such knowledge."
        elif "arrogant" in traits or "cunning" in traits:
            return f"*smirks confidently* You wish to know of {context}? Most wouldn't even comprehend it, but perhaps you might..."
        elif "fierce" in traits or "protective" in traits or "loyal" in traits:
            return f"*stands tall* {context} is a matter of honor and duty. Listen carefully to what I tell you."
        else:
            return f"You ask about {context}? Very well, I shall share what I know."
    
    def get_related_characters(self, entry_name: str) -> List[str]:
        """Find characters related to a specific lore entry."""
        related = []
        entry_content = self.get_entry_content(entry_name)
        
        if not entry_content:
            return related
            
        entry_str = ""
        if isinstance(entry_content, str):
            entry_str = entry_content
        elif isinstance(entry_content, dict):
            entry_str = json.dumps(entry_content)
        
        # Check which characters are mentioned in the entry
        for character in self.characters:
            if character in entry_str:
                related.append(character)
                
        return related