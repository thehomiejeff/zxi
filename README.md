# zxi
# ChuzoBot: The Lore-Driven Telegram Companion

ChuzoBot is a Telegram bot that brings the rich world of Fangen to life through interactive storytelling, character interactions, and quest-driven gameplay. This bot serves as a companion for users to explore the elemental forces, legendary characters, and ancient mysteries of the Fangen universe.

## 🌟 Features

### 📜 Quest System
- **Interactive Storylines**: Experience branching narratives where your choices matter
- **Decision-Based Outcomes**: Different choices lead to different rewards and story developments
- **Inventory Integration**: Items earned in quests can be used in crafting and future adventures

### 👥 Character Interactions
- **Personality-Driven Dialogue**: Each character responds based on their unique personality and backstory
- **Relationship Building**: Build connections with characters like Hand of Diamond, Zero, Wagami, and more
- **Lore Discovery**: Learn more about the world through conversations with its inhabitants

### 🎒 Inventory & Crafting
- **Item Collection**: Gather components throughout your adventures
- **Tiered Crafting**: Craft items of increasing rarity (Normal → Rare → Legendary)
- **Recipe Discovery**: Unlock new crafting recipes as you progress through quests

### 📚 Lore Exploration
- **World History**: Discover the rich history of Fangen and its elemental forces
- **Character Backstories**: Learn about the motivations and histories of key figures
- **Mystical Themes**: Explore the elemental duality, legacy, and transformation themes

### 🔄 Recent Improvements
- **Enhanced Error Handling**: Robust error handling with proper transaction management
- **Improved Logging System**: Comprehensive logging with rotation and better formatting
- **Optimized Lore Parsing**: More flexible regex patterns for better content extraction
- **Better Documentation**: Detailed docstrings and improved code comments
- **User Experience Enhancements**: Better error messages and Markdown formatting support

## 🚀 Getting Started

### Prerequisites
- Python 3.7+
- A Telegram account
- A Telegram Bot Token (obtained from [BotFather](https://t.me/botfather))

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/chuzobot.git
cd chuzobot
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your configuration:
```
BOT_TOKEN=your_telegram_bot_token
BOT_NAME=ChuzoBot
BOT_USERNAME=your_bot_username
LOG_LEVEL=INFO
DB_TYPE=sqlite
DB_NAME=fangen.db
LORE_FILE=data/lore.txt
```

4. Run the bot:
```bash
python main.py
```

5. Start interacting with your bot on Telegram by messaging it!

## 📋 Commands

### Quest Commands
- `/quests` - Browse available quests
- `/startquest [name]` - Begin a specific quest
- `/currentquest` - View your active quest
- `/abandonquest` - Abandon your current quest

### Character Interactions
- `/interact` - Speak with characters from Fangen
- `/interact [name]` - Speak with a specific character

### Inventory & Crafting
- `/inventory` - View your collected items
- `/craft` - View available crafting recipes
- `/craft [item]` - Craft a specific item

### Lore Exploration
- `/lore` - Browse the world's lore by category
- `/search [query]` - Search for specific lore entries
- `/discover` - Find something new in the world

### User Features
- `/status` - Check your exploration progress
- `/collection` - View lore entries you've discovered
- `/settings` - Adjust your preferences

## 🌍 The World of Fangen

Fangen is a realm where elemental forces are not just natural phenomena but living essences interwoven with the destiny of its inhabitants. The world's history is marked by ancient empires, cataclysmic events, and a continuous struggle between order and chaos.

Key elements of the world include:

- **Elemental Forces**: Diamond, Paper, Fire, and other elements exist as physical manifestations
- **The Alpha Empire**: A powerful regime led by the Alpha Empress
- **The Great Wormhole**: A portal between dimensions, accidentally reopened by Wagami
- **Legendary Beings**: Characters like Hand of Diamond, Fist of Ape, and the Legendary Beasts

## 📁 Project Structure

```
chuzobot/
├── main.py                 # Main entry point
├── config.py               # Configuration file
├── .env                    # Environment variables
├── .gitignore              # Git ignore file
├── .gitattributes          # Git attributes file
├── requirements.txt        # Project dependencies
├── data/                   # Data directory
│   ├── lore.txt            # Lore data file
│   └── .gitkeep            # Placeholder
├── handlers/               # Command handlers
│   ├── __init__.py         # Package initializer
│   ├── lore_handlers.py    # Lore-related command handlers
│   └── quest_handlers.py   # Quest-related command handlers
├── utils/                  # Utility modules
│   ├── __init__.py         # Package initializer
│   ├── database.py         # Database utility
│   ├── logger.py           # Logging utility
│   ├── fangen_lore_manager.py # Fangen-specific lore manager
│   └── quest_manager.py    # Quest management utility
└── logs/                   # Log files directory (auto-created)
```

## 🛠️ Development

### Adding New Quests

Quests are structured as scenes with choices that affect the narrative progression. To add a new quest:

1. Create a structured quest description in the lore file with scenes, choices, and outcomes
2. Ensure all required items and rewards are properly defined
3. Test the quest flow to ensure all branches work correctly

### Adding New Characters

To add a new character:

1. Add the character profile to the lore file with backstory, personality, and relationships
2. Create dialogue patterns for the character in the FangenLoreManager
3. Test character interactions to ensure they respond appropriately

### Adding New Crafting Recipes

To add a new crafting recipe:

1. Define the recipe in the database with required components and results
2. Add any quest prerequisites if needed
3. Update the lore file with information about the new item

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Special thanks to all the contributors who helped bring the world of Fangen to life
- Inspired by the rich tradition of interactive storytelling and text-based adventures
- Built with [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)

## 📞 Contact

For questions, suggestions, or contributions, please open an issue on this repository or contact the maintainer directly.

---

*"In the world of Fangen, every choice shapes destiny, every element tells a story, and every character holds a piece of the truth."* - Chuzo
