# Lost & Found Telegram Bot 🔍📦

A Telegram bot that allows users to report lost and found items. All reports are saved to a SQLite database.

## Features

- **Report Lost Items**: Users can report items they've lost
- **Report Found Items**: Users can report items they've found
- **Categories**: 10 item categories (Electronics, Bags & Wallets, Keys, Documents, Clothing, Jewelry, Books, Accessories, Pets, Other)
- **Location Sharing**: Optional GPS location sharing via Telegram
- **Photo Upload**: Optional photo attachment
- **Date Validation**: Ensures dates are in DD.MM.YYYY format
- **SQLite Database**: All reports are stored persistently

## Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Install Dependencies

```bash
cd lostandfound
pip install -r requirements.txt
```

### 3. Configure the Bot

Create a `.env` file in the project root and add your bot token:

```bash
# Create .env file
echo "BOT_TOKEN=your_telegram_bot_token_here" > .env
```

Or manually create a `.env` file with:

```
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 4. Run the Bot

```bash
python bot.py
```

## Usage

### Commands

- `/start` - Start reporting a lost or found item
- `/cancel` - Cancel current report
- `/help` - Show help message

### Flow

#### For Lost Items:
1. Select "I Lost Something"
2. Choose category
3. Describe the item (color, size, specific details)
4. Share location (optional)
5. Enter date lost (DD.MM.YYYY)
6. Upload photo (optional)
7. Set reward

#### For Found Items:
1. Select "I Found Something"
2. Choose category
3. Describe the item (color, size, specific details)
4. Share location (optional)
5. Enter date found (DD.MM.YYYY)
6. Upload photo (optional)
7. Provide contact information

## Database Schema

### LOST_ITEMS Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| user_id | INTEGER | Telegram user ID |
| category | TEXT | Item category |
| description | TEXT | Item description |
| latitude | REAL | GPS latitude (nullable) |
| longitude | REAL | GPS longitude (nullable) |
| location_text | TEXT | Location description (nullable) |
| date_lost | TEXT | Date item was lost |
| photo_file_id | TEXT | Telegram photo file ID (nullable) |
| reward | TEXT | Reward information |
| created_at | TEXT | Timestamp of report |

### FOUND_ITEMS Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| user_id | INTEGER | Telegram user ID |
| category | TEXT | Item category |
| description | TEXT | Item description |
| latitude | REAL | GPS latitude (nullable) |
| longitude | REAL | GPS longitude (nullable) |
| location_text | TEXT | Location description (nullable) |
| date_found | TEXT | Date item was found |
| photo_file_id | TEXT | Telegram photo file ID (nullable) |
| contact_info | TEXT | Contact information |
| created_at | TEXT | Timestamp of report |

## File Structure

```
lostandfound/
├── bot.py           # Main bot logic
├── database.py      # SQLite database operations
├── requirements.txt # Python dependencies
├── README.md        # This file
└── lostandfound.db  # SQLite database (created on first run)
```

## License

MIT License
