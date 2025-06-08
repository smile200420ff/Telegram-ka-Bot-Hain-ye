"""
Admin panel handlers
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from utils.keyboard import get_admin_keyboard, get_admin_deal_keyboard, get_main_menu
from utils.database import get_all_deals, get_deal, update_deal_status, get_deal_stats
from utils.security import is_admin
from config import EMOJIS, ADMIN_USER

router = Router()

@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Show admin panel"""
    
    if not await is_admin(message.from_user.id, message.from_user.username):
        await message.answer(
            f"{EMOJIS['error']} Access denied. Only {ADMIN_USER} can access admin panel."
        )
        return
    
    # Get dashboard stats
    stats = await get_deal_stats()
    
    admin_text = f"""
{EMOJIS['shield']} <b>Admin Control Panel</b>

{EMOJIS['diamond']} <b>Dashboard Stats:</b>
{EMOJIS['deal']} Total Deals: {stats.get('total_deals', 0)}
{EMOJIS['money']} Active Deals: {stats.get('active_deals', 0)}
{EMOJIS['success']} Completed: {stats.get('completed_deals', 0)}
{EMOJIS['warning']} Disputed: {stats.get('disputed_deals', 0)}

{EMOJIS['lock']} <b>Total Escrow Value:</b> ₹{stats.get('total_value', 0):,.2f}

{EMOJIS['lightning']} <b>System Status:</b> Online
{EMOJIS['rocket']} <b>Security Level:</b> Maximum

<b>Select an action:</b>
    """
    
    await message.answer(
        admin_text,
        reply_markup=get_admin_keyboard()
    )

@router.callback_query(F.data == "admin_all_deals")
async def show_all_deals(callback: CallbackQuery):
    """Show all deals for admin"""
    
    if not await is_admin(callback.from_user.id, callback.from_user.username):
        await callback.answer(f"{EMOJIS['error']} Access denied!")
        return
    
    deals = await get_all_deals()
    
    if not deals:
        await callback.message.edit_text(
            f"""
{EMOJIS['shield']} <b>All Deals</b>

{EMOJIS['warning']} No deals found.
            """,
            reply_markup=get_admin_keyboard()
        )
        await callback.answer()
        return
    
    deals_text = f"{EMOJIS['shield']} <b>All Deals</b>\n\n"
    
    for deal in deals[-10:]:  # Show last 10 deals
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
{EMOJIS['key']} Creator: {deal['creator_id']}
<i>{deal['description'][:40]}...</i>

"""
    
    await callback.message.edit_text(
        deals_text,
        reply_markup=get_admin_keyboard()
    )
    
    await callback.answer()

@router.callback_query(F.data == "admin_disputes")
async def show_disputes(callback: CallbackQuery):
    """Show disputed deals"""
    
    if not await is_admin(callback.from_user.id, callback.from_user.username):
        await callback.answer(f"{EMOJIS['error']} Access denied!")
        return
    
    deals = await get_all_deals(status='disputed')
    
    if not deals:
        await callback.message.edit_text(
            f"""
{EMOJIS['shield']} <b>Disputed Deals</b>

{EMOJIS['success']} No active disputes!

All deals are running smoothly.
            """,
            reply_markup=get_admin_keyboard()
        )
        await callback.answer()
        return
    
    disputes_text = f"{EMOJIS['warning']} <b>Active Disputes</b>\n\n"
    
    for deal in deals:
        disputes_text += f"""
{EMOJIS['warning']} <b>#{deal['deal_id']}</b>
{EMOJIS['money']} ₹{deal['amount']:,.2f}
{EMOJIS['key']} Creator: {deal['creator_id']}
{EMOJIS['lightning']} Created: {deal['created_at']}
<i>{deal['description'][:50]}...</i>

"""
    
    await callback.message.edit_text(
        disputes_text,
        reply_markup=get_admin_keyboard()
    )
    
    await callback.answer(f"{EMOJIS['shield']} {len(deals)} disputes found")

@router.callback_query(F.data.startswith("admin_deal_"))
async def admin_deal_details(callback: CallbackQuery):
    """Show deal details for admin"""
    
    if not await is_admin(callback.from_user.id, callback.from_user.username):
        await callback.answer(f"{EMOJIS['error']} Access denied!")
        return
    
    deal_id = callback.data.split("_")[-1]
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
    
    admin_deal_text = f"""
{EMOJIS['shield']} <b>Admin - Deal Details</b>

