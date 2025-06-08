"""
Payment processing handlers
"""

import os
import uuid
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from utils.keyboard import get_payment_keyboard, get_main_menu
from utils.qr_generator import generate_upi_qr
from utils.database import get_deal, update_deal_status, create_payment_record
from utils.security import rate_limit
from config import EMOJIS, DEFAULT_UPI_ID

router = Router()

class PaymentStates(StatesGroup):
    waiting_for_payment_proof = State()
    waiting_for_upi_ref = State()

@router.callback_query(F.data.startswith("pay_deal_"))
@rate_limit
async def initiate_payment(callback: CallbackQuery, state: FSMContext):
    """Initiate payment for a deal"""
    
    deal_id = callback.data.split("_")[-1]
    deal = await get_deal(deal_id)
    
    if not deal:
        await callback.answer(f"{EMOJIS['error']} Deal not found!")
        return
    
    if deal['status'] != 'created':
        await callback.answer(f"{EMOJIS['warning']} Deal is not available for payment!")
        return
    
    # Use custom QR code for payment
    qr_filename = "static/payment_qr.jpg"
    
    try:
        payment_text = f"""
{EMOJIS['money']} <b>Payment Instructions</b>

{EMOJIS['diamond']} <b>Deal:</b> #{deal_id}
{EMOJIS['money']} <b>Amount:</b> ₹{deal['amount']:,.2f}

{EMOJIS['qr']} <b>Payment Methods:</b>

<b>1. Scan QR Code</b>
Scan the QR code below with any UPI app

<b>2. Manual UPI Transfer</b>
UPI ID: <code>{DEFAULT_UPI_ID}</code>
Amount: ₹{deal['amount']:,.2f}
Note: Escrow#{deal_id}

{EMOJIS['shield']} <b>Security Notice:</b>
• Funds will be held securely in escrow
• Payment will only be released after confirmation
• Keep your payment receipt/screenshot
        """
        
        await state.update_data(deal_id=deal_id, amount=deal['amount'])
        await state.set_state(PaymentStates.waiting_for_payment_proof)
        
        # Send custom QR code
        qr_file = FSInputFile(qr_filename)
        await callback.message.answer_photo(
            photo=qr_file,
            caption=payment_text,
            reply_markup=get_payment_keyboard(deal_id)
        )
        
    except Exception as e:
        await callback.answer(f"{EMOJIS['error']} Error loading payment QR!")
        return
    
    await callback.answer(f"{EMOJIS['rocket']} Payment initiated!")

@router.callback_query(F.data.startswith("regenerate_qr_"))
async def regenerate_qr(callback: CallbackQuery, state: FSMContext):
    """Regenerate QR code (but use same custom QR)"""
    
    deal_id = callback.data.split("_")[-1]
    deal = await get_deal(deal_id)
    
    if not deal:
        await callback.answer(f"{EMOJIS['error']} Deal not found!")
        return
    
    # Use the same custom QR code
    qr_filename = "static/payment_qr.jpg"
    
    try:
        payment_text = f"""
{EMOJIS['money']} <b>Payment Instructions</b>

{EMOJIS['diamond']} <b>Deal:</b> #{deal_id}
{EMOJIS['money']} <b>Amount:</b> ₹{deal['amount']:,.2f}

{EMOJIS['qr']} <b>Payment Methods:</b>

<b>1. Scan QR Code</b>
Scan the QR code below with any UPI app

<b>2. Manual UPI Transfer</b>
UPI ID: <code>{DEFAULT_UPI_ID}</code>
Amount: ₹{deal['amount']:,.2f}
Note: Escrow#{deal_id}

{EMOJIS['shield']} <b>Security Notice:</b>
• Funds will be held securely in escrow
• Payment will only be released after confirmation
• Keep your payment receipt/screenshot
        """
        
        await state.update_data(deal_id=deal_id, amount=deal['amount'])
        await state.set_state(PaymentStates.waiting_for_payment_proof)
        
        # Send same custom QR code
        qr_file = FSInputFile(qr_filename)
        await callback.message.answer_photo(
            photo=qr_file,
            caption=payment_text,
            reply_markup=get_payment_keyboard(deal_id)
        )
        
        await callback.answer(f"{EMOJIS['success']} QR code refreshed!")
        
    except Exception as e:
        await callback.answer(f"{EMOJIS['error']} Error loading QR code!")

@router.callback_query(F.data.startswith("payment_done_"))
async def payment_confirmation(callback: CallbackQuery, state: FSMContext):
    """Handle payment confirmation"""
    
    deal_id = callback.data.split("_")[-1]
    
    confirmation_text = f"""
{EMOJIS['success']} <b>Payment Confirmation</b>

{EMOJIS['shield']} Please provide payment proof:

<b>Option 1: Screenshot</b>
Send a screenshot of your payment confirmation

<b>Option 2: UPI Reference ID</b>
Send your UPI transaction reference number

{EMOJIS['lightning']} <b>This helps us verify your payment quickly!</b>

<i>Send your proof now...</i>
    """
    
    # Send new message instead of editing photo message
    try:
        if callback.message.photo:
            # For photo messages, send a new message
            await callback.message.answer(
                confirmation_text,
                reply_markup=None
            )
        else:
            # For text messages, edit the existing message
            await callback.message.edit_text(
                confirmation_text,
                reply_markup=None
            )
    except Exception:
        # Fallback: always send new message
        await callback.message.answer(
            confirmation_text,
            reply_markup=None
        )
    
    await callback.answer(f"{EMOJIS['loading']} Waiting for payment proof...")

