from aiogram.fsm.state import StatesGroup, State

class QuestionnaireCreation(StatesGroup):
    waiting_for_title = State()
    waiting_for_count = State()
    waiting_for_questions = State()
    review_questions = State()
    editing_question = State()

class QuestionnairePassing(StatesGroup):
    waiting_for_code = State()
    answering_questions = State()

class InterviewAnalysis(StatesGroup):
    waiting_for_title = State()
    waiting_for_docx = State()

class CandidateRegistration(StatesGroup):
    waiting_for_name = State()
    waiting_for_delete_code = State()