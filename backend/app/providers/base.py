# @author zhangzhihao
"""Provider 统一接口定义（Protocol）。"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class Message:
    role: str
    content: str


@dataclass
class ImageResult:
    url: str
    prompt: str


@dataclass
class VideoResult:
    url: str
    duration: int


@dataclass
class TTSResult:
    audio_url: str
    duration: float


@runtime_checkable
class LLMProvider(Protocol):
    async def chat(self, messages: list[Message], **kwargs: object) -> str: ...


@runtime_checkable
class ImageProvider(Protocol):
    async def text_to_image(self, prompt: str, **kwargs: object) -> ImageResult: ...

    async def image_to_image(
        self, prompt: str, reference_urls: list[str], **kwargs: object
    ) -> ImageResult: ...


@runtime_checkable
class VideoProvider(Protocol):
    async def image_to_video(
        self, image_url: str, prompt: str, duration: int, **kwargs: object
    ) -> VideoResult: ...


@runtime_checkable
class TTSProvider(Protocol):
    async def synthesize(self, text: str, **kwargs: object) -> TTSResult: ...
