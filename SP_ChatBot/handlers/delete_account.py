from aiogram import F, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, delete
from db.session import SessionLocal
from keyboards.inline import get_personal_account
from models.bases import Profile, Questionnaire, Answer, Question


def get_delete_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟥 Удалить аккаунт", callback_data="confirm_delete")],
        [InlineKeyboardButton(text="🟩 Отмена", callback_data="cancel_delete")]
    ])


def delete_account_handlers(dp: Dispatcher):
    @dp.message(F.text == "/delete_account")
    async def cmd_delete_account(message: Message):
        user_id = message.from_user.id

        async with SessionLocal() as session:
            result = await session.execute(select(Profile).where(Profile.telegram_id == user_id))
            profile = result.scalars().first()

        if not profile:
            await message.answer("⚠️ Профиль не найден. Создайте аккаунт по команде Начать - /start")
            return

        await message.answer(
            "⚠️ Вы уверены, что хотите удалить аккаунт? Это действие необратимо.",
            reply_markup=get_delete_confirmation_keyboard()
        )

    @dp.callback_query(F.data == "confirm_delete")
    async def confirm_delete(callback: CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id

        async with SessionLocal() as session:
            result = await session.execute(
                select(Profile).where(Profile.telegram_id == user_id)
            )
            profile = result.scalars().first()

            if not profile:
                await callback.message.edit_text("⚠️ Профиль не найден. Создайте аккаунт по команде Начать - /start")
                return

            if profile.role == "recruiter":
                result = await session.execute(
                    select(Questionnaire.id).where(Questionnaire.recruiter_id == profile.id)
                )
                questionnaire_ids = [row[0] for row in result.fetchall()]

                if questionnaire_ids:
                    await session.execute(delete(Answer).where(Answer.questionnaire_id.in_(questionnaire_ids)))
                    await session.execute(delete(Question).where(Question.questionnaire_id.in_(questionnaire_ids)))
                    await session.execute(delete(Questionnaire).where(Questionnaire.id.in_(questionnaire_ids)))

            await session.delete(profile)
            await session.commit()

        await callback.message.edit_text("✅ Ваш аккаунт и связанные данные были удалены.")
        await state.clear()
        await callback.answer()

    @dp.callback_query(F.data == "cancel_delete")
    async def cancel_delete(callback: CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id

        async with SessionLocal() as session:
            result = await session.execute(
                select(Profile).where(Profile.telegram_id == user_id)
            )
            profile = result.scalars().first()

            if profile and profile.role == "candidate":
                await callback.message.edit_text(
                    "Удаление отменено! \n\nЕсли у Вас есть код опросника от рекрутера, то просто отправьте мне его:"
                )
            else:
                await callback.message.edit_text(
                    "Удаление отменено.",
                    reply_markup=get_personal_account()
                )

        await state.clear()
        await callback.answer()

