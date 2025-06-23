import asyncio
from typing import Any

from aiogram import Bot as AiogramTGConn
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup
from aiogram.utils.exceptions import BotBlocked
from loguru import logger

from tg_bot_template.bot_data import features
from tg_bot_template.bot_data.bot_models import InlineButton, TgUser, UserFormData
from tg_bot_template.bot_data.errors import Errors
from tg_bot_template.bot_data.features import Feature
from tg_bot_template.bot_infra.callbacks import game_cb
from tg_bot_template.bot_infra.states import UserForm
from tg_bot_template.config import settings
from tg_bot_template.domain.repository import Repository
from tg_bot_template.domain.tg_connection import TGConnection

"""
Сделать идеальный бизнес слой, который не зависит от либы/фреймворка (в данном случае от aiogram) не получилось.
В текущей реализации можно добавить слой, который будет преобразовывать объект types.Message, например в pydantic модель.
После этого заменить все msg.answer() на self.tg_connection.send_massage, таким образом снизить зависимость от aiogram.
Как я понимаю, с сообщениями можно сделать реализацию в общем виде(чтобы работало и для вебхуков),
но не уверен, что работу с состояниями (state: FSMContext) получится так просто привести к общему виду.
"""
# TODO: Добавить докстринги, тесты, линтеры, ci/cd.


