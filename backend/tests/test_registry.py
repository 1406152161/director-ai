# @author zhangzhihao
"""Provider 注册表单元测试。"""

from app.core.config import Settings
from app.providers.image.agnes import AgnesImageProvider
from app.providers.image.mock import MockImageProvider
from app.providers.llm.agnes import AgnesLLMProvider
from app.providers.llm.mock import MockLLMProvider
from app.providers.registry import get_image_provider, get_llm_provider


def test_registry_selects_mock():
    settings = Settings(llm_provider="mock", image_provider="mock")
    assert isinstance(get_llm_provider(settings), MockLLMProvider)
    assert isinstance(get_image_provider(settings), MockImageProvider)


def test_registry_selects_agnes():
    settings = Settings(llm_provider="agnes", image_provider="agnes")
    assert isinstance(get_llm_provider(settings), AgnesLLMProvider)
    assert isinstance(get_image_provider(settings), AgnesImageProvider)
