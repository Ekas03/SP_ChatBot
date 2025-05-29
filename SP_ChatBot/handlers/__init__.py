from aiogram import Dispatcher
from .analyzer import analyzer
from .candidate import candidate_handlers
from .questionnaire_pass import questionnaire_pass_handlers
from .start import start_handlers
from .registration import registration_handlers
from .delete_account import delete_account_handlers
from .fall import fallback_handlers
from .questionnaire import questionnaire_handlers
from .personal_account import my_personal_account


def register_all_handlers(dp: Dispatcher):
    start_handlers(dp)
    candidate_handlers(dp)
    registration_handlers(dp)
    analyzer(dp)
    questionnaire_handlers(dp)
    questionnaire_pass_handlers(dp)
    my_personal_account(dp)
    delete_account_handlers(dp)
    fallback_handlers(dp)
