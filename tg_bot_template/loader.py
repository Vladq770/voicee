from aiogram import Bot as TGConn
from aiogram import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from tg_bot_template.config import settings
from tg_bot_template.domain.bot import Bot
from tg_bot_template.domain.peewee_repo import PeeweeRepository

storage = (
    MemoryStorage()
    if settings.environment.local_test
    else RedisStorage2(settings.fsm_redis_host, db=settings.fsm_redis_db, password=settings.fsm_redis_pass)
)
repository = PeeweeRepository()
tg_connection = TGConn(token=settings.tg_bot_token)
bot = Bot(repository=repository, tg_connection=tg_connection)
dp = Dispatcher(tg_connection, storage=storage)  # type: ignore[no-untyped-call]
