import os
import time
import random
import json
import asyncio
import aiohttp
import blessed
import dotenv
import secrets
from datetime import datetime

# Debug mode
DEBUG = True

# Load environment variables
dotenv.load_dotenv()

# Debug: Print environment variables
if DEBUG:
    print("DEBUG: Environment variables loaded:")
    print(f"AVEUM_EMAIL: {os.getenv('AVEUM_EMAIL')}")
    print(f"AVEUM_PASSWORD: {'*' * len(os.getenv('AVEUM_PASSWORD', '')) if os.getenv('AVEUM_PASSWORD') else 'None'}")
    print(f"Current working directory: {os.getcwd()}")
    print(f".env file exists: {os.path.exists('.env')}")
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            print(f".env file contents: {f.read()}")

# Constants
API_BASE_URL = 'https://api.aveum.io'
API_ENDPOINTS = {
    'login': '/users/login',
    'startHub': '/users/start-hub',
    'stopHub': '/users/stop-hub',
    'hubStatus': '/users/hub-status',
    'profile': '/users/profile',
    'checkBan': '/users/check-ban',
    'claimReward': '/users/claim-reward',
    'discoverFeed': '/users/discover-feed',
    'discoverOnlineUsers': '/users/discover-online-users',
    'toggleLike': '/users/toggle-like/'
}

ANDROID_DEVICE_MODELS = [
    'SM-G9750', 'SM-G988B', 'SM-G973F', 'SM-G975F', 'SM-N975F',
    'SM-A515F', 'SM-A715F', 'SM-A516B', 'SM-A526B', 'SM-A536E',
    'Pixel 6', 'Pixel 6 Pro', 'Pixel 7', 'Pixel 7 Pro', 'Pixel 8',
    'OnePlus 9', 'OnePlus 10 Pro', 'OnePlus 11', 'OnePlus Nord 3',
    'Redmi Note 12', 'Redmi Note 11', 'POCO F5', 'POCO X5 Pro',
    'Vivo X90', 'Vivo V25', 'Vivo Y35', 'Oppo Reno 8', 'Oppo Find X5'
]

ANDROID_VERSIONS = ['10', '11', '12', '13']

BOT_MODE = {
    'MINING': 'mining',
    'AUTO_LIKE': 'auto_like'
}

# Global variables
current_bot_mode = BOT_MODE['MINING']
auto_like_running = False
processed_post_ids = set()
processed_user_ids = set()
total_liked = 0

# Create UI
term = blessed.Terminal()

# UI state variables
user_info_content = 'Loading user info...'
mining_status_content = 'Loading mining status...'
auto_like_status_content = 'Auto Like status will appear here when active'
log_messages = []
current_mode = 'MINING'

# Authentication class
class Auth:
    def __init__(self):
        self.token = None
    
    async def login(self):
        try:
            log_message('Logging in to Aveum...', 'info')
            
            if not os.getenv('AVEUM_EMAIL') or not os.getenv('AVEUM_PASSWORD'):
                log_message('Error: Missing email or password in .env file!', 'error')
                os._exit(1)
            
            payload = get_login_payload()
            headers = get_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_BASE_URL}{API_ENDPOINTS['login']}", 
                    json=payload, 
                    headers=headers
                ) as response:
                    data = await response.json()
                    self.token = data['token']
                    log_message('Login successful! Token received.', 'success')
                    return True
        except Exception as error:
            log_message(f'Login failed: {str(error)}', 'error')
            return False
    
    def get_token(self):
        return self.token
    
    def is_authenticated(self):
        return bool(self.token)

# Create auth instance
auth = Auth()

# Helper functions
def generate_random_device_id():
    return secrets.token_hex(8)

def get_random_device_model():
    return random.choice(ANDROID_DEVICE_MODELS)

def get_random_android_version():
    return random.choice(ANDROID_VERSIONS)

def get_random_delay(min_val, max_val):
    return random.randint(min_val, max_val)

def get_headers(token=None):
    headers = {
        'User-Agent': 'okhttp/4.9.2',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip',
        'Content-Type': 'application/json'
    }
    
    if token:
        headers['authorization'] = f'Bearer {token}'
    
    return headers

def get_login_payload():
    device_id = generate_random_device_id()
    device_model = get_random_device_model()
    platform_version = get_random_android_version()
    
    log_message(f'Using random device: {device_model} (ID: {device_id}, Android {platform_version})', 'info')
    
    return {
        'email': os.getenv('AVEUM_EMAIL'),
        'password': os.getenv('AVEUM_PASSWORD'),
        'language': "en",
        'device_id': device_id,
        'device_model': device_model,
        'platform': "android",
        'platform_version': platform_version,
        'version': "1.0.25",
        'ip_address': "180.249.164.195"
    }

