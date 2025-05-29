from aiogram import F, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from db.session import SessionLocal
from keyboards.inline import get_personal_account
from models.bases import Profile
from states.fsm import CandidateRegistration
from states.registration import Registration


def registration_handlers(dp: Dispatcher):
    from aiogram import F

    @dp.callback_query(F.data.startswith("role_"))
    async def handle_role(callback: CallbackQuery, state: FSMContext):
        role = callback.data.split("_")[1]
        await state.update_data(role=role)

        if role == "candidate":
            await callback.message.answer("Для регистрации под ролью \"КАНДИДАТ\" необходимо ввести имя. \n\nВведите Ваше имя:")
            await state.set_state(CandidateRegistration.waiting_for_name)
        elif role == "recruiter":
            await callback.message.answer(
                "Для регистрации под ролью \"РЕКРУТЕР\" необходимо ввести имя, компанию и должность. Если нет данных для ввода, то введите прочерк."
                "\n\nВведите Ваше имя:")

            await state.set_state(Registration.waiting_for_name)

        await callback.answer()

    @dp.message(Registration.waiting_for_name)
    async def process_name(message: Message, state: FSMContext):
        name = message.text.strip()
        if not name:
            await message.answer("Имя не может быть пустым. Введите имя.")
            return
        await state.update_data(name=name)
        await message.answer("Введите название компании:")
        await state.set_state(Registration.waiting_for_company)

    @dp.message(Registration.waiting_for_company)
    async def process_company(message: Message, state: FSMContext):
        company = message.text.strip()
        if not company:
            await message.answer("Название компании не может быть пустым.")
            return
        await state.update_data(company=company)
        await message.answer("Введите вашу должность:")
        await state.set_state(Registration.waiting_for_position)


    @dp.message(Registration.waiting_for_position)
    async def process_position(message: Message, state: FSMContext):
        position = message.text.strip()
        if not position:
            await message.answer("Должность не может быть пустой.")
            return

        await state.update_data(position=position)
        data = await state.get_data()

        async with SessionLocal() as session:
            new_profile = Profile(
                telegram_id=message.from_user.id,
                name=data["name"],
                company=data["company"],
                position=data["position"],
                role=data["role"]
            )
            session.add(new_profile)
            await session.commit()

        await message.answer(
            f"Вы успешно зарегистрировались!\n\n"
            f"Ваши данные после регистрации:\n"
            f"Имя: {data['name']}\n"
            f"Компания: {data['company']}\n"
            f"Должность: {data['position']}\n"
            f"Роль: {'Рекрутер' if data['role'] == 'recruiter' else 'Кандидат'}\n\n"
            f"Перейдите в личный кабинет для продолжения работы 👇",
            reply_markup=get_personal_account()
        )

        await state.clear()
