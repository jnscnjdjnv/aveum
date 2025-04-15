# Aveum Mining Bot

A Python-based bot for the Aveum platform that can perform mining and auto-liking functions.

## Features

- **Mining Mode**: Automatically mines AVEUM tokens
- **Auto-Like Mode**: Automatically likes users to earn rewards
- **User Interface**: Terminal-based UI with real-time status updates
- **Authentication**: Secure login with token management

## Requirements

- Python 3.7+
- Required packages (install using `pip install -r requirements.txt`):
  - aiohttp
  - blessed
  - python-dotenv

## Installation

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Aveum credentials:
   ```
   AVEUM_EMAIL=your_email@example.com
   AVEUM_PASSWORD=your_password
   ```

## Usage

Run the bot with:

```
python aveum_bot.py
```

### Controls

- Press `m` to toggle between Mining and Auto-Like modes
- Press `r` to refresh the authentication token
- Press `q` or `Ctrl+C` to quit the bot

## Disclaimer

This bot is for educational purposes only. Use at your own risk. The developers are not responsible for any consequences of using this bot.

## License

MIT 