def format_time_remaining(hours):
    total_seconds = int(hours * 3600)
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    
    return f"{h:02d}:{m:02d}:{s:02d}"

def log_message(message, type='info'):
    global log_messages
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    if type == 'error':
        colored_message = f"{term.red}[{timestamp}] {message}{term.normal}"
    elif type == 'success':
        colored_message = f"{term.green}[{timestamp}] {message}{term.normal}"
    elif type == 'warning':
        colored_message = f"{term.yellow}[{timestamp}] {message}{term.normal}"
    else:
        colored_message = f"{term.white}[{timestamp}] {message}{term.normal}"
    
    log_messages.append(colored_message)
    if len(log_messages) > 100:  # Keep only the last 100 messages
        log_messages = log_messages[-100:]
    
    render_ui()

# API functions
async def get_user_profile():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE_URL}{API_ENDPOINTS['profile']}", 
                headers=get_headers(auth.get_token())
            ) as response:
                data = await response.json()
                return data
    except Exception as error:
        log_message(f'Error fetching user profile: {str(error)}', 'error')
        return None

async def check_user_ban():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE_URL}{API_ENDPOINTS['checkBan']}", 
                headers=get_headers(auth.get_token())
            ) as response:
                data = await response.json()
                return data
    except Exception as error:
        log_message(f'Error checking ban status: {str(error)}', 'error')
        return {'banned': False}

async def start_hub_mining():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}{API_ENDPOINTS['startHub']}", 
                json={}, 
                headers=get_headers(auth.get_token())
            ) as response:
                data = await response.json()
                log_message('✅ Hub mining started successfully!', 'success')
                log_message(f"Start time: {data['startTime']}", 'info')
                return data
    except Exception as error:
        log_message(f'❌ Error starting hub mining: {str(error)}', 'error')
        return None

async def claim_reward():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}{API_ENDPOINTS['claimReward']}", 
                json={}, 
                headers=get_headers(auth.get_token())
            ) as response:
                data = await response.json()
                log_message('✅ Reward claimed successfully!', 'success')
                if data and 'reward' in data:
                    log_message(f"Claimed {data['reward']} AVEUM!", 'success')
                return data
    except Exception as error:
        log_message(f'❌ Error claiming reward: {str(error)}', 'error')
        return None

async def get_hub_status():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE_URL}{API_ENDPOINTS['hubStatus']}", 
                headers=get_headers(auth.get_token())
            ) as response:
                data = await response.json()
                return data
    except Exception as error:
        log_message(f'Error fetching hub status: {str(error)}', 'error')
        return None

async def get_discover_feed(page=1, limit=20):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE_URL}{API_ENDPOINTS['discoverFeed']}?page={page}&limit={limit}", 
                headers=get_headers(auth.get_token())
            ) as response:
                data = await response.json()
                
                # Log the structure for debugging
                log_message(f"Received discover feed data. Response structure: {', '.join(data.keys())}", 'info')
                
                return data
    except Exception as error:
        log_message(f'Error fetching discover feed: {str(error)}', 'error')
        return None

async def get_discover_online_users(page=1, limit=20):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE_URL}{API_ENDPOINTS['discoverOnlineUsers']}?page={page}&limit={limit}", 
                headers=get_headers(auth.get_token())
            ) as response:
                data = await response.json()
                return data
    except Exception as error:
        log_message(f'Error fetching online users: {str(error)}', 'error')
        return None

async def toggle_like(user_id):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}{API_ENDPOINTS['toggleLike']}{user_id}", 
                json={}, 
                headers=get_headers(auth.get_token())
            ) as response:
                data = await response.json()
                log_message(f"✅ Successfully liked user ID: {user_id}", 'success')
                return data
    except Exception as error:
        log_message(f"❌ Error liking user ID {user_id}: {str(error)}", 'error')
        return None

