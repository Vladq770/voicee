from aiogram.dispatcher.filters.state import State, StatesGroup


class UserForm(StatesGroup):  # type: ignore[misc]
    name = State()
    info = State()
    photo = State()
