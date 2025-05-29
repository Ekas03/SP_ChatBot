from aiogram import F, Dispatcher
from aiogram.types import CallbackQuery
from sqlalchemy import select

from db.session import SessionLocal
from keyboards.inline import get_menu
from models.bases import Profile

def my_personal_account(dp: Dispatcher):
    @dp.callback_query(F.data == "my_account")
    async def show_my_profile(callback: CallbackQuery):
        async with SessionLocal() as session:
            result = await session.execute(
                select(Profile).where(Profile.telegram_id == callback.from_user.id)
            )
            profile = result.scalar_one_or_none()

        await callback.message.edit_text(
            text=f"*ЛИЧНЫЙ КАБИНЕТ* 👤\n\n"
                 f"*Имя:* {profile.name}\n"
                 f"*Компания:* {profile.company or '—'}\n"
                 f"*Должность:* {profile.position or '—'}\n"
                 f"*Роль:* Рекрутер",
            reply_markup=get_menu(),
            parse_mode="Markdown"
        )

        await callback.answer()

