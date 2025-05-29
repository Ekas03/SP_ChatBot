from aiogram import Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile
from db.session import SessionLocal
from models.bases import Profile
from states.fsm import CandidateRegistration, QuestionnairePassing


def candidate_handlers(dp: Dispatcher):
    @dp.message(CandidateRegistration.waiting_for_name)
    async def process_name(message: Message, state: FSMContext):
        name = message.text.strip()
        if not name:
            await message.answer("Имя не может быть пустым. Попробуйте ещё раз:")
            return

        async with SessionLocal() as session:
            profile = Profile(
                telegram_id=message.from_user.id,
                name=name,
                role="candidate"
            )
            session.add(profile)
            await session.commit()

        photo = FSInputFile("img/lk_candidate.png")
        await message.answer_photo(photo=photo,
                                   caption=f"{name}, Вы зарегистрированы под ролью\"КАНДИДАТ\"! \n\nВведите в чат код опросника, который хотите пройти:")
        await state.set_state(QuestionnairePassing.waiting_for_code)



