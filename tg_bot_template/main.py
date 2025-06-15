import asyncio

import aioschedule
from aiogram import Dispatcher, types
from aiogram.utils import executor
from loguru import logger

from tg_bot_template.bot_data import features
from tg_bot_template.bot_data.bot_models import Feature
from tg_bot_template.config import settings
from tg_bot_template.handlers.handlers import bot, dp


async def healthcheck() -> None:
    logger.info(features.ping_ftr.text2)
    if settings.creator_id is not None:
        await bot_safe_send_message(dp, int(settings.creator_id), features.ping_ftr.text2)  # type: ignore[arg-type]


# -------------------------------------------- BOT SETUP --------------------------------------------
async def bot_scheduler() -> None:
    logger.info("Scheduler is up")
    aioschedule.every().day.at(settings.schedule_healthcheck).do(healthcheck)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(dispatcher: Dispatcher) -> None:
    logger.info("Bot is up")
    await bot.safe_send_message(settings.creator_id, "Bot is up")

    # bot commands setup
    cmds = Feature.commands_to_set
    bot_commands = [types.BotCommand(ftr.slashed_command, ftr.slashed_command_descr) for ftr in cmds]
    await dispatcher.bot.set_my_commands(bot_commands)
    # scheduler startup
    asyncio.create_task(bot_scheduler())


async def on_shutdown(dispatcher: Dispatcher) -> None:
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)
