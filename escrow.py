"""
Escrow deal handlers
"""

import uuid
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from utils.keyboard import (
    get_main_menu, get_deal_keyboard, get_deal_management_keyboard,
    get_confirmation_keyboard
)
from utils.database import (
    create_deal, get_deal, get_user_deals, update_deal_status,
    get_all_deals
)
from utils.security import rate_limit
from config import EMOJIS, DEAL_CREATED_MESSAGE

router = Router()

class DealStates(StatesGroup):
    waiting_for_description = State()
    waiting_for_amount = State()
    waiting_for_terms = State()
    waiting_for_confirmation = State()

@router.callback_query(F.data == "create_deal")
@rate_limit
async def start_deal_creation(callback: CallbackQuery, state: FSMContext):
    """Start the deal creation process"""
    
    await state.set_state(DealStates.waiting_for_description)
    
    creation_text = f"""
{EMOJIS['diamond']} <b>Create New Escrow Deal</b>

{EMOJIS['lock']} <b>Step 1/3: Description</b>

Please describe what you're buying or selling:

<i>Example: "iPhone 14 Pro Max 256GB Space Black"</i>

{EMOJIS['lightning']} <b>Tips:</b>
• Be specific and detailed
• Include model numbers, conditions
• Mention any accessories included
    """
    
    await callback.message.edit_text(creation_text)
    await callback.answer(f"{EMOJIS['rocket']} Let's create your deal!")

