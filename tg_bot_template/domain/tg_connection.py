from abc import ABC, abstractmethod


class TGConnection(ABC):
    @abstractmethod
    async def send_message(self, chat_id: int | None, text: str, **kwargs) -> None:  # type: ignore[no-untyped-def]
        pass

    @abstractmethod
    async def delete_message(self, chat_id: int, message_id: int) -> None:  # type: ignore[no-untyped-def]
        pass

    @abstractmethod
    async def send_photo(self, chat_id: int, photo, **kwargs) -> None:  # type: ignore[no-untyped-def]
        pass

    @abstractmethod
    async def edit_message_text(  # type: ignore[no-untyped-def]
        self, text: str | None, chat_id: int, message_id: int, **kwargs
    ) -> None:
        pass
