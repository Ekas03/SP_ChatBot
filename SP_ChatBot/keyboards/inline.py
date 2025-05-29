from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_role_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Рекрутер", callback_data="role_recruiter"),
            InlineKeyboardButton(text="Кандидат", callback_data="role_candidate")
        ]
    ])


def get_personal_account():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Личный кабинет", callback_data="my_account")]
    ])

def get_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊Анализ интервью", callback_data="analysis")],
        [InlineKeyboardButton(text="📋Опросник", callback_data="create_questionnaire")]
    ])


def get_main_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Мои опросники", callback_data="my_questionnaires"),
             InlineKeyboardButton(text="➕ Добавить", callback_data="start_creation")
            ],
            [InlineKeyboardButton(text="Назад", callback_data="my_account")]]
    )


def get_questionnaire_view_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_existing_q"),
             InlineKeyboardButton(text="Назад", callback_data="my_questionnaires")],
            [InlineKeyboardButton(text="Ответы пользователя", callback_data="user_answers")],
            [InlineKeyboardButton(text="🗑 Удалить", callback_data="delete_q")]
        ]
    )


def get_back_to_count_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_count")]
        ]
    )


def get_question_list_keyboard(questions):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"📝 {i + 1}. {q[:10]}", callback_data=f"view_question_{i}")]
            for i, q in enumerate(questions)
        ] + [[InlineKeyboardButton(text="✅ Сохранить опросник", callback_data="confirm_save")]]
    )


def get_cancel_creation_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="create_questionnaire")]
        ]
    )

def get_questionnaire_list_keyboard(questionnaires):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=q.title, callback_data=f"view_q:{q.id}")]
            for q in questionnaires
        ] + [[InlineKeyboardButton(text="🔙 Назад", callback_data="create_questionnaire")]]
    )

def get_edit_questionnaire_keyboard(questions, questionnaires):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"📝 {i + 1}. {q[:10]}", callback_data=f"view_question_{i}")]
            for i, q in enumerate(questions)
        ] + [[InlineKeyboardButton(text="🔖 Карточка опросника", callback_data=f"view_q:{questionnaires.id}")]]
    )

def get_back_to_creation_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="create_questionnaire")]
        ]
    )

def get_back_to_questionnaires():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к опросникам", callback_data="my_questionnaires")]
        ]
    )

def get_question_view_keyboard(index):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_question_{index}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="edit_existing_q")]
        ]
    )

def get_updated_question_list_keyboard(questions):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"📝 {i + 1}. {q[:10]}", callback_data=f"view_question_{i}")]
            for i, q in enumerate(questions)
        ] + [[InlineKeyboardButton(text="✅ Сохранить опросник", callback_data="confirm_save")]]
    )

def get_review_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_answers")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_menu")]
    ])

def get_edit_answer_keyboard(questions):
    keyboard = []
    for i, (_, q_text) in enumerate(questions):
        keyboard.append([
            InlineKeyboardButton(text=f"✏️ Изменить ответ №{i + 1}", callback_data=f"edit_answer:{i}")
        ])
    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="review_answers")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_analysis_menu_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊Проанализировать интервью", callback_data="analyze_interview")],
        [InlineKeyboardButton(text="📒Мои интервью", callback_data="my_interviews")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="my_account")]
    ])
    return keyboard


def get_back_to_analysis_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="my_account")]
        ]
    )
def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Личный кабинет", callback_data="open_profile")]
    ])

def profile_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пройти опросник", callback_data="start_questionnaire")],
        [InlineKeyboardButton(text="Удалить аккаунт", callback_data="delete_account")]
    ])

def cancel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
    ])
