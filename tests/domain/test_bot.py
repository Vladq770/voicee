from unittest.mock import AsyncMock

import pytest
from aiogram.types import CallbackQuery

from tg_bot_template.bot_data import features
from tg_bot_template.domain.bot import Bot


class TestBot:
    @pytest.fixture
    def bot(self):
        return Bot(tg_connection=AsyncMock(), repository=AsyncMock())

    @pytest.fixture
    def mock_message(self):
        return AsyncMock()

    @pytest.fixture
    def mock_state(self):
        return AsyncMock()

    @pytest.fixture
    def mock_callback(self):
        return AsyncMock(spec=CallbackQuery)

    @pytest.fixture
    def mock_logger(self, mocker):
        return mocker.patch("tg_bot_template.domain.bot.logger")

    async def test_safe_delete_message(self, bot):
        await bot.safe_delete_message(123, 321)
        bot.tg_connection.delete_message.assert_called_once_with(123, 321)

    async def test_safe_delete_message_with_exception(self, bot, mock_logger):
        bot.tg_connection.delete_message.side_effect = Exception
        await bot.safe_delete_message(123, 321)
        bot.tg_connection.delete_message.assert_called_once_with(123, 321)
        mock_logger.warning.assert_called_once_with(f"Delete message 321 from chat 123 failed.")

    async def test_start(self, bot, mock_callback):
        await bot.start(mock_callback)
        mock_callback.answer.assert_called_once()
        bot.tg_connection.send_message.assert_called_once()

    async def test_help_feature(self, bot, mock_message):
        await bot.help_feature(mock_message)
        mock_message.answer.assert_called_once_with(features.help_ftr.text, reply_markup=features.empty.kb)

    async def test_cancel_command(self, bot, mock_message, mock_state):
        await bot.cancel_command(mock_message, mock_state)
        bot.tg_connection.send_message.assert_called_once()
        mock_message.answer.assert_called_once_with(features.cancel_ftr.text)
        mock_state.finish.assert_called_once()
