
"""
FSM состояния для админ-панели
"""
from aiogram.fsm.state import State, StatesGroup

class BrandStates(StatesGroup):
    """Состояния для управления брендами"""
    add_name = State()
    edit_select = State()
    edit_name = State()
    delete_select = State()
    delete_confirm = State()

class CategoryStates(StatesGroup):
    """Состояния для управления категориями"""
    add_name = State()
    edit_select = State()
    edit_name = State()
    delete_select = State()
    delete_confirm = State()

class ProductStates(StatesGroup):
    """Состояния для управления товарами"""
    add_brand = State()
    add_category = State()
    add_name = State()
    add_price = State()
    add_photo = State()
    add_description = State()
    edit_select = State()
    edit_field = State()
    delete_select = State()
    delete_confirm = State()

