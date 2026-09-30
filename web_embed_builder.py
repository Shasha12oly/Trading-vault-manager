"""
Web Interface for Custom Discord Embed Builder
Flask-based web app to create and post custom embeds to Discord channels
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import discord
import asyncio
import threading
import os
from dotenv import load_dotenv
from config import SUPPORT_ROLE_ID

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key-here")
app.config['JSON_AS_ASCII'] = False  # Enable UTF-8 for JSON responses

# Web authentication credentials
WEB_USERNAME = os.getenv("WEB_USERNAME", "admin")
WEB_PASSWORD = os.getenv("WEB_PASSWORD", "adm")

# Discord bot client
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
client = discord.Client(intents=intents)

# Store bot token
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Global event loop for async operations
event_loop = None

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for web interface"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == WEB_USERNAME and password == WEB_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout from web interface"""
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Render the embed builder interface"""
    return render_template('embed_builder.html')

@app.route('/api/channels', methods=['GET'])
def get_channels():
    """Get list of text channels from the server"""
    try:
        # Run async function to get channels
        channels = asyncio.run_coroutine_threadsafe(fetch_channels(), event_loop).result(timeout=10)
        return jsonify({'success': True, 'channels': channels})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

async def fetch_channels():
    """Fetch text channels from Discord"""
    channels = []
    for guild in client.guilds:
        for channel in guild.text_channels:
            channels.append({
                'id': str(channel.id),
                'name': channel.name,
                'guild': guild.name
            })
    return channels

@app.route('/api/post_embed', methods=['POST'])
def post_embed():
    """Post a custom embed to Discord channel"""
    try:
        data = request.json
        
        # Get embed parameters
        channel_id = data.get('channel_id')
        title = data.get('title', '')
        description = data.get('description', '')
        color = data.get('color', '#00FFFF')
        thumbnail_url = data.get('thumbnail_url', '')
        banner_url = data.get('banner_url', '')
        footer_text = data.get('footer_text', '')
        fields = data.get('fields', [])
        
        # Convert hex color to discord.Color
        color_rgb = discord.Color.from_str(color)
        
        # Run async function to post embed
        result = asyncio.run_coroutine_threadsafe(send_embed_to_channel(
            channel_id, title, description, color_rgb, 
            thumbnail_url, banner_url, footer_text, fields
        ), event_loop).result(timeout=10)
        
        response = jsonify(result)
        response.charset = 'utf-8'
        return response
    except Exception as e:
        error_response = jsonify({'success': False, 'error': str(e)})
        error_response.charset = 'utf-8'
        return error_response

async def send_embed_to_channel(channel_id, title, description, color, thumbnail_url, banner_url, footer_text, fields):
    """Send embed to Discord channel"""
    # Get channel
    channel = client.get_channel(int(channel_id))
    if not channel:
        return {'success': False, 'error': 'Channel not found'}
    
    print(f"Creating embed - Banner URL: {banner_url}, Thumbnail URL: {thumbnail_url}")
    
    # Create embed
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    
    # Add thumbnail if provided
    if thumbnail_url:
        print(f"Setting thumbnail: {thumbnail_url}")
        embed.set_thumbnail(url=thumbnail_url)
    
    # Add banner if provided
    if banner_url:
        print(f"Setting banner image: {banner_url}")
        embed.set_image(url=banner_url)
    
    # Add footer if provided
    if footer_text:
        embed.set_footer(text=footer_text)
    
    # Add fields if provided
    for field in fields:
        if field.get('name') and field.get('value'):
            embed.add_field(
                name=field['name'],
                value=field['value'],
                inline=field.get('inline', False)
            )
    
    print(f"Sending embed to channel {channel.name}")
    # Send embed
    await channel.send(embed=embed)
    
    return {'success': True, 'message': f'Embed posted to #{channel.name}'}

def start_bot():
    """Start Discord bot in background"""
    global event_loop
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    try:
        event_loop.run_until_complete(client.login(DISCORD_TOKEN))
        event_loop.run_until_complete(client.connect())
        event_loop.run_forever()
    except Exception as e:
        print(f"Bot connection error: {e}")

if __name__ == '__main__':
    # Start Discord bot in background thread
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Wait for bot to connect
    import time
    time.sleep(2)
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
