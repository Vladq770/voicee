from abc import ABC, abstractmethod

from tg_bot_template.bot_data.bot_models import TgUser, UserFormData
from tg_bot_template.domain.bd_models import Users
from tg_bot_template.unit_of_work.unit_of_work import UnitOfWork


class Repository(UnitOfWork, ABC):
    @abstractmethod
    async def get_user(self, tg_user: TgUser) -> Users | None:
        pass

    @abstractmethod
    async def create_user(self, tg_user: TgUser) -> None:
        pass

    @abstractmethod
    async def update_user_info(self, tg_user: TgUser, user_form_data: UserFormData) -> None:
        pass

    @abstractmethod
    async def incr_user_taps(self, tg_user: TgUser) -> None:
        pass

    @abstractmethod
    async def get_all_users(self) -> list[Users]:
        pass

    @abstractmethod
    async def check_user_registered(self, tg_user: TgUser) -> bool:
        pass
