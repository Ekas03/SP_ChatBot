from aiogram import F, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select

from db.session import SessionLocal
from models.bases import Profile
from states.fsm import QuestionnairePassing

async def ask_code(message: Message, state: FSMContext):
    await state.set_state(QuestionnairePassing.waiting_for_code)

def fallback_handlers(dp: Dispatcher):
    @dp.message(F.text)
    async def fallback_message(message: Message, state: FSMContext):
        user_id = message.from_user.id

        async with SessionLocal() as session:
            result = await session.execute(select(Profile).where(Profile.telegram_id == user_id))
            profile = result.scalars().first()

        if profile is None or profile.role == "recruiter":
            await message.answer("Пожалуйста, используйте команду Начать - /start, чтобы использовать функционал бота! 👾")
        else:
            await ask_code(message, state)

