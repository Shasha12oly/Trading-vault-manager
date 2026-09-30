# Discord Embed Builder Web Interface

A web-based interface for creating and posting custom Discord embeds to channels.

## Features

- 🎨 **Custom Embed Builder**: Create Discord embeds with full customization
- 🎯 **Channel Selection**: Choose from all available Discord channels
- 🌈 **Color Picker**: Select custom embed colors with visual picker
- 🖼️ **Image Support**: Add thumbnails and banner images
- 📝 **Multiple Fields**: Add multiple embed fields with inline support
- 👁️ **Live Preview**: See your embed in real-time as you build it
- 🔐 **Authentication**: Protected with username/password login
- 🚀 **Easy Deployment**: Simple Flask-based web application

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Add these to your `.env` file:

```env
# Web Interface Configuration
FLASK_SECRET_KEY=your_random_secret_key_here
WEB_USERNAME=your_username
WEB_PASSWORD=your_password
```

### 3. Run the Web Interface

```bash
python web_embed_builder.py
```

The web interface will be available at: `http://localhost:5000`

## Usage

1. **Login**: Access the web interface and login with your credentials
2. **Select Channel**: Choose the Discord channel where you want to post the embed
3. **Build Embed**:
   - Enter title and description
   - Choose embed color using the color picker
   - Add thumbnail and banner URLs (optional)
   - Add footer text (optional)
   - Add multiple fields with names and values
4. **Preview**: Click "Preview" to see how your embed will look
5. **Post**: Click "Post Embed to Discord" to send it to the selected channel

## Features in Detail

### Embed Options

- **Title**: Main title of the embed
- **Description**: Main content (supports Discord markdown)
- **Color**: Embed color bar (visual color picker)
- **Thumbnail**: Small image in the top-right corner
- **Banner**: Large image at the bottom of the embed
- **Footer**: Text at the bottom of the embed
- **Fields**: Additional named sections with values

### Field Options

- **Name**: Field title
- **Value**: Field content
- **Inline**: Display fields side-by-side (instead of stacked)

## Security

- The web interface is protected with username/password authentication
- Uses Flask session management for secure login
- Configure strong credentials in your `.env` file

## Troubleshooting

### Bot Not Connecting

Make sure your `DISCORD_TOKEN` is correctly set in `.env` and the bot has proper permissions.

### Channels Not Loading

Ensure the bot is in the server and has permission to view channels.

### Embed Not Posting

Check that:
- The bot has permission to send messages in the selected channel
- The channel ID is valid
- The bot is running and connected

## Integration with Existing Bot

This web interface runs alongside your existing Discord bot. It uses the same Discord token and can post to any channel the bot has access to.

## Customization

You can customize the web interface by editing:
- `templates/embed_builder.html` - Main interface styling and layout
- `templates/login.html` - Login page styling
- `web_embed_builder.py` - Backend logic and API endpoints

## Future Enhancements

Potential improvements:
- Discord OAuth2 authentication
- Embed templates
- Save/load embed designs
- Schedule embeds for later posting
- Multi-channel posting
- Embed history/log
