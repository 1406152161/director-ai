# @author zhangzhihao
"""Embedding 工厂单元测试。"""

from app.core.config import Settings
from app.providers.embedding.factory import create_embedding_function
from app.providers.embedding.local_hash import LocalHashEmbeddingFunction


def test_test_env_uses_local_hash():
    fn = create_embedding_function(Settings(app_env="test", novel_embedding_provider="auto"))
    assert isinstance(fn, LocalHashEmbeddingFunction)


def test_explicit_deepseek_without_key_falls_back():
    fn = create_embedding_function(
        Settings(app_env="development", novel_embedding_provider="deepseek", deepseek_api_key="")
    )
    assert isinstance(fn, LocalHashEmbeddingFunction)
