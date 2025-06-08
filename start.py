"""
Start and onboarding handlers
"""

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from utils.keyboard import get_main_menu, get_onboarding_keyboard
from utils.database import create_user, get_user
from utils.security import rate_limit
from config import WELCOME_MESSAGE, EMOJIS

router = Router()

@router.message(CommandStart())
@rate_limit
async def start_handler(message: Message, state: FSMContext):
    """Handle /start command with cyberpunk welcome"""
    
    user_id = message.from_user.id
    username = message.from_user.username or "Anonymous"
    first_name = message.from_user.first_name or "User"
    
    # Create or get user
    user = await get_user(user_id)
    if not user:
        await create_user(user_id, username, first_name)
        is_new_user = True
    else:
        is_new_user = False
    
    # Clear any existing state
    await state.clear()
    
    if is_new_user:
        # New user onboarding
        onboarding_text = f"""
{EMOJIS['rocket']} <b>Welcome aboard, {first_name}!</b>

{EMOJIS['diamond']} You've just joined the most secure escrow platform on Telegram.

<b>Quick Setup:</b>
{EMOJIS['shield']} Your account is automatically secured
{EMOJIS['key']} All transactions are encrypted
{EMOJIS['lightning']} Instant notifications enabled

<b>Ready to start your first deal?</b>
        """
        
        await message.answer(
            onboarding_text,
            reply_markup=get_onboarding_keyboard()
        )
    else:
        # Returning user
        welcome_back = f"""
{EMOJIS['fire']} <b>Welcome back, {first_name}!</b>

{EMOJIS['lightning']} Ready to make some secure deals?
        """
        
        await message.answer(
            welcome_back,
            reply_markup=get_main_menu()
        )

@router.callback_query(F.data == "start_onboarding")
async def onboarding_complete(callback: CallbackQuery):
    """Complete onboarding process"""
    
    await callback.message.edit_text(
        WELCOME_MESSAGE,
        reply_markup=get_main_menu()
    )
    
    await callback.answer(f"{EMOJIS['success']} Setup complete!")

@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery, state: FSMContext):
    """Show main menu"""
    
    await state.clear()
    
    await callback.message.edit_text(
        WELCOME_MESSAGE,
        reply_markup=get_main_menu()
    )
    
    await callback.answer()

@router.message(Command("help"))
async def help_handler(message: Message):
    """Show help information"""
    
    help_text = f"""
{EMOJIS['shield']} <b>Quick Escrow Bot Help</b>

<b>Commands:</b>
/start - Main menu
/help - Show this help
/status - Check your deals
/admin - Admin panel (authorized only)

<b>How Escrow Works:</b>
1. {EMOJIS['deal']} Create a new deal
2. {EMOJIS['money']} Buyer sends payment
3. {EMOJIS['lock']} Funds held securely
4. {EMOJIS['send']} Seller delivers goods/service
5. {EMOJIS['success']} Payment released to seller

<b>Security Features:</b>
{EMOJIS['shield']} End-to-end encryption
{EMOJIS['key']} Multi-factor verification
{EMOJIS['lock']} Secure fund holding
{EMOJIS['lightning']} Instant dispute resolution

<b>Need help?</b>
Contact admin: @darx_zerox
    """
    
    await message.answer(help_text)
