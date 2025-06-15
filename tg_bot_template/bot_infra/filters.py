from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from tg_bot_template.bot_data.bot_models import TgUser
from tg_bot_template.config import settings
from tg_bot_template.loader import repository


class AbsFilter(BoundFilter):  # type: ignore[misc]
    key = "key"

    def __init__(self, **kwargs):  # type: ignore[no-untyped-def]
        setattr(self, self.key, kwargs[self.key])

    async def check(self, msg: types.Message) -> bool:
        return True


class CreatorFilter(AbsFilter):
    key = "creator"

    async def check(self, msg: types.Message) -> bool:
        return settings.creator_id is None or msg.from_user.id == settings.creator_id


class RegistrationFilter(AbsFilter):
    key = "registered"

    async def check(self, msg: types.Message) -> bool:
        return await repository.check_user_registered(
            tg_user=TgUser(tg_id=msg.from_user.id, username=msg.from_user.username)
        )


class NonRegistrationFilter(AbsFilter):
    key = "not_registered"

    async def check(self, msg: types.Message) -> bool:
        return not await repository.check_user_registered(
            tg_user=TgUser(tg_id=msg.from_user.id, username=msg.from_user.username)
        )