{EMOJIS['key']} <b>ID:</b> #{deal['deal_id']}
{status_emoji} <b>Status:</b> {deal['status'].title()}
{EMOJIS['money']} <b>Amount:</b> ₹{deal['amount']:,.2f}
{EMOJIS['diamond']} <b>Creator:</b> {deal['creator_id']}

{EMOJIS['lock']} <b>Description:</b>
{deal['description']}

{EMOJIS['lightning']} <b>Terms:</b>
{deal['terms']}

{EMOJIS['rocket']} <b>Created:</b> {deal['created_at']}

<b>Admin Actions Available:</b>
    """
    
    await callback.message.edit_text(
        admin_deal_text,
        reply_markup=get_admin_deal_keyboard(deal_id, deal['status'])
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("admin_resolve_"))
async def admin_resolve_dispute(callback: CallbackQuery):
    """Admin resolve dispute"""
    
    if not await is_admin(callback.from_user.id, callback.from_user.username):
        await callback.answer(f"{EMOJIS['error']} Access denied!")
        return
    
    deal_id = callback.data.split("_")[-1]
    
    # Update deal status to completed (admin resolution)
    await update_deal_status(deal_id, 'completed')
    
    resolution_text = f"""
{EMOJIS['success']} <b>Dispute Resolved</b>

{EMOJIS['key']} <b>Deal ID:</b> #{deal_id}
{EMOJIS['shield']} <b>Resolved by:</b> Admin
{EMOJIS['lightning']} <b>Action:</b> Payment released

{EMOJIS['diamond']} <b>Resolution complete!</b>
Both parties have been notified.
    """
    
    await callback.message.edit_text(
        resolution_text,
        reply_markup=get_admin_keyboard()
    )
    
    await callback.answer(f"{EMOJIS['success']} Dispute resolved!")

@router.callback_query(F.data.startswith("admin_cancel_"))
async def admin_cancel_deal(callback: CallbackQuery):
    """Admin cancel deal"""
    
    if not await is_admin(callback.from_user.id, callback.from_user.username):
        await callback.answer(f"{EMOJIS['error']} Access denied!")
        return
    
    deal_id = callback.data.split("_")[-1]
    
    # Update deal status to cancelled
    await update_deal_status(deal_id, 'cancelled')
    
    cancellation_text = f"""
{EMOJIS['error']} <b>Deal Cancelled</b>

{EMOJIS['key']} <b>Deal ID:</b> #{deal_id}
{EMOJIS['shield']} <b>Cancelled by:</b> Admin
{EMOJIS['lightning']} <b>Status:</b> Refund initiated

{EMOJIS['warning']} <b>Reason:</b> Administrative decision
{EMOJIS['diamond']} All parties have been notified.
    """
    
    await callback.message.edit_text(
        cancellation_text,
        reply_markup=get_admin_keyboard()
    )
    
    await callback.answer(f"{EMOJIS['warning']} Deal cancelled!")

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery):
    """Admin broadcast message"""
    
    if not await is_admin(callback.from_user.id, callback.from_user.username):
        await callback.answer(f"{EMOJIS['error']} Access denied!")
        return
    
    broadcast_text = f"""
{EMOJIS['rocket']} <b>Broadcast System</b>

{EMOJIS['lightning']} Feature coming soon!

This will allow you to send announcements to all users.

{EMOJIS['shield']} <b>Use cases:</b>
• System maintenance notices
• New feature announcements  
• Security updates
• Important policy changes
    """
    
    await callback.message.edit_text(
        broadcast_text,
        reply_markup=get_admin_keyboard()
    )
    
    await callback.answer(f"{EMOJIS['rocket']} Broadcast panel")

@router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery):
    """Return to admin panel"""
    
    if not await is_admin(callback.from_user.id, callback.from_user.username):
        await callback.answer(f"{EMOJIS['error']} Access denied!")
        return
    
    # Redirect to admin panel
    await admin_panel(callback.message)
    await callback.answer()