# UI update functions
async def update_user_info():
    global user_info_content
    try:
        if not auth.is_authenticated():
            user_info_content = f"{term.red}Not logged in. Please check credentials.{term.normal}"
            render_ui()
            return
        
        profile_data = await get_user_profile()
        ban_status = await check_user_ban()
        
        if not profile_data:
            user_info_content = f"{term.red}Failed to fetch user data{term.normal}"
            render_ui()
            return
        
        ban_status_text = f"{term.red}BANNED{term.normal}" if profile_data.get('ban') else f"{term.green}NOT BANNED{term.normal}"
        
        user_info_content = (
            f"{term.yellow}Username:{term.normal} {term.green}{profile_data.get('username')}{term.normal}\n" +
            f"{term.yellow}Email:{term.normal} {term.green}{profile_data.get('email')}{term.normal}\n" +
            f"{term.yellow}Total Reward:{term.normal} {term.green}{profile_data.get('all_reward')} AVEUM{term.normal}\n" +
            f"{term.yellow}Ban Status:{term.normal} {ban_status_text}"
        )
        
        render_ui()
    except Exception as error:
        log_message(f'Error updating user info: {str(error)}', 'error')

async def update_mining_status():
    global mining_status_content
    try:
        if not auth.is_authenticated() or current_bot_mode != BOT_MODE['MINING']:
            return
        
        hub_status = await get_hub_status()
        
        if not hub_status:
            mining_status_content = f"{term.red}Failed to fetch mining status{term.normal}"
            render_ui()
            return
        
        if hub_status.get('isHub'):
            if hub_status.get('remainingTime', 0) <= 0.001:
                log_message('Mining complete! Claiming reward...', 'success')
                await claim_reward()
                log_message('Starting new mining session...', 'info')
                await start_hub_mining()
                asyncio.create_task(asyncio.sleep(2, update_mining_status()))
                return
            
            mining_status_content = (
                f"{term.yellow}Mining Status:{term.normal} {term.green}ACTIVE{term.normal}\n" +
                f"{term.yellow}Start Time:{term.normal} {term.green}{hub_status.get('startTime')}{term.normal}\n" +
                f"{term.yellow}Daily Reward:{term.normal} {term.green}{hub_status.get('dailyReward')} AVEUM{term.normal}\n" +
                f"{term.yellow}Current Earning:{term.normal} {term.green}{hub_status.get('currentEarning')} AVEUM{term.normal}\n" +
                f"{term.yellow}Hourly Rate:{term.normal} {term.green}{hub_status.get('hourlyRate')} AVEUM/hour{term.normal}\n" +
                f"{term.yellow}Remaining Time:{term.normal} {term.green}{format_time_remaining(hub_status.get('remainingTime', 0))}{term.normal}"
            )
        else:
            mining_status_content = f"{term.yellow}Mining Status:{term.normal} {term.red}INACTIVE{term.normal}\n{term.yellow}Starting mining...{term.normal}"
            
            log_message('Mining is not active. Starting automatically...', 'warning')
            await start_hub_mining()
            
            asyncio.create_task(asyncio.sleep(2, update_mining_status()))
        
        render_ui()
    except Exception as error:
        log_message(f'Error updating mining status: {str(error)}', 'error')
        
        if hasattr(error, 'response') and error.response and (error.response.status == 401 or error.response.status == 403):
            log_message('Authentication error. Trying to login again...', 'warning')
            await auth.login()
            
            if auth.is_authenticated():
                asyncio.create_task(asyncio.sleep(1, update_mining_status()))

async def ensure_mining():
    try:
        if not auth.is_authenticated() or current_bot_mode != BOT_MODE['MINING']:
            return
        
        hub_status = await get_hub_status()
        
        if hub_status and not hub_status.get('isHub'):
            log_message('Mining check: Mining is not active. Starting...', 'warning')
            await start_hub_mining()
        elif hub_status and hub_status.get('isHub') and hub_status.get('remainingTime', 0) <= 0.001:
            log_message('Mining complete! Claiming reward...', 'success')
            await claim_reward()
            log_message('Starting new mining session...', 'info')
            await start_hub_mining()
    except Exception as error:
        log_message(f'Error checking mining status: {str(error)}', 'error')

