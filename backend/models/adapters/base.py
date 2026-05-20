from abc import ABC, abstractmethod
from typing import AsyncGenerator


class BaseAdapter(ABC):

    @abstractmethod
    async def chat_stream(
        self, messages: list[dict], **kwargs
    ) -> AsyncGenerator[str, None]:
        yield ""
