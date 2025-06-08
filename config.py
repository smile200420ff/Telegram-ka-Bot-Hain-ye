"""
Configuration settings for the Escrow Bot
"""

import os

# Bot Configuration
BOT_TOKEN = "7640121375:AAEM9mJO9TUrhdxuUxLq8KlrOkL-hbVtDRM"

# Admin Configuration
ADMIN_USER = "@darx_zerox"
ADMIN_ID = None  # Will be set dynamically when admin interacts

# UPI Configuration
DEFAULT_UPI_ID = "Shouryahooda751-2@oksbi"

# Security Settings
MAX_DEALS_PER_USER = 10
RATE_LIMIT_SECONDS = 5

# Database Settings
DATABASE_FILE = "escrow_bot.db"

# Styling Configuration
COLORS = {
    'primary': '#00D4FF',    # Neon Blue
    'secondary': '#FF006E',  # Neon Pink
    'success': '#00FF88',    # Neon Green
    'warning': '#FFD60A',    # Neon Yellow
    'danger': '#FF073A',     # Neon Red
    'dark': '#0A0E27',       # Dark Blue
    'darker': '#020408'      # Almost Black
}

# Emoji Sets
EMOJIS = {
    'lock': '🔐',
    'money': '💰',
    'deal': '📦',
    'send': '📤',
    'receive': '📥',
    'status': '🧾',
    'dispute': '🛡️',
    'admin': '🧑‍💼',
    'loading': '⏳',
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'fire': '🔥',
    'lightning': '⚡',
    'rocket': '🚀',
    'diamond': '💎',
    'shield': '🛡️',
    'key': '🔑',
    'qr': '📱'
}

# Messages
WELCOME_MESSAGE = f"""
{EMOJIS['fire']} <b>Welcome to Quick Escrow Bot</b> {EMOJIS['fire']}

{EMOJIS['diamond']} <i>Secure • Fast • Reliable</i>

{EMOJIS['lock']} Your trusted partner for safe transactions
{EMOJIS['lightning']} Powered by cutting-edge security

<b>Features:</b>
{EMOJIS['deal']} Create secure escrow deals
{EMOJIS['money']} UPI & QR code payments
{EMOJIS['shield']} 24/7 dispute resolution
{EMOJIS['rocket']} Lightning-fast processing

<i>Click below to get started!</i>
"""

DEAL_CREATED_MESSAGE = f"""
{EMOJIS['success']} <b>Deal Created Successfully!</b>

{EMOJIS['key']} <b>Deal ID:</b> #{{deal_id}}
{EMOJIS['money']} <b>Amount:</b> ₹{{amount}}
{EMOJIS['lock']} <b>Status:</b> Waiting for payment

<i>Share this deal ID with the other party</i>
"""