async def run_auto_like():
    global auto_like_running, auto_like_status_content, total_liked
    
    if not auth.is_authenticated() or current_bot_mode != BOT_MODE['AUTO_LIKE'] or auto_like_running:
        return
    
    auto_like_running = True
    total_liked = 0
    
    try:
        async def process_users(page, source):
            global total_liked
            log_message(f"Fetching {source} page {page}...", 'info')
            
            data = None
            if source == 'discover feed':
                data = await get_discover_feed(page, 20)
            else:
                data = await get_discover_online_users(page, 20)
            
            if not data:
                log_message(f"Could not fetch {source}", 'warning')
                return 0
            
            users = []
            if 'users' in data and isinstance(data['users'], list):
                users = data['users']
                log_message(f"Found {len(users)} users in {source}", 'info')
            elif 'posts' in data and isinstance(data['posts'], list):
                users = [{'id': post.get('user_id') or post.get('id'), 
                          'username': post.get('username'), 
                          'is_liked': post.get('liked')} for post in data['posts']]
                log_message(f"Found {len(users)} posts in {source}", 'info')
            else:
                log_message(f"Unexpected data structure in {source}. Available keys: {', '.join(data.keys())}", 'warning')
                return 0
            
            liked_count = 0
            
            for user in users:
                if current_bot_mode != BOT_MODE['AUTO_LIKE']:
                    break
                
                if user['id'] in processed_user_ids:
                    continue
                
                if user.get('is_liked'):
                    processed_user_ids.add(user['id'])
                    continue
                
                log_message(f"Liking user ID: {user['id']}{f' ({user.get('username')})' if user.get('username') else ''}...", 'info')
                await toggle_like(user['id'])
                processed_user_ids.add(user['id'])
                total_liked += 1
                liked_count += 1
                
                update_auto_like_status(total_liked)
                
                delay = get_random_delay(2000, 5000)
                log_message(f"Waiting {delay/1000} seconds before next like...", 'info')
                await asyncio.sleep(delay / 1000)
            
            return liked_count
        
        current_page = 1
        max_pages = 5
        
        while current_page <= max_pages and current_bot_mode == BOT_MODE['AUTO_LIKE']:
            total_processed = 0
            
            total_processed += await process_users(current_page, 'discover feed')
            
            if total_processed < 5 and current_bot_mode == BOT_MODE['AUTO_LIKE']:
                await process_users(current_page, 'online users')
            
            current_page += 1
            
            if current_page <= max_pages and current_bot_mode == BOT_MODE['AUTO_LIKE']:
                page_delay = get_random_delay(5000, 10000)
                log_message(f"Waiting {page_delay/1000} seconds before fetching next page...", 'info')
                await asyncio.sleep(page_delay / 1000)
        
        log_message(f"Auto-like session completed. Liked {total_liked} users.", 'success')
        
        if current_bot_mode == BOT_MODE['AUTO_LIKE']:
            reset_delay = get_random_delay(60000, 120000)
            log_message(f"Taking a break. Will restart auto-like in {reset_delay/1000} seconds...", 'info')
            
            async def restart_auto_like():
                await asyncio.sleep(reset_delay / 1000)
                global auto_like_running
                auto_like_running = False
                if current_bot_mode == BOT_MODE['AUTO_LIKE']:
                    await run_auto_like()
            
            asyncio.create_task(restart_auto_like())
        else:
            auto_like_running = False
        
    except Exception as error:
        log_message(f"Error in auto-like: {str(error)}", 'error')
        auto_like_running = False
        
        if hasattr(error, 'response') and error.response and (error.response.status == 401 or error.response.status == 403):
            log_message('Authentication error. Trying to login again...', 'warning')
            await auth.login()
        
        async def retry_auto_like():
            await asyncio.sleep(10)
            if current_bot_mode == BOT_MODE['AUTO_LIKE']:
                global auto_like_running
                auto_like_running = False
                await run_auto_like()
        
        asyncio.create_task(retry_auto_like())

def update_auto_like_status(total_liked):
    global auto_like_status_content
    auto_like_status_content = (
        f"{term.yellow}Auto Like Status:{term.normal} {term.green}ACTIVE{term.normal}\n" +
        f"{term.yellow}Total Users Liked:{term.normal} {term.green}{total_liked}{term.normal}\n" +
        f"{term.yellow}Processed Users:{term.normal} {term.green}{len(processed_user_ids)}{term.normal}\n" +
        f"{term.yellow}Started At:{term.normal} {term.green}{datetime.now().strftime('%H:%M:%S')}{term.normal}"
    )
    render_ui()

def update_mode_display():
    global current_mode
    current_mode = 'MINING' if current_bot_mode == BOT_MODE['MINING'] else 'AUTO LIKE'
    render_ui()

def toggle_bot_mode():
    global current_bot_mode
    
    if current_bot_mode == BOT_MODE['MINING']:
        current_bot_mode = BOT_MODE['AUTO_LIKE']
        log_message('Switching to AUTO LIKE mode', 'info')
        if not auto_like_running:
            asyncio.create_task(run_auto_like())
    else:
        current_bot_mode = BOT_MODE['MINING']
        log_message('Switching to MINING mode', 'info')
        asyncio.create_task(asyncio.sleep(1, update_mining_status()))
    
    update_mode_display()

