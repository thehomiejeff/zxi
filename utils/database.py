#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced database utility for ChuzoBot
Supporting quests, inventory, and character interactions
"""

import os
import sqlite3
import json
from typing import Dict, List, Tuple, Any, Optional

from utils.logger import get_logger
from config import DB_TYPE, DB_NAME, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD

logger = get_logger(__name__)

class Database:
    """Database handler for ChuzoBot."""
    
    def __init__(self):
        """Initialize the database connection."""
        self.conn = None
        self.db_type = DB_TYPE
        self.db_name = DB_NAME
        
        if self.db_type == "sqlite":
            self._connect_sqlite()
        elif self.db_type == "postgres":
            self._connect_postgres()
        else:
            logger.error(f"Unsupported database type: {self.db_type}")
    
    def _connect_sqlite(self):
        """Connect to SQLite database."""
        try:
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            db_path = os.path.join('data', self.db_name)
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to SQLite database: {db_path}")
        except Exception as e:
            logger.error(f"Error connecting to SQLite database: {e}", exc_info=True)
    
    def _connect_postgres(self):
        """Connect to PostgreSQL database."""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            self.conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            logger.info(f"Connected to PostgreSQL database: {DB_NAME}")
        except ImportError:
            logger.error("psycopg2 not installed. Install it to use PostgreSQL.")
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL database: {e}", exc_info=True)
    
    def setup(self):
        """Set up the database tables."""
        if not self.conn:
            logger.error("Database connection not established")
            return
        
        try:
            cursor = self.conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    settings TEXT
                )
            ''')
            
            # Create interactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    character TEXT,
                    message TEXT,
                    response TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Create user_progress table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_progress (
                    user_id INTEGER,
                    category TEXT,
                    item_name TEXT,
                    discovered BOOLEAN DEFAULT FALSE,
                    discovery_date TIMESTAMP,
                    notes TEXT,
                    PRIMARY KEY (user_id, category, item_name),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Create user_inventory table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_inventory (
                    user_id INTEGER,
                    item_name TEXT,
                    rarity TEXT DEFAULT 'Normal',
                    quantity INTEGER DEFAULT 1,
                    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, item_name),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Create quest_logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quest_logs (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    quest_name TEXT,
                    status TEXT, -- 'in_progress', 'completed', 'abandoned'
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    choices_made TEXT, -- JSON string of choices
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Create decision_logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS decision_logs (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    quest_name TEXT,
                    scene_id TEXT,
                    choice_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Create crafting_recipes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS crafting_recipes (
                    id INTEGER PRIMARY KEY,
                    result_item TEXT,
                    result_rarity TEXT,
                    requirements TEXT, -- JSON string of required items
                    quest_requirements TEXT, -- JSON string of required quest completions or choices
                    description TEXT
                )
            ''')
            
            # Create character_relationships table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS character_relationships (
                    user_id INTEGER,
                    character_name TEXT,
                    relationship_level INTEGER DEFAULT 0,
                    last_interaction TIMESTAMP,
                    notes TEXT,
                    PRIMARY KEY (user_id, character_name),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            self.conn.commit()
            logger.info("Database tables set up successfully")
            
            # Add initial crafting recipes
            self._add_initial_recipes()
            
        except Exception as e:
            logger.error(f"Error setting up database tables: {e}", exc_info=True)
    
    def _add_initial_recipes(self):
        """Add initial crafting recipes based on lore."""
        recipes = [
            {
                "result_item": "Inferno Fang",
                "result_rarity": "Rare",
                "requirements": json.dumps({"Emberdust Vial": 1, "Relic Shard": 1}),
                "quest_requirements": json.dumps({"The Ember's Awakening": {"scene3": "3A"}}),
                "description": "A blazing weapon forged from the essence of fire."
            },
            {
                "result_item": "Enhanced Inferno Fang",
                "result_rarity": "Rare",
                "requirements": json.dumps({"Emberdust Vial": 1, "Relic Shard": 1, "Data Chip": 1, "Secret Note": 1}),
                "quest_requirements": json.dumps({"The Ember's Awakening": {"scene3": "3B"}}),
                "description": "An enhanced version of the Inferno Fang with the 'Ember Surge' ability."
            },
            {
                "result_item": "Solar Fang",
                "result_rarity": "Legendary",
                "requirements": json.dumps({"Diamond Shard": 1, "Mystic Fragment": 1, "Visionary Pendant": 1}),
                "quest_requirements": json.dumps({"The Shattered Relics of Fate": {"scene4": "4A"}}),
                "description": "A legendary weapon that radiates with the unified power of all elemental forces."
            },
            {
                "result_item": "Paper's Edge",
                "result_rarity": "Rare",
                "requirements": json.dumps({"Paper Fragment": 2}),
                "quest_requirements": json.dumps({}),
                "description": "A razor-sharp weapon crafted from the essence of the Paper element."
            },
            {
                "result_item": "Ape's Wrath",
                "result_rarity": "Normal",
                "requirements": json.dumps({}),
                "quest_requirements": json.dumps({}),
                "description": "A basic weapon that embodies the raw physical power of the Ape element."
            }
        ]
        
        try:
            cursor = self.conn.cursor()
            
            for recipe in recipes:
                # Check if recipe already exists
                existing = self.execute_query(
                    "SELECT id FROM crafting_recipes WHERE result_item = ?",
                    (recipe["result_item"],)
                )
                
                if not existing:
                    cursor.execute(
                        "INSERT INTO crafting_recipes (result_item, result_rarity, requirements, quest_requirements, description) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (recipe["result_item"], recipe["result_rarity"], recipe["requirements"], 
                         recipe["quest_requirements"], recipe["description"])
                    )
            
            self.conn.commit()
            logger.info("Initial crafting recipes added successfully")
        except Exception as e:
            logger.error(f"Error adding initial recipes: {e}", exc_info=True)
    
    def execute_query(self, query: str, params: Tuple = ()) -> Optional[List[Dict]]:
        """Execute a database query."""
        if not self.conn:
            logger.error("Database connection not established")
            return None
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            
            if query.strip().upper().startswith(("SELECT", "PRAGMA")):
                if self.db_type == "sqlite":
                    results = [dict(row) for row in cursor.fetchall()]
                else:
                    results = cursor.fetchall()
                return results
            else:
                self.conn.commit()
                return None
        except Exception as e:
            logger.error(f"Error executing query: {e}", exc_info=True)
            return None
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def can_craft_item(self, user_id: int, item_name: str) -> Tuple[bool, str, Dict]:
        """Check if a user can craft a specific item."""
        # Get recipe
        recipe = self.execute_query(
            "SELECT * FROM crafting_recipes WHERE result_item = ?",
            (item_name,)
        )
        
        if not recipe:
            return False, f"No recipe found for {item_name}.", {}
        
        recipe = recipe[0]
        
        # Check inventory requirements
        requirements = json.loads(recipe["requirements"])
        user_inventory = self.execute_query(
            "SELECT item_name, quantity FROM user_inventory WHERE user_id = ?",
            (user_id,)
        )
        
        if not user_inventory:
            user_inventory = []
        
        # Convert to dict for easier lookup
        inventory_dict = {item["item_name"]: item["quantity"] for item in user_inventory}
        
        missing_items = []
        for req_item, req_quantity in requirements.items():
            if req_item not in inventory_dict or inventory_dict[req_item] < req_quantity:
                missing_items.append(f"{req_item} x{req_quantity}")
        
        # Check quest requirements
        quest_requirements = json.loads(recipe["quest_requirements"])
        
        for quest_name, scene_choices in quest_requirements.items():
            # Check if quest is completed
            quest_completed = self.execute_query(
                "SELECT * FROM user_progress WHERE user_id = ? AND category = 'quests' AND item_name = ? AND discovered = TRUE",
                (user_id, quest_name)
            )
            
            if not quest_completed:
                missing_items.append(f"Quest: {quest_name}")
                continue
            
            # Check specific choices if needed
            for scene, choice in scene_choices.items():
                choice_made = self.execute_query(
                    "SELECT * FROM decision_logs WHERE user_id = ? AND quest_name = ? AND scene_id = ? AND choice_id = ?",
                    (user_id, quest_name, scene, choice)
                )
                
                if not choice_made:
                    missing_items.append(f"Choice: {scene}-{choice} in {quest_name}")
        
        if missing_items:
            return False, f"You are missing the following requirements to craft {item_name}:", {
                "missing": missing_items,
                "recipe": recipe
            }
        
        return True, f"You can craft {item_name}!", {
            "recipe": recipe,
            "inventory": inventory_dict
        }
    
    def craft_item(self, user_id: int, item_name: str) -> Tuple[bool, str]:
        """Craft an item for a user."""
        can_craft, message, details = self.can_craft_item(user_id, item_name)
        
        if not can_craft:
            return False, message
        
        try:
            # Consume required items
            recipe = details["recipe"]
            requirements = json.loads(recipe["requirements"])
            
            for req_item, req_quantity in requirements.items():
                self.execute_query(
                    "UPDATE user_inventory SET quantity = quantity - ? WHERE user_id = ? AND item_name = ?",
                    (req_quantity, user_id, req_item)
                )
            
            # Add crafted item
            result_rarity = recipe["result_rarity"]
            
            # Check if item already exists in inventory
            existing_item = self.execute_query(
                "SELECT * FROM user_inventory WHERE user_id = ? AND item_name = ?",
                (user_id, item_name)
            )
            
            if existing_item:
                self.execute_query(
                    "UPDATE user_inventory SET quantity = quantity + 1 WHERE user_id = ? AND item_name = ?",
                    (user_id, item_name)
                )
            else:
                self.execute_query(
                    "INSERT INTO user_inventory (user_id, item_name, rarity, quantity) VALUES (?, ?, ?, 1)",
                    (user_id, item_name, result_rarity)
                )
            
            return True, f"Successfully crafted {item_name} ({result_rarity})!"
        except Exception as e:
            logger.error(f"Error crafting item: {e}", exc_info=True)
            return False, f"Error crafting item: {str(e)}"