# Lost & Found Telegram Bot 🔍📦

A Telegram bot that allows users to report lost and found items. Reports are stored in CSV files, and the bot automatically matches found items with lost ones, notifying owners of potential matches.

## Features

- **Report Lost Items**: Users can report items they've lost
- **Report Found Items**: Users can report items they've found
- **Automatic Matching**: When a found item is registered, the bot searches for similar lost items and lets the finder review potential matches
- **Owner Notifications**: Lost item owners are notified when someone finds a similar item, and can confirm or reject the match
- **Categories**: 14 item categories (Toy, Phone, Laptop/Tablet, Bag/Bagpack, Wallet, Watches, Earphones/Earbuds, Document, Clothing, Jewelry, Glasses/Sunglasses, Keys, Pets, Other)
- **Photo Upload**: Optional photo attachment
- **CSV Storage**: All reports are stored persistently in CSV files

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
4. Upload photo (optional)
5. Set reward

#### For Found Items:
1. Select "I Found Something"
2. Choose category
3. Describe the item (color, size, specific details)
4. Upload photo (optional)
5. Provide contact information
6. Review potential matches with lost items (if any similar lost items exist)

## Data Storage (CSV)

Data is stored in two CSV files, created automatically on first run.

### `lost_items.csv`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment primary key |
| user_id | INTEGER | Telegram user ID |
| category | TEXT | Item category |
| description | TEXT | Item description |
| photo_file_id | TEXT | Telegram photo file ID (may be empty) |
| reward | TEXT | Reward information (may be empty) |
| created_at | TEXT | ISO timestamp of report |
| is_matched | TEXT | `"false"` or ID of the matching found item |

### `found_items.csv`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment primary key |
| user_id | INTEGER | Telegram user ID |
| category | TEXT | Item category |
| description | TEXT | Item description |
| photo_file_id | TEXT | Telegram photo file ID (may be empty) |
| contact_info | TEXT | Contact information (may be empty) |
| created_at | TEXT | ISO timestamp of report |
| is_matched | TEXT | `"false"` or ID of the matching lost item |

## File Structure

```
lostandfound/
├── bot.py            # Main bot logic (ConversationHandler + matching)
├── database.py       # CSV-based data operations
├── requirements.txt  # Python dependencies
├── LOGIC.md          # Detailed bot logic documentation (in Russian)
├── README.md         # This file
├── .env              # Bot token (not committed)
├── .gitignore        # Git ignore rules
├── lost_items.csv    # Lost items data (created on first run)
└── found_items.csv   # Found items data (created on first run)
```

## License

MIT License
