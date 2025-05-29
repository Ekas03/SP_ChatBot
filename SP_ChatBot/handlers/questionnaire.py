import re
import string
import random
from aiogram import Dispatcher, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, delete

from db.session import SessionLocal
from handlers.analyzer import analyze_and_save
from keyboards.inline import get_back_to_count_keyboard, get_question_list_keyboard, get_main_menu_keyboard, \
    get_questionnaire_list_keyboard, get_questionnaire_view_keyboard, get_edit_questionnaire_keyboard, \
    get_cancel_creation_keyboard, get_back_to_creation_keyboard, get_question_view_keyboard, \
    get_updated_question_list_keyboard, get_back_to_analysis_menu_keyboard, get_back_to_questionnaires
from models.bases import Questionnaire, Question, Profile, Answer
from states.fsm import QuestionnaireCreation

import nltk
nltk.download('punkt')

MAX_QUESTIONS = 10


def questionnaire_handlers(dp: Dispatcher):
    @dp.callback_query(F.data == "create_questionnaire")
    async def show_main_menu(callback: CallbackQuery):
        await callback.message.edit_text("Выберите действие:", reply_markup=get_main_menu_keyboard())
        await callback.answer()

    @dp.callback_query(F.data == "my_questionnaires")
    async def show_my_questionnaires(callback: CallbackQuery):
        async with SessionLocal() as session:
            result = await session.execute(
                select(Profile).filter_by(telegram_id=callback.from_user.id)
            )
            profile = result.scalars().first()

            if not profile:
                await callback.message.edit_text(
                    "Сначала создайте хотя бы один опросник.",
                    reply_markup=get_back_to_creation_keyboard()
                )
                await callback.answer()
                return

            result = await session.execute(
                select(Questionnaire).where(Questionnaire.recruiter_id == profile.id)
            )
            questionnaires = result.scalars().all()

            if not questionnaires:
                await callback.message.edit_text(
                    "У вас пока нет созданных опросников.",
                    reply_markup=get_back_to_creation_keyboard()
                )
            else:
                await callback.message.edit_text(
                    "📋 Ваши опросники:",
                    reply_markup=get_questionnaire_list_keyboard(questionnaires)
                )

        await callback.answer()

    @dp.callback_query(F.data.startswith("view_q:"))
    async def handle_questionnaire_view(callback: CallbackQuery, state: FSMContext):
        q_id = int(callback.data.split(":")[1])
        async with SessionLocal() as session:
            result = await session.execute(select(Questionnaire).where(Questionnaire.id == q_id))
            q = result.scalar_one_or_none()

            if q is None:
                await callback.message.edit_text("Опросник не найден.")
                await callback.answer()
                return

            await state.update_data(edit_q_id=q.id)

            await callback.message.edit_text(
                f"📝 *{q.title}*\nКод: `{q.code}`",
                parse_mode="Markdown",
                reply_markup=get_questionnaire_view_keyboard()
            )
            await callback.answer()

    @dp.callback_query(F.data == "delete_q")
    async def delete_questionnaire(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        data = await state.get_data()
        q_id = data.get("edit_q_id")

        if not q_id:
            await callback.message.edit_text("❌ Ошибка: не выбран опросник для удаления.")
            return

        async with SessionLocal() as session:
            await session.execute(
                delete(Answer).where(
                    Answer.question_id.in_(
                        select(Question.id).where(Question.questionnaire_id == q_id)
                    )
                )
            )

            await session.execute(
                delete(Question).where(Question.questionnaire_id == q_id)
            )

            await session.execute(
                delete(Questionnaire).where(Questionnaire.id == q_id)
            )

            await session.commit()

            result = await session.execute(
                select(Questionnaire).where(Questionnaire.recruiter_id == callback.from_user.id)
            )
            questionnaires = result.scalars().all()

        await callback.message.edit_text(
            "Опросник удален!",
            reply_markup=get_questionnaire_list_keyboard(questionnaires)
        )

    @dp.callback_query(F.data == "edit_existing_q")
    async def edit_existing_questionnaire(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        q_id = data.get("edit_q_id")

        async with SessionLocal() as session:
            questionnaire_result = await session.execute(
                select(Questionnaire).where(Questionnaire.id == q_id)
            )
            questionnaire = questionnaire_result.scalar_one_or_none()

            if questionnaire is None:
                await callback.message.edit_text("Опросник не найден.")
                return

            question_result = await session.execute(
                select(Question).where(Question.questionnaire_id == q_id)
            )
            questions = question_result.scalars().all()

        questions_text = [q.text for q in questions]

        await state.update_data(
            questions=questions_text,
            current_index=len(questions_text) + 1,
            question_count=len(questions_text),
            editing_index=None,
            title=questionnaire.title
        )

        await callback.message.edit_text("Выберите опросник, который хотите отредактировать:", reply_markup=get_edit_questionnaire_keyboard(questions_text, questionnaire))
        await state.set_state(QuestionnaireCreation.review_questions)
        await callback.answer()

    @dp.callback_query(F.data == "start_creation")
    async def start_creation(callback: CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id

        async with SessionLocal() as session:
            result = await session.execute(
                select(Questionnaire).where(Questionnaire.recruiter_id == user_id)
            )
            user_questionnaires = result.scalars().all()

        if len(user_questionnaires) >= 10:
            await callback.message.edit_text("У вас уже есть 10 опросников. Удалите один из них, чтобы создать новый.")
            await callback.answer()
            return

        await callback.message.edit_text("Введите название опросника:", reply_markup=get_cancel_creation_keyboard())
        await state.set_state(QuestionnaireCreation.waiting_for_title)
        await callback.answer()

    @dp.message(QuestionnaireCreation.waiting_for_title)
    async def receive_title(message: Message, state: FSMContext):
        await state.update_data(title=message.text)
        await message.answer(
            "Сколько вопросов должно быть в опроснике? (до 10)",
            reply_markup=get_back_to_creation_keyboard()
        )
        await state.set_state(QuestionnaireCreation.waiting_for_count)

    @dp.message(QuestionnaireCreation.waiting_for_count)
    async def receive_count(message: Message, state: FSMContext):
        try:
            count = int(message.text)
            if not (1 <= count <= MAX_QUESTIONS):
                raise ValueError
        except ValueError:
            await message.answer("Пожалуйста, введите число от 1 до 10.")
            return

        await state.update_data(question_count=count, questions=[], current_index=1)
        await message.answer("Введите вопрос №1:", reply_markup=get_back_to_count_keyboard())
        await state.set_state(QuestionnaireCreation.waiting_for_questions)

    @dp.callback_query(F.data == "cancel_creation")
    async def cancel_creation(callback: CallbackQuery, state: FSMContext):
        await state.clear()
        await callback.message.edit_text("Создание опросника отменено!", )
        await callback.answer()

    @dp.callback_query(F.data == "back_to_count")
    async def back_to_count(callback: CallbackQuery, state: FSMContext):
        await callback.message.edit_text("Сколько вопросов должно быть в опроснике? (до 10)")
        await state.set_state(QuestionnaireCreation.waiting_for_count)
        await callback.answer()

    @dp.message(QuestionnaireCreation.waiting_for_questions)
    async def receive_question(message: Message, state: FSMContext):
        data = await state.get_data()
        questions = data.get("questions", [])
        current_index = data.get("current_index", 1)
        total = data.get("question_count")

        questions.append(message.text)
        await state.update_data(questions=questions, current_index=current_index + 1)

        if len(questions) < total:
            await message.answer(
                f"Введите вопрос №{current_index + 1}:",
                reply_markup=get_back_to_count_keyboard()
            )
        else:
            await message.answer(
                "Все вопросы добавлены. Выберите вопрос для просмотра/редактирования или сохраните опросник:",
                reply_markup=get_question_list_keyboard(questions)
            )
            await state.set_state(QuestionnaireCreation.review_questions)

    @dp.callback_query(F.data.startswith("view_question_"))
    async def view_question(callback: CallbackQuery, state: FSMContext):
        index = int(callback.data.split("_")[-1])
        data = await state.get_data()
        question = data["questions"][index]

        await callback.message.edit_text(f"Вопрос №{index + 1}:\n{question}",
                                      reply_markup=get_question_view_keyboard(index))

    @dp.callback_query(F.data == "back_to_question_list")
    async def back_to_question_list(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        questions = data.get("questions", [])

        await callback.message.edit_text("Обновленный список вопросов:",
                                      reply_markup=get_updated_question_list_keyboard(questions))
        await state.set_state(QuestionnaireCreation.review_questions)
        await callback.answer()

    @dp.callback_query(F.data.startswith("edit_question_"))
    async def edit_question(callback: CallbackQuery, state: FSMContext):
        index = int(callback.data.split("_")[-1])
        data = await state.get_data()
        questions = data.get("questions", [])
        await state.update_data(editing_index=index)
        await callback.message.edit_text(f"Прошлый текст вопроса: {questions[index]} \nВведите новый текст вопроса:")
        await state.set_state(QuestionnaireCreation.editing_question)
        await callback.answer()

    @dp.message(QuestionnaireCreation.editing_question)
    async def save_edited_question(message: Message, state: FSMContext):
        data = await state.get_data()
        index = data["editing_index"]
        questions = data["questions"]
        questions[index] = message.text
        await state.update_data(questions=questions)

        await message.answer(
            "Вопрос обновлен. Обновленный список вопросов:",
            reply_markup=get_updated_question_list_keyboard(questions)
        )
        await state.set_state(QuestionnaireCreation.review_questions)

    @dp.callback_query(F.data == "confirm_save")
    async def confirm_save(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        title = data.get("title")
        questions = data.get("questions", [])
        edit_q_id = data.get("edit_q_id")

        if not title or not questions:
            await callback.message.edit_text("Название и вопросы не должны быть пустыми.")
            return

        async with SessionLocal() as session:
            result = await session.execute(
                select(Profile).filter_by(telegram_id=callback.from_user.id)
            )
            profile = result.scalars().first()
            if not profile:
                profile = Profile(
                    telegram_id=callback.from_user.id,
                    name=callback.from_user.full_name
                )
                session.add(profile)
                await session.flush()  # Получаем profile.id

            if edit_q_id:
                questionnaire = await session.get(Questionnaire, edit_q_id)
                if questionnaire is None:
                    await callback.message.edit_text("Опросник не найден.")
                    return

                questionnaire.title = title
                await session.execute(
                    delete(Answer).where(
                        Answer.question_id.in_(
                            select(Question.id).where(Question.questionnaire_id == edit_q_id)
                        )
                    )
                )
                await session.execute(
                    delete(Question).where(Question.questionnaire_id == edit_q_id)
                )
                for text in questions:
                    session.add(Question(text=text, questionnaire_id=edit_q_id))

            else:
                code = generate_code()
                questionnaire = Questionnaire(
                    recruiter_id=profile.id,
                    title=title,
                    code=code
                )
                session.add(questionnaire)
                await session.flush()
                for text in questions:
                    session.add(Question(text=text, questionnaire_id=questionnaire.id))

            await session.commit()

        await state.clear()
        await callback.answer()

        if questionnaire is None:
            await callback.message.edit_text("Произошла ошибка при сохранении опросника.")
            return

        await callback.message.answer(
            f"Чтобы пройти опросник, Вам необходимо:"
            f"\n\n1. Перейти в чат-бот @genspecbot"
            f"\n\n2. Зарегистрироваться под ролью \"КАНДИДАТ\""
            f"\n\n3. Ввести код опросника: <code>{questionnaire.code}</code> и ответить на вопросы\n",
            parse_mode="HTML"
        )

        await callback.message.answer(
            "Опросник успешно сохранен! ✅ \n\nВыше сгенерировано приглашение с инструкцией прохождения опросника - отправьте его кандидату!",
            reply_markup=get_edit_questionnaire_keyboard(questions, questionnaire)
        )


    @dp.callback_query(F.data == "user_answers")
    async def show_users_with_answers(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        questionnaire_id = data.get("edit_q_id")

        async with SessionLocal() as session:
            result = await session.execute(
                select(Answer.respondent_id)
                .where(Answer.questionnaire_id == questionnaire_id)
                .distinct()
            )
            user_ids = [row[0] for row in result.all()]

            if not user_ids:
                await callback.message.edit_text("Нет пользователей с ответами!", reply_markup=get_back_to_questionnaires())
                return

            result = await session.execute(
                select(Profile.telegram_id, Profile.name).where(Profile.telegram_id.in_(user_ids))
            )
            users = result.all()
            user_names = {uid: name for uid, name in users}
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
            [InlineKeyboardButton(text=user_names.get(uid, str(uid)), callback_data=f"answers_of:{uid}")]
            for uid in user_ids] +
            [[InlineKeyboardButton(text="🔙 Назад", callback_data=f"view_q:{questionnaire_id}")]]
        )

        await callback.message.edit_text("Выберите пользователя:", reply_markup=keyboard)

    @dp.callback_query(F.data.startswith("answers_of:"))
    async def show_user_answers(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        questionnaire_id = data.get("edit_q_id")

        if questionnaire_id is None:
            await callback.message.edit_text("Ошибка: не выбран опросник.")
            await callback.answer()
            return

        try:
            telegram_id = int(callback.data.split(":")[1])
        except (IndexError, ValueError):
            await callback.message.edit_text("Некорректные данные.")
            await callback.answer()
            return

        async with SessionLocal() as session:
            profile = await session.execute(
                select(Profile).where(Profile.telegram_id == telegram_id)
            )
            profile_obj = profile.scalar_one_or_none()
            user_display_name = (
                profile_obj.name
                if profile_obj and profile_obj.name
                else f"Кандидат {telegram_id}"
            )

            result_answers = await session.execute(
                select(Answer)
                .where(
                    Answer.questionnaire_id == questionnaire_id,
                    Answer.respondent_id == telegram_id
                )
            )
            answers = result_answers.scalars().all()

            if not answers:
                await callback.message.edit_text("Ответы не найдены.")
                await callback.answer()
                return

            result_questions = await session.execute(
                select(Question).where(Question.questionnaire_id == questionnaire_id)
            )
            questions = result_questions.scalars().all()

        question_dict = {q.id: q.text for q in questions}

        full_text = ""
        for a in answers:
            question_text = question_dict.get(a.question_id)
            full_text += f"{a.answer_text}\n"

        full_text = full_text[:4096]

        await state.update_data(analyze_text=full_text, analyze_title=f"Кандидат {user_display_name}")

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Анализировать", callback_data="analyze_answers_now")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="user_answers")]
        ])

        await callback.message.edit_text(full_text, reply_markup=keyboard)
        await callback.answer()

    def split_into_sentences(text: str) -> list[str]:
        sentences = re.split(r'(?<=[.!?])[\s\n]+', text.strip())
        return [s.strip() for s in sentences if s.strip()]

    @dp.callback_query(F.data == "analyze_answers_now")
    async def analyze_user_answers(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        full_text = data.get("analyze_text")
        title = data.get("analyze_title")

        if not full_text:
            await callback.message.edit_text("Ошибка: отсутствует текст для анализа.")
            await callback.answer()
            return

        try:
            msg, _ = await analyze_and_save(full_text, callback.from_user.id, title)
        except Exception as e:
            await callback.message.edit_text(str(e))
            await callback.answer()
            return

        await callback.message.edit_text(msg, reply_markup=get_back_to_analysis_menu_keyboard())
        await callback.answer()
        await state.clear()


def generate_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

async def save_questionnaire(recruiter_id: int, title: str, questions: list[str], message: Message):
    async with SessionLocal() as session:
        while True:
            code = generate_code()
            existing = await session.execute(
                select(Questionnaire).where(Questionnaire.code == code)
            )
            if existing.scalar_one_or_none() is None:
                break

        q = Questionnaire(recruiter_id=recruiter_id, title=title, code=code)
        session.add(q)
        await session.flush()

        for text in questions:
            question = Question(questionnaire_id=q.id, text=text)
            session.add(question)

        await session.commit()
        await message.edit_text(f"✅ Опросник сохранён!\nКод: `{q.code}`", parse_mode="Markdown")