def render_ui():
    # Clear the screen
    print(term.clear)
    
    # Header
    print(term.center(f"{term.cyan}SAVAN MINING BOTx{term.normal}"))
    
    # Mode
    mode_color = term.green if current_bot_mode == BOT_MODE['MINING'] else term.cyan
    print(term.center(f"CURRENT MODE: {mode_color}{current_mode}{term.normal}"))
    print(term.center("=" * 50))
    
    # User info
    print(f"{term.yellow}USER INFO:{term.normal}")
    print(user_info_content)
    print(term.center("=" * 50))
    
    # Status box
    if current_bot_mode == BOT_MODE['MINING']:
        print(f"{term.yellow}MINING STATUS:{term.normal}")
        print(mining_status_content)
    else:
        print(f"{term.yellow}AUTO LIKE STATUS:{term.normal}")
        print(auto_like_status_content)
    print(term.center("=" * 50))
    
    # Log box
    print(f"{term.yellow}LOG:{term.normal}")
    for message in log_messages[-8:]:  # Show only the last 8 log messages
        print(message)
    
    # Status bar with commands
    print(term.center("=" * 50))
    print(term.center(f"{term.bold}{term.yellow}AVAILABLE COMMANDS{term.normal}"))
    print(term.center("-" * 50))
    print(term.center(f"{term.bold}{term.red}[1]{term.normal} = Exit Bot"))
    print(term.center(f"{term.bold}{term.green}[2]{term.normal} = Refresh Token"))
    print(term.center(f"{term.bold}{term.cyan}[3]{term.normal} = Switch Mode (Mining/Auto-Like)"))
    print(term.center("=" * 50))
    print(f"\n{term.bold}{term.yellow}Enter Command Number (1-3):{term.normal} ", end='', flush=True)

async def run_bot():
    log_message('Starting Aveum Mining Bot...', 'info')
    
    login_success = await auth.login()
    if not login_success:
        log_message('Failed to login. Please check your credentials in .env file.', 'error')
        return
    
    await update_user_info()
    update_mode_display()
    await update_mining_status()
    
    # Set up refresh intervals
    refresh_task = asyncio.create_task(refresh_loop())
    mining_check_task = asyncio.create_task(mining_check_loop())
    
    # Set up command handling
    while True:
        render_ui()
        
        try:
            # Get command from user
            command = input().strip()
            
            # Process command
            if command == '1':
                log_message('Quitting bot...', 'warning')
                break
            elif command == '2':
                log_message('Refreshing token...', 'info')
                await refresh_token()
            elif command == '3':
                log_message('Toggling mode...', 'info')
                toggle_bot_mode()
            else:
                log_message(f'Invalid command: {command}. Please enter 1, 2, or 3.', 'error')
        except Exception as e:
            log_message(f'Error processing command: {str(e)}', 'error')
    
    # Clean up
    refresh_task.cancel()
    mining_check_task.cancel()
    log_message('Shutting down bot...', 'warning')
    await asyncio.sleep(1)
    os._exit(0)

async def refresh_loop():
    while True:
        await update_user_info()
        if current_bot_mode == BOT_MODE['MINING']:
            await update_mining_status()
        await asyncio.sleep(10)

async def mining_check_loop():
    while True:
        if current_bot_mode == BOT_MODE['MINING']:
            await ensure_mining()
        elif current_bot_mode == BOT_MODE['AUTO_LIKE'] and not auto_like_running:
            await run_auto_like()
        await asyncio.sleep(30)

async def refresh_token():
    log_message('Manually refreshing authentication token...', 'info')
    await auth.login()
    if auth.is_authenticated():
        log_message('Token refreshed successfully!', 'success')
        await update_user_info()
        if current_bot_mode == BOT_MODE['MINING']:
            await update_mining_status()

# Check if .env file exists, create if not
if not os.path.exists('.env'):
    with open('.env', 'w') as f:
        f.write('AVEUM_EMAIL=youremail@gmail.com\nAVEUM_PASSWORD=\n')
    log_message('Created .env file with template. Please fill in your credentials.', 'info')
else:
    # Check if .env file is empty or has template values
    with open('.env', 'r') as f:
        content = f.read().strip()
        if not content or 'youremail@gmail.com' in content:
            with open('.env', 'w') as f:
                f.write('AVEUM_EMAIL=youremail@gmail.com\nAVEUM_PASSWORD=\n')
            log_message('Created .env file with template. Please fill in your credentials.', 'info')

# Run the bot
if __name__ == "__main__":
    asyncio.run(run_bot()) 