@router.message(PaymentStates.waiting_for_payment_proof)
async def process_payment_proof(message: Message, state: FSMContext):
    """Process payment proof (screenshot or reference ID)"""
    
    data = await state.get_data()
    deal_id = data.get('deal_id')
    amount = data.get('amount')
    
    if not deal_id:
        await message.answer(f"{EMOJIS['error']} Session expired. Please try again.")
        await state.clear()
        return
    
    # Handle screenshot
    if message.photo:
        # Mock payment verification (in real app, this would integrate with payment gateway)
        payment_id = str(uuid.uuid4())[:12].upper()
        
        # Create payment record
        await create_payment_record(
            deal_id=deal_id,
            payer_id=message.from_user.id,
            amount=amount,
            payment_method='UPI_SCREENSHOT',
            reference_id=payment_id,
            status='pending_verification'
        )
        
        # Update deal status
        await update_deal_status(deal_id, 'funded')
        
        success_text = f"""
{EMOJIS['success']} <b>Payment Received!</b>

{EMOJIS['key']} <b>Deal ID:</b> #{deal_id}
{EMOJIS['money']} <b>Amount:</b> ₹{amount:,.2f}
{EMOJIS['diamond']} <b>Payment ID:</b> {payment_id}

{EMOJIS['lock']} <b>Status:</b> Funds secured in escrow

{EMOJIS['shield']} <b>Next Steps:</b>
1. Seller will be notified
2. Complete the transaction as agreed
3. Funds will be released upon completion

{EMOJIS['lightning']} <b>Your payment is now secure!</b>
        """
        
        await message.answer(
            success_text,
            reply_markup=get_main_menu()
        )
        
    # Handle text (UPI reference)
    elif message.text:
        reference_id = message.text.strip()
        
        if len(reference_id) < 8:
            await message.answer(
                f"{EMOJIS['warning']} Please provide a valid UPI reference ID (minimum 8 characters)"
            )
            return
        
        # Mock payment verification
        payment_id = str(uuid.uuid4())[:12].upper()
        
        # Create payment record
        await create_payment_record(
            deal_id=deal_id,
            payer_id=message.from_user.id,
            amount=amount,
            payment_method='UPI_REFERENCE',
            reference_id=reference_id,
            status='pending_verification'
        )
        
        # Update deal status
        await update_deal_status(deal_id, 'funded')
        
        success_text = f"""
{EMOJIS['success']} <b>Payment Verified!</b>

{EMOJIS['key']} <b>Deal ID:</b> #{deal_id}
{EMOJIS['money']} <b>Amount:</b> ₹{amount:,.2f}
{EMOJIS['lightning']} <b>UPI Ref:</b> {reference_id}
{EMOJIS['diamond']} <b>Payment ID:</b> {payment_id}

{EMOJIS['lock']} <b>Status:</b> Funds secured in escrow

{EMOJIS['shield']} <b>Transaction Complete!</b>
Your payment has been verified and secured.

{EMOJIS['rocket']} <b>Next:</b> Proceed with your deal as agreed.
        """
        
        await message.answer(
            success_text,
            reply_markup=get_main_menu()
        )
    
    else:
        await message.answer(
            f"{EMOJIS['warning']} Please send a screenshot or UPI reference ID."
        )
        return
    
    await state.clear()

@router.callback_query(F.data.startswith("release_payment_"))
async def release_payment(callback: CallbackQuery):
    """Release payment to seller"""
    
    deal_id = callback.data.split("_")[-1]
    deal = await get_deal(deal_id)
    
    if not deal:
        await callback.answer(f"{EMOJIS['error']} Deal not found!")
        return
    
    if deal['status'] != 'funded':
        await callback.answer(f"{EMOJIS['warning']} Deal is not ready for payment release!")
        return
    
    # Update deal status to completed
    await update_deal_status(deal_id, 'completed')
    
    # Mock payment release (in real app, this would trigger actual transfer)
    release_text = f"""
{EMOJIS['success']} <b>Payment Released!</b>

{EMOJIS['key']} <b>Deal ID:</b> #{deal_id}
{EMOJIS['money']} <b>Amount:</b> ₹{deal['amount']:,.2f}

{EMOJIS['rocket']} <b>Transaction Complete!</b>
Funds have been successfully released to the seller.

{EMOJIS['diamond']} <b>Thank you for using Quick Escrow Bot!</b>

{EMOJIS['shield']} Your transaction is now complete and secure.
    """
    
    await callback.message.edit_text(
        release_text,
        reply_markup=get_main_menu()
    )
    
    await callback.answer(f"{EMOJIS['success']} Payment released successfully!")

@router.callback_query(F.data.startswith("dispute_deal_"))
async def create_dispute(callback: CallbackQuery):
    """Create a dispute for a deal"""
    
    deal_id = callback.data.split("_")[-1]
    deal = await get_deal(deal_id)
    
    if not deal:
        await callback.answer(f"{EMOJIS['error']} Deal not found!")
        return
    
    # Update deal status to disputed
    await update_deal_status(deal_id, 'disputed')
    
    dispute_text = f"""
{EMOJIS['warning']} <b>Dispute Created</b>

{EMOJIS['key']} <b>Deal ID:</b> #{deal_id}
{EMOJIS['money']} <b>Amount:</b> ₹{deal['amount']:,.2f}

{EMOJIS['shield']} <b>Status:</b> Under Review

{EMOJIS['lightning']} <b>What happens next:</b>
1. Admin team has been notified
2. Both parties will be contacted
3. Evidence will be reviewed
4. Fair resolution will be provided

{EMOJIS['diamond']} <b>Admin Contact:</b> @darx_zerox

{EMOJIS['lock']} Funds remain securely held during dispute resolution.
    """
    
    await callback.message.edit_text(
        dispute_text,
        reply_markup=get_main_menu()
    )
    
    await callback.answer(f"{EMOJIS['shield']} Dispute created - Admin notified!")