class Bot:
    def __init__(self, repository: Repository, tg_connection: TGConnection | AiogramTGConn):
        self.repository = repository
        self.tg_connection = tg_connection

    async def safe_send_message(  # type: ignore[no-untyped-def]
        self, social_id: int | None, text: str, **kwargs
    ) -> None:
        try:
            text_arr = Feature.tg_msg_text_split(text)
            for mes in text_arr:
                await self.tg_connection.send_message(social_id, mes, **kwargs)
        except Exception:
            logger.warning(f"User with {social_id = } did not receive the message.")

    async def safe_delete_message(self, chat_id: int, message_id: int) -> None:
        try:
            await self.tg_connection.delete_message(chat_id, message_id)
        except Exception:
            logger.warning(f"Delete message {message_id} from chat {chat_id} failed.")

    async def safe_send_photo(self, social_id: int, photo, **kwargs) -> None:  # type: ignore[no-untyped-def]
        try:
            await self.tg_connection.send_photo(social_id, photo, **kwargs)
        except Exception as e:
            logger.warning(f"User with {social_id = } did not receive the photo.\nError: {e}")

    async def edit_callback_message(  # type: ignore[no-untyped-def]
        self, callback: types.CallbackQuery, text: str | None, **kwargs
    ):
        try:
            await self.tg_connection.edit_message_text(
                text, callback.from_user.id, callback.message.message_id, **kwargs
            )
        except Exception as e:
            logger.warning(f"Cant edit callback message for {callback = }.\nError: {e}")

    async def start(self, msg: types.Message | types.CallbackQuery) -> None:
        await self.main_menu(from_user_id=msg.from_user.id)
        if isinstance(msg, types.CallbackQuery):
            await msg.answer()

    async def main_menu(self, from_user_id: int) -> None:
        text = f"{features.start_ftr.text}\n\n{features.start_ftr.menu.text}"  # type: ignore[union-attr]
        await self.safe_send_message(from_user_id, text, reply_markup=features.start_ftr.kb)

    async def ping(self, msg: types.Message) -> None:
        await self.safe_send_message(msg.from_user.id, features.ping_ftr.text)  # type: ignore[arg-type]

    async def creator_filter_check(self, msg: types.Message) -> None:
        await msg.answer(features.creator_ftr.text, parse_mode=types.ParseMode.MARKDOWN)

    async def cancel_command(self, msg: types.Message, state: FSMContext) -> None:
        await msg.answer(features.cancel_ftr.text)
        if await state.get_state() is not None:
            await state.finish()
        await self.main_menu(msg.from_user.id)

    async def cancel_callback(self, callback: types.CallbackQuery, state: FSMContext) -> None:
        await self.edit_callback_message(callback, features.cancel_ftr.text)
        if await state.get_state() is not None:
            await state.finish()
        await self.main_menu(callback.from_user.id)

    async def help_feature(self, msg: types.Message) -> None:
        await msg.answer(features.help_ftr.text, reply_markup=features.empty.kb)

    async def set_name(self, msg: types.Message) -> None:
        await msg.answer(features.set_user_info.text, reply_markup=features.cancel_ftr.kb)
        await UserForm.name.set()

    async def fill_form(self, msg: types.Message, feature: Feature, form: StatesGroup, state: FSMContext) -> None:
        async with state.proxy() as data:
            data[feature.data_key] = msg.caption or msg.text
        await form.next()
        await msg.answer(feature.text, reply_markup=features.cancel_ftr.kb)

    async def add_form_photo(self, msg: types.Message, state: FSMContext) -> None:
        async with state.proxy() as data:
            user_form_data = UserFormData(
                name=data[features.set_user_name.data_key],
                info=data[features.set_user_about.data_key],
                photo=msg.photo[-1].file_id,
            )
            tg_user = TgUser(tg_id=msg.from_user.id, username=msg.from_user.username)
            await self.repository.update_user_info(tg_user=tg_user, user_form_data=user_form_data)
        await state.finish()
        await msg.answer(features.set_user_info.text2, reply_markup=features.set_user_info.kb)

    async def error_form(self, msg: types.Message) -> None:
        await msg.answer(Errors.text_form, reply_markup=features.cancel_ftr.kb)

    async def error_form_photo(self, msg: types.Message) -> None:
        await msg.answer(Errors.photo_form, reply_markup=features.cancel_ftr.kb)

    async def rating(self, msg: types.Message) -> None:
        user = await self.repository.get_user(tg_user=TgUser(tg_id=msg.from_user.id, username=msg.from_user.username))
        all_users = await self.repository.get_all_users()
        total_taps = sum([i.taps for i in all_users])
        text = features.rating_ftr.text.format(user_taps=user.taps, total_taps=total_taps)  # type: ignore[union-attr]
        await msg.answer(text, reply_markup=features.rating_ftr.kb)
        if all_users and (best_user := all_users[0]).taps > 0:
            text = features.rating_ftr.text2.format(  # type: ignore[union-attr]
                name=best_user.name, username=best_user.username, info=best_user.info
            )
            await msg.answer(text, reply_markup=features.rating_ftr.kb)
            await self.safe_send_photo(msg.from_user.id, best_user.photo, reply_markup=features.rating_ftr.kb)

    async def send_press_button(self, msg: types.Message) -> None:
        text, keyboard = await self.update_button_tap(taps=0)
        await msg.answer(text, reply_markup=Feature.create_tg_inline_kb(keyboard))

    @staticmethod
    async def update_button_tap(taps: int) -> tuple[str, list[list[InlineButton]]]:
        text = features.press_button_ftr.text.format(last_session=taps)  # type: ignore[union-attr]
        keyboard = [
            [
                InlineButton(
                    text=features.press_button_ftr.button,
                    callback_data=game_cb.new(action=features.press_button_ftr.callback_action, taps=taps),
                )
            ],
            [
                InlineButton(
                    text=features.start_ftr.button,
                    callback_data=game_cb.new(action=features.start_ftr.callback_action, taps=taps),
                )
            ],
        ]
        return text, keyboard

    async def count_button_tap(self, callback: types.CallbackQuery, callback_data: dict[Any, Any]) -> None:
        current_taps = int(callback_data["taps"])
        new_taps = current_taps + 1
        await self.repository.incr_user_taps(
            tg_user=TgUser(tg_id=callback.from_user.id, username=callback.from_user.username)
        )
        text, keyboard = await self.update_button_tap(taps=new_taps)
        await self.edit_callback_message(callback, text, reply_markup=Feature.create_tg_inline_kb(keyboard))

    async def registration(self, msg: types.Message) -> types.Message | None:
        if settings.register_passphrase is not None:
            if msg.text.lower() != settings.register_passphrase:
                return await msg.answer(Errors.please_register, reply_markup=features.empty.kb)
            if not msg.from_user.username:
                return await msg.answer(Errors.register_failed, reply_markup=features.empty.kb)
        # user registration
        await self.repository.create_user(tg_user=TgUser(tg_id=msg.from_user.id, username=msg.from_user.username))
        await msg.answer(features.register_ftr.text)
        await self.main_menu(from_user_id=msg.from_user.id)

    async def handle_wrong_text_msg(self, msg: types.Message) -> None:
        await asyncio.sleep(2)
        await msg.reply(Errors.text)

    @staticmethod
    async def handle_my_chat_member_handlers(msg: types.Message):
        logger.info(msg)

    @staticmethod
    async def exception_handler(update: types.Update, exception: BotBlocked):
        # работает только для хендлеров бота, для шедулера не работает
        logger.info(update.message.from_user.id)  # уведомление о блокировке
        logger.info(exception)  # уведомление о блокировке
        return True
