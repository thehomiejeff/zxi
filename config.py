#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration file for ZXI/ChuzoBot
"""

import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_NAME = os.getenv("BOT_NAME", "ZXI")
BOT_USERNAME = os.getenv("BOT_USERNAME", "ZXI")

# Admin configuration
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "bot.log")

# Database configuration
DB_TYPE = os.getenv("DB_TYPE", "sqlite")
DB_NAME = os.getenv("DB_NAME", "fangen.db")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "botuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Lore configuration
LORE_FILE = os.getenv("LORE_FILE", "data/lore.txt")
LORE_CATEGORIES = os.getenv("LORE_CATEGORIES", "characters,locations,events,items,themes,factions,world,quests").split(",")

# Feature toggles
ENABLE_LORE = os.getenv("ENABLE_LORE", "True").lower() == "true"
ENABLE_INTERACTIONS = os.getenv("ENABLE_INTERACTIONS", "True").lower() == "true"
ENABLE_QUESTS = os.getenv("ENABLE_QUESTS", "True").lower() == "true"
ENABLE_CRAFTING = os.getenv("ENABLE_CRAFTING", "True").lower() == "true"

# Message customization
DEFAULT_INTERACTION_TIMEOUT = int(os.getenv("DEFAULT_INTERACTION_TIMEOUT", "3600"))  # Default: 1 hour
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "10"))  # Maximum results to show in search