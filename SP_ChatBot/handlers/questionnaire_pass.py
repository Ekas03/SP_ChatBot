from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from db.session import SessionLocal
from keyboards.inline import get_review_keyboard, get_edit_answer_keyboard
from models.bases import Questionnaire, Question, Answer
from states.fsm import QuestionnairePassing

def questionnaire_pass_handlers(dp: Dispatcher):

    @dp.message(QuestionnairePassing.waiting_for_code, lambda message: not message.text.startswith("/"))
    async def load_questionnaire(message: Message, state: FSMContext):
        code = message.text.strip()

        async with SessionLocal() as session:
            result = await session.execute(
                select(Questionnaire).where(Questionnaire.code == code)
            )
            questionnaire = result.scalar_one_or_none()

            if questionnaire is None:
                await message.answer("❌ Опросник с таким кодом не найден. Попробуйте ввести код опросника ещё раз:")
                return

            result = await session.execute(
                select(Answer).filter(
                    Answer.respondent_id == message.from_user.id,
                    Answer.questionnaire_id == questionnaire.id
                )
            )
            existing_answer = result.scalars().first()  # здесь исправил имя переменной

            if existing_answer:
                await message.answer("⚠️ Вы уже проходили этот опросник! Попробуйте ввести код опросника ещё раз:")
                return

            result = await session.execute(
                select(Question).where(Question.questionnaire_id == questionnaire.id).order_by(Question.id)
            )
            questions = result.scalars().all()

            if not questions:
                await message.answer("У этого опросника нет вопросов.")
                return

        await state.update_data(
            questionnaire_id=questionnaire.id,
            questions=[(q.id, q.text) for q in questions],
            current=0,
            answers=[]
        )
        await message.answer(
            f"Опросник «{questionnaire.title}» \n\nОтвечайте на вопросы максимально развернуто, долго не раздумывая над формулировкой, так как наиболее живой ответ даст наиболее верный результат! \n\nУспехов! \n\nВопрос №1:\n{questions[0].text}"
        )
        await state.set_state(QuestionnairePassing.answering_questions)

    @dp.message(QuestionnairePassing.answering_questions)
    async def process_answer(message: Message, state: FSMContext):
        data = await state.get_data()
        answers = data["answers"]
        questions = data["questions"]
        current = data["current"]
        editing = data.get("editing", False)

        question_id, _ = questions[current]
        if current < len(answers):
            answers[current] = (question_id, message.text)  # редактирование
        else:
            answers.append((question_id, message.text))  # добавление нового

        await state.update_data(answers=answers)

        if editing:
            text = "📝 Ваши ответы (после редактирования):\n\n" + "\n".join(
                [f"{i + 1}. {q_text}\n {ans}" for i, ((_, q_text), (_, ans)) in enumerate(zip(questions, answers))]
            )
            await message.answer(text, reply_markup=get_review_keyboard())
            await state.set_state(QuestionnairePassing.reviewing)
            await state.update_data(editing=False)  # сбрасываем флаг
        else:
            current += 1
            if current >= len(questions):
                await state.update_data(current=current, answers=answers)
                text = "📝 Проверьте свои ответы и внесите изменения, если хотите:\n\n" + "\n".join(
                    [f"{i + 1}. {q_text}\n- {ans}" for i, ((_, q_text), (_, ans)) in
                     enumerate(zip(questions, answers))]
                )
                await message.answer(text, reply_markup=get_review_keyboard())
                await state.set_state(QuestionnairePassing.reviewing)
            else:
                next_q_text = questions[current][1]
                await state.update_data(current=current, answers=answers)
                await message.answer(f"Вопрос №{current + 1}:\n{next_q_text}")

    @dp.callback_query(F.data == "confirm_answers")
    async def confirm_answers(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        await save_answers(
            respondent_id=callback.from_user.id,
            questionnaire_id=data["questionnaire_id"],
            answers=data["answers"]
        )
        await callback.message.edit_text("✅ Спасибо, Ваши ответы сохранены и отправлены рекрутеру! \n\nЕсли у Вас есть код от другого опросника, то просто отправьте его в чат:")
        await state.clear()
        await callback.answer()

    @dp.callback_query(F.data.startswith("edit_answer:"))
    async def edit_answer(callback: CallbackQuery, state: FSMContext):
        index = int(callback.data.split(":")[1])
        data = await state.get_data()
        question_text = data["questions"][index][1]

        await state.update_data(
            current=index,
            editing=True
        )

        await callback.message.edit_text(f"✏️ Перепишите ответ на вопрос: {question_text}")
        await state.set_state(QuestionnairePassing.answering_questions)
        await callback.answer()

    @dp.callback_query(F.data == "edit_menu")
    async def edit_menu(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        questions = data["questions"]
        await callback.message.edit_text("Выберите ответ для редактирования:", reply_markup=get_edit_answer_keyboard(questions))
        await callback.answer()

async def save_answers(respondent_id: int, questionnaire_id: int, answers: list[tuple[int, str]]):
    async with SessionLocal() as session:
        for question_id, answer_text in answers:
            session.add(Answer(
                respondent_id=respondent_id,
                questionnaire_id=questionnaire_id,
                question_id=question_id,
                answer_text=answer_text
            ))
        await session.commit()