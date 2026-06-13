# @author zhangzhihao
"""Provider 注册表单元测试。"""

from app.core.config import Settings
from app.providers.image.agnes import AgnesImageProvider
from app.providers.image.mock import MockImageProvider
from app.providers.llm.agnes import AgnesLLMProvider
from app.providers.llm.deepseek import DeepSeekLLMProvider
from app.providers.llm.mock import MockLLMProvider
from app.providers.llm.zhipu import ZhipuLLMProvider
from app.providers.registry import get_image_provider, get_llm_provider, get_novel_llm_provider


def test_registry_selects_mock():
    settings = Settings(llm_provider="mock", image_provider="mock")
    assert isinstance(get_llm_provider(settings), MockLLMProvider)
    assert isinstance(get_image_provider(settings), MockImageProvider)


def test_registry_selects_agnes():
    settings = Settings(llm_provider="agnes", image_provider="agnes")
    assert isinstance(get_llm_provider(settings), AgnesLLMProvider)
    assert isinstance(get_image_provider(settings), AgnesImageProvider)


def test_novel_registry_selects_deepseek():
    settings = Settings(novel_llm_provider="deepseek")
    assert isinstance(get_novel_llm_provider(settings), DeepSeekLLMProvider)


def test_novel_registry_selects_zhipu():
    settings = Settings(novel_llm_provider="zhipu")
    assert isinstance(get_novel_llm_provider(settings), ZhipuLLMProvider)


def test_novel_registry_selects_mock():
    settings = Settings(novel_llm_provider="mock")
    assert isinstance(get_novel_llm_provider(settings), MockLLMProvider)
