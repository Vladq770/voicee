import inspect
from datetime import datetime

import peewee
import peewee_async
import playhouse.migrate
from loguru import logger

from tg_bot_template.bot_data.bot_models import TgUser, UserFormData
from tg_bot_template.config import BotSettings, settings
from tg_bot_template.domain import bd_models
from tg_bot_template.domain.bd_models import Users
from tg_bot_template.domain.repository import Repository

ALL_TABLES = [data for _, data in inspect.getmembers(bd_models) if isinstance(data, peewee.ModelBase)]


def _dev_drop_tables(database: peewee_async.PooledPostgresqlDatabase, tables: list[peewee.ModelBase]) -> None:
    with database:
        database.drop_tables(tables, safe=True)
    logger.info("Tables dropped")


def _create_tables(database: peewee_async.PooledPostgresqlDatabase, tables: list[peewee.ModelBase]) -> None:
    with database:
        database.create_tables(tables, safe=True)
    logger.info("Tables created")


def _make_migrations(database: peewee_async.PooledPostgresqlDatabase) -> None:
    migrator = playhouse.migrate.PostgresqlMigrator(database)  # noqa: F841
    try:
        with database.atomic():
            playhouse.migrate.migrate(
                # migrator.add_column("users", "social_id", peewee.BigIntegerField(null=True)),  # noqa: ERA001
                # migrator.drop_not_null("users", "name"),  # noqa: ERA001
                # migrator.alter_column_type("users", "social_id", peewee.BigIntegerField(null=False)),  # noqa: ERA001
            )
        logger.info("Tables migrated")
    except peewee.ProgrammingError as e:
        logger.exception(f"Tables migrating error: {str(e)}")


def setup_db(settings: BotSettings) -> peewee_async.Manager:
    # psql postgresql://tg_bot_user:tg_bot_user@localhost:5432/tg_bot_user
    # ---------------- DB INIT ----------------
    database = peewee_async.PooledPostgresqlDatabase(
        settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
    )
    database.bind(ALL_TABLES)

    # ---------------- MIGRATIONS ----------------
    # _dev_drop_tables(database, ALL_TABLES)  # noqa: ERA001
    _create_tables(database, ALL_TABLES)
    _make_migrations(database)

    database.close()
    database.set_allow_sync(False)
    return peewee_async.Manager(database)


class PeeweeRepository(Repository):
    def __init__(self):
        self.connection = setup_db(settings)

    async def commit(self):
        # В Peewee нет методов commit и rollback.
        # При переходе на алхимию нужно раскомментить следующую строку
        # и вызывать методы БД через контекстный менеджер.
        # self.connection.commit()
        pass

    async def rollback(self):
        # self.connection.rollback()
        pass

    async def get_user(self, tg_user: TgUser) -> Users | None:
        try:
            user = await self.connection.get(Users, social_id=tg_user.tg_id)
        except Exception:
            return None
        else:
            user.username = tg_user.username
            await self.connection.update(user)
            return user  # type: ignore[no-any-return]

    async def create_user(self, tg_user: TgUser) -> None:
        await self.connection.create(
            Users, social_id=tg_user.tg_id, username=tg_user.username, registration_date=datetime.now()  # noqa: DTZ005
        )
        logger.info(f"New user[{tg_user.username}] registered")

    async def update_user_info(self, tg_user: TgUser, user_form_data: UserFormData) -> None:
        user = await self.get_user(tg_user=tg_user)
        if user is not None:
            user.name = user_form_data.name
            user.info = user_form_data.info
            user.photo = user_form_data.photo
            await self.connection.update(user)

    async def incr_user_taps(self, tg_user: TgUser) -> None:
        user = await self.get_user(tg_user=tg_user)
        if user is not None:
            user.taps += 1
            await self.connection.update(user)

    async def get_all_users(self) -> list[Users]:
        return list(await self.connection.execute(Users.select().order_by(Users.taps.desc())))

    async def check_user_registered(self, tg_user: TgUser) -> bool:
        return bool(await self.get_user(tg_user=tg_user))
