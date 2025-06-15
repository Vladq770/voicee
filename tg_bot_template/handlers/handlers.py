from typing import Any

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.utils.exceptions import BotBlocked

from tg_bot_template.bot_data import features
from tg_bot_template.bot_infra.callbacks import game_cb
from tg_bot_template.bot_infra.filters import (CreatorFilter,
                                               NonRegistrationFilter,
                                               RegistrationFilter)
from tg_bot_template.bot_infra.states import UserForm
from tg_bot_template.loader import bot, dp

# filters binding
dp.filters_factory.bind(CreatorFilter)
dp.filters_factory.bind(RegistrationFilter)
dp.filters_factory.bind(NonRegistrationFilter)


@dp.message_handler(lambda message: features.ping_ftr.find_triggers(message))
async def ping(msg: types.Message) -> None:
    await bot.ping(msg)


@dp.message_handler(lambda message: features.creator_ftr.find_triggers(message), creator=True)
async def creator_filter_check(msg: types.Message) -> None:
    await bot.creator_filter_check(msg)


@dp.message_handler(Text(equals=features.cancel_ftr.triggers, ignore_case=True), state="*")
async def cancel_command(msg: types.Message, state: FSMContext) -> None:
    await bot.cancel_command(msg, state)


@dp.callback_query_handler(Text(equals=features.cancel_ftr.triggers, ignore_case=True), state="*")
async def cancel_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await bot.cancel_callback(callback, state)


@dp.callback_query_handler(game_cb.filter(action=features.start_ftr.callback_action), registered=True)
@dp.message_handler(Text(equals=features.start_ftr.triggers, ignore_case=True), registered=True)
async def start(msg: types.Message | types.CallbackQuery) -> None:
    await bot.start(msg)


@dp.message_handler(Text(equals=features.help_ftr.triggers, ignore_case=True), registered=True)
async def help_feature(msg: types.Message) -> None:
    await bot.help_feature(msg)


# -------------------------------------------- PROFILE HANDLERS -------------------------------------------------------
@dp.message_handler(Text(equals=features.set_user_info.triggers, ignore_case=True), registered=True)
async def set_name(msg: types.Message) -> None:
    await bot.set_name(msg)


@dp.message_handler(content_types=["text", "caption"], state=UserForm.name)
async def add_form_name(msg: types.Message, state: FSMContext) -> None:
    await bot.fill_form(msg=msg, feature=features.set_user_name, form=UserForm, state=state)


@dp.message_handler(content_types=["text", "caption"], state=UserForm.info)
async def add_form_info(msg: types.Message, state: FSMContext) -> None:
    await bot.fill_form(msg=msg, feature=features.set_user_about, form=UserForm, state=state)


@dp.message_handler(content_types=["photo"], state=UserForm.photo)
async def add_form_photo(msg: types.Message, state: FSMContext) -> None:
    await bot.add_form_photo(msg, state)


@dp.message_handler(content_types=["any"], state=UserForm.name)
async def error_form_name(msg: types.Message) -> None:
    await bot.error_form(msg)


@dp.message_handler(content_types=["any"], state=UserForm.info)
async def error_form_info(msg: types.Message) -> None:
    await bot.error_form(msg)


@dp.message_handler(content_types=["any"], state=UserForm.photo)
async def error_form_photo(msg: types.Message) -> None:
    await bot.error_form_photo(msg)


# -------------------------------------------- GAME HANDLERS ----------------------------------------------------------
@dp.message_handler(Text(equals=features.rating_ftr.triggers, ignore_case=True), registered=True)
async def rating(msg: types.Message) -> None:
    await bot.rating(msg)


@dp.message_handler(Text(equals=features.press_button_ftr.triggers, ignore_case=True), registered=True)
async def send_press_button(msg: types.Message) -> None:
    await bot.send_press_button(msg)


@dp.callback_query_handler(game_cb.filter(action=features.press_button_ftr.callback_action), registered=True)
async def count_button_tap(callback: types.CallbackQuery, callback_data: dict[Any, Any]) -> None:
    await bot.count_button_tap(callback, callback_data)


# -------------------------------------------- SERVICE HANDLERS -------------------------------------------------------
@dp.message_handler(content_types=["any"], not_registered=True)
async def registration(msg: types.Message) -> types.Message | None:
    return await bot.registration(msg)


@dp.message_handler(content_types=["any"], registered=True)
async def handle_wrong_text_msg(msg: types.Message) -> None:
    await bot.handle_wrong_text_msg(msg)


@dp.my_chat_member_handler()
async def handle_my_chat_member_handlers(msg: types.Message):
    await bot.handle_my_chat_member_handlers(msg)


@dp.errors_handler(exception=BotBlocked)
async def exception_handler(update: types.Update, exception: BotBlocked):
    return await bot.exception_handler(update, exception)