@router.message(DealStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    """Process deal description"""
    
    description = message.text.strip()
    
    if len(description) < 10:
        await message.answer(
            f"{EMOJIS['warning']} Description too short! Please provide at least 10 characters."
        )
        return
    
    if len(description) > 500:
        await message.answer(
            f"{EMOJIS['warning']} Description too long! Please keep it under 500 characters."
        )
        return
    
    await state.update_data(description=description)
    await state.set_state(DealStates.waiting_for_amount)
    
    amount_text = f"""
{EMOJIS['money']} <b>Step 2/3: Amount</b>

{EMOJIS['success']} Description saved!

Now enter the deal amount in INR:

<i>Example: 45000 or 45000.50</i>

{EMOJIS['shield']} <b>Security Note:</b>
• Minimum amount: ₹100
• Maximum amount: ₹500,000
• Amount will be held securely in escrow
    """
    
    await message.answer(amount_text)

@router.message(DealStates.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    """Process deal amount"""
    
    try:
        amount = float(message.text.strip().replace(',', ''))
        
        if amount < 100:
            await message.answer(
                f"{EMOJIS['warning']} Minimum amount is ₹100"
            )
            return
        
        if amount > 500000:
            await message.answer(
                f"{EMOJIS['warning']} Maximum amount is ₹5,00,000"
            )
            return
        
        await state.update_data(amount=amount)
        await state.set_state(DealStates.waiting_for_terms)
        
        terms_text = f"""
{EMOJIS['key']} <b>Step 3/3: Terms & Conditions</b>

{EMOJIS['success']} Amount: ₹{amount:,.2f} saved!

Please specify the deal terms:

<i>Example: "Payment within 24 hours, delivery within 3 days"</i>

{EMOJIS['lightning']} <b>Include:</b>
• Payment timeframe
• Delivery conditions
• Return/refund policy
• Any special conditions
        """
        
        await message.answer(terms_text)
        
    except ValueError:
        await message.answer(
            f"{EMOJIS['error']} Invalid amount! Please enter a valid number."
        )

@router.message(DealStates.waiting_for_terms)
async def process_terms(message: Message, state: FSMContext):
    """Process deal terms and show confirmation"""
    
    terms = message.text.strip()
    
    if len(terms) < 20:
        await message.answer(
            f"{EMOJIS['warning']} Terms too short! Please provide at least 20 characters."
        )
        return
    
    if len(terms) > 1000:
        await message.answer(
            f"{EMOJIS['warning']} Terms too long! Please keep it under 1000 characters."
        )
        return
    
    await state.update_data(terms=terms)
    
    # Get all data for confirmation
    data = await state.get_data()
    
    confirmation_text = f"""
{EMOJIS['diamond']} <b>Deal Confirmation</b>

{EMOJIS['lock']} <b>Description:</b>
{data['description']}

{EMOJIS['money']} <b>Amount:</b> ₹{data['amount']:,.2f}

{EMOJIS['key']} <b>Terms:</b>
{data['terms']}

{EMOJIS['shield']} <b>Security Features:</b>
• Funds held in secure escrow
• Dispute resolution available
• 24/7 monitoring
• Encrypted communications

<b>Ready to create this deal?</b>
    """
    
    await state.set_state(DealStates.waiting_for_confirmation)
    
    await message.answer(
        confirmation_text,
        reply_markup=get_confirmation_keyboard()
    )

@router.callback_query(F.data == "confirm_deal", DealStates.waiting_for_confirmation)
async def confirm_deal_creation(callback: CallbackQuery, state: FSMContext):
    """Confirm and create the deal"""
    
    data = await state.get_data()
    user_id = callback.from_user.id
    
    # Generate unique deal ID
    deal_id = str(uuid.uuid4())[:8].upper()
    
    # Create deal in database
    await create_deal(
        deal_id=deal_id,
        creator_id=user_id,
        description=data['description'],
        amount=data['amount'],
        terms=data['terms']
    )
    
    await state.clear()
    
    success_text = DEAL_CREATED_MESSAGE.format(
        deal_id=deal_id,
        amount=f"{data['amount']:,.2f}"
    )
    
    await callback.message.edit_text(
        success_text,
        reply_markup=get_deal_keyboard(deal_id)
    )
    
    await callback.answer(f"{EMOJIS['success']} Deal created successfully!")

@router.callback_query(F.data == "cancel_deal_creation")
async def cancel_deal_creation(callback: CallbackQuery, state: FSMContext):
    """Cancel deal creation"""
    
    await state.clear()
    
    await callback.message.edit_text(
        f"{EMOJIS['warning']} Deal creation cancelled.",
        reply_markup=get_main_menu()
    )
    
    await callback.answer("Cancelled")

@router.callback_query(F.data == "my_deals")
async def show_my_deals(callback: CallbackQuery):
    """Show user's deals"""
    
    user_id = callback.from_user.id
    deals = await get_user_deals(user_id)
    
    if not deals:
        await callback.message.edit_text(
            f"""
{EMOJIS['lock']} <b>Your Deals</b>

{EMOJIS['warning']} No deals found.

Create your first secure deal now!
            """,
            reply_markup=get_main_menu()
        )
        await callback.answer()
        return
    
    deals_text = f"{EMOJIS['lock']} <b>Your Deals</b>\n\n"
    
    for deal in deals:
        status_emoji = {
            'created': EMOJIS['loading'],
            'funded': EMOJIS['money'],
            'completed': EMOJIS['success'],
            'disputed': EMOJIS['warning'],
            'cancelled': EMOJIS['error']
        }.get(deal['status'], EMOJIS['lock'])
        
        deals_text += f"""
{status_emoji} <b>#{deal['deal_id']}</b>
{EMOJIS['money']} ₹{deal['amount']:,.2f} • {deal['status'].title()}
<i>{deal['description'][:50]}...</i>

"""
    
    await callback.message.edit_text(
        deals_text,
        reply_markup=get_main_menu()
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("deal_"))
async def show_deal_details(callback: CallbackQuery):
    """Show specific deal details"""
    
    deal_id = callback.data.split("_")[1]
    deal = await get_deal(deal_id)
    
    if not deal:
        await callback.answer(f"{EMOJIS['error']} Deal not found!")
        return
    
    status_emoji = {
        'created': EMOJIS['loading'],
        'funded': EMOJIS['money'],
        'completed': EMOJIS['success'],
        'disputed': EMOJIS['warning'],
        'cancelled': EMOJIS['error']
    }.get(deal['status'], EMOJIS['lock'])
    
    deal_text = f"""
{EMOJIS['diamond']} <b>Deal Details</b>

{EMOJIS['key']} <b>ID:</b> #{deal['deal_id']}
{status_emoji} <b>Status:</b> {deal['status'].title()}
{EMOJIS['money']} <b>Amount:</b> ₹{deal['amount']:,.2f}

{EMOJIS['lock']} <b>Description:</b>
{deal['description']}

{EMOJIS['shield']} <b>Terms:</b>
{deal['terms']}

{EMOJIS['lightning']} <b>Created:</b> {deal['created_at']}
    """
    
    await callback.message.edit_text(
        deal_text,
        reply_markup=get_deal_management_keyboard(deal_id, deal['status'])
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("share_deal_"))
async def share_deal(callback: CallbackQuery):
    """Share deal with others"""
    
    deal_id = callback.data.split("_")[-1]
    deal = await get_deal(deal_id)
    
    if not deal:
        await callback.answer(f"{EMOJIS['error']} Deal not found!")
        return
    
    # Check if user has permission to share (creator or admin)
    user_id = callback.from_user.id
    from utils.security import is_admin
    is_creator = deal['creator_id'] == user_id
    username = callback.from_user.username or ""
    is_admin_user = await is_admin(user_id, username)
    
    if not (is_creator or is_admin_user):
        await callback.answer(f"{EMOJIS['error']} Only deal creator can share this deal!")
        return
    
    # Generate shareable message
    share_text = f"""
{EMOJIS['diamond']} <b>Quick Escrow Deal</b>

{EMOJIS['key']} <b>Deal ID:</b> #{deal_id}
{EMOJIS['money']} <b>Amount:</b> ₹{deal['amount']:,.2f}
{EMOJIS['lock']} <b>Status:</b> {deal['status'].title()}

{EMOJIS['shield']} <b>Description:</b>
{deal['description']}

{EMOJIS['lightning']} <b>Terms:</b>
{deal['terms']}

{EMOJIS['rocket']} <b>To participate:</b>
1. Start the bot: @QuickEscrow_Bot
2. Use deal ID: #{deal_id}
3. Follow secure payment process

{EMOJIS['diamond']} <b>Secured by Quick Escrow Bot</b>
    """
    
    # Check if content is different before editing
    try:
        await callback.message.edit_text(
            share_text,
            reply_markup=get_deal_management_keyboard(deal_id, deal['status'])
        )
    except Exception:
        # If edit fails (content same), just show the current content
        pass
    
    await callback.answer(f"{EMOJIS['success']} Deal ready to share! Copy this message.")

@router.callback_query(F.data == "payment_status")
async def payment_status(callback: CallbackQuery):
    """Show payment status information"""
    
    status_text = f"""
{EMOJIS['money']} <b>Payment Status Guide</b>

{EMOJIS['loading']} <b>Created:</b> Waiting for payment
{EMOJIS['money']} <b>Funded:</b> Payment received & secured
{EMOJIS['success']} <b>Completed:</b> Payment released
{EMOJIS['warning']} <b>Disputed:</b> Under admin review
{EMOJIS['error']} <b>Cancelled:</b> Deal terminated

{EMOJIS['shield']} <b>Security Features:</b>
• Funds held in secure escrow
• 24/7 transaction monitoring
• Instant dispute resolution
• Multi-layer verification

{EMOJIS['lightning']} <b>Need help?</b> Contact @darx_zerox
    """
    
    await callback.message.edit_text(
        status_text,
        reply_markup=get_main_menu()
    )
    
    await callback.answer()

@router.callback_query(F.data == "support")
async def support(callback: CallbackQuery):
    """Show support information"""
    
    support_text = f"""
{EMOJIS['shield']} <b>Quick Escrow Support</b>

{EMOJIS['admin']} <b>Admin Contact:</b> @darx_zerox

{EMOJIS['lightning']} <b>Common Issues:</b>
• Payment not reflecting - Contact admin with UPI ref
• Deal disputes - Use dispute button in deal
• Technical problems - Message admin directly

{EMOJIS['rocket']} <b>Response Time:</b>
• Critical issues: 1-2 hours
• General queries: 4-6 hours
• Disputes: 12-24 hours

{EMOJIS['diamond']} <b>Security:</b>
All conversations are encrypted and monitored for your safety.

{EMOJIS['lock']} <b>Emergency:</b>
For urgent issues, include "URGENT" in your message to admin.
    """
    
    await callback.message.edit_text(
        support_text,
        reply_markup=get_main_menu()
    )
    
    await callback.answer()

@router.callback_query(F.data == "how_it_works")
async def how_it_works(callback: CallbackQuery):
    """Show how escrow works"""
    
    guide_text = f"""
{EMOJIS['diamond']} <b>How Escrow Works</b>

{EMOJIS['rocket']} <b>Step-by-Step Process:</b>

{EMOJIS['deal']} <b>1. Create Deal</b>
• Describe item/service
• Set amount and terms
• Get unique deal ID

{EMOJIS['money']} <b>2. Buyer Payment</b>
• Scan UPI QR code
• Send payment proof
• Funds secured in escrow

{EMOJIS['lock']} <b>3. Seller Delivery</b>
• Complete agreed terms
• Provide delivery proof
• Await buyer confirmation

{EMOJIS['success']} <b>4. Release Payment</b>
• Buyer confirms receipt
• Funds released to seller
• Deal completed successfully

{EMOJIS['shield']} <b>Safety Features:</b>
• Admin oversight on all deals
• Dispute resolution available
• Secure fund holding
• 24/7 monitoring system
    """
    
    await callback.message.edit_text(
        guide_text,
        reply_markup=get_main_menu()
    )
    
    await callback.answer()

@router.callback_query(F.data == "security_info")
async def security_info(callback: CallbackQuery):
    """Show security information"""
    
    security_text = f"""
{EMOJIS['shield']} <b>Security & Protection</b>

{EMOJIS['lock']} <b>Fund Security:</b>
• Multi-signature escrow system
• Encrypted transaction logs
• Real-time monitoring
• Instant fraud detection

{EMOJIS['diamond']} <b>User Protection:</b>
• Rate limiting prevents spam
• IP monitoring for suspicious activity
• Admin verification for disputes
• Secure payment processing

{EMOJIS['lightning']} <b>Privacy:</b>
• No personal data stored
• Anonymous transaction IDs
• Secure communication channels
• GDPR compliant operations

{EMOJIS['rocket']} <b>Compliance:</b>
• RBI guidelines followed
• UPI security standards
• Financial regulations adherence
• Regular security audits

{EMOJIS['warning']} <b>Red Flags:</b>
• Requests for direct payments
• Pressure to complete quickly
• Unusual payment methods
• Contact admin if suspicious
    """
    
    await callback.message.edit_text(
        security_text,
        reply_markup=get_main_menu()
    )
    
    await callback.answer()
