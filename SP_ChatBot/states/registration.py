# Состояния
from aiogram.fsm.state import StatesGroup, State


class Registration(StatesGroup):
    waiting_for_role = State()
    waiting_for_name = State()
    waiting_for_company = State()
    waiting_for_position = State()