from aiogram import F, Dispatcher
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy.future import select
from models.bases import Profile
from db.session import SessionLocal
from states.fsm import QuestionnairePassing
from states.registration import Registration
from keyboards.inline import get_role_keyboard, get_personal_account

def start_handlers(dp: Dispatcher):
    @dp.message(F.text == "/start")
    async def cmd_start(message: Message, state: FSMContext):
        user_id = message.from_user.id
        async with SessionLocal() as session:
            result = await session.execute(select(Profile).where(Profile.telegram_id == user_id))
            profile = result.scalars().first()

        if profile:
            if profile.role == "recruiter":
                role_text = "РЕКРУТЕР"
                await message.answer(f"С возвращением, {profile.name}!\nВы вошли под ролью \"{role_text}\"", reply_markup=get_personal_account())
                await state.clear()
            else:
                role_text = "КАНДИДАТ"
                await message.answer(f"С возвращением, {profile.name}!\nВы вошли под ролью \"{role_text}\". \n\nОтправьте в чат код опросника, чтобы его пройти!")
                await state.set_state(QuestionnairePassing.waiting_for_code)
        else:
            photo_start = FSInputFile("img/start.png")
            await message.answer_photo(photo=photo_start, caption="Приветствуем в чат-боте \"АНАЛИЗ ИНТЕРВЬЮ: ОБЩЕЕ - ЧАСТНОЕ\"\n\nВыберите ниже роль, под которой хотите продолжить работу 👥", reply_markup=get_role_keyboard())
            await state.set_state(Registration.waiting_for_role)