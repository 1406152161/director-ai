# @author zhangzhihao
"""Embedding 工厂：DeepSeek / 智谱 / LocalHash，带运行时降级。"""

import logging

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from app.core.config import Settings, get_settings
from app.providers.embedding.deepseek import DeepSeekEmbeddingFunction
from app.providers.embedding.local_hash import LocalHashEmbeddingFunction
from app.providers.embedding.zhipu import ZhipuEmbeddingFunction

logger = logging.getLogger(__name__)


class _FallbackEmbeddingFunction(EmbeddingFunction[Documents]):
    """主 Provider 失败时自动降级为 LocalHash。"""

    def __init__(self, primary: EmbeddingFunction[Documents], fallback_name: str = "local_hash") -> None:
        self._primary = primary
        self._fallback = LocalHashEmbeddingFunction()
        self._fallback_name = fallback_name
        self._use_fallback = False

    def name(self) -> str:
        if self._use_fallback:
            return self._fallback.name()
        return self._primary.name()

    def __call__(self, input: Documents) -> Embeddings:
        if self._use_fallback:
            return self._fallback(input)
        try:
            return self._primary(input)
        except Exception as exc:
            logger.warning(
                "Embedding Provider %s 失败，降级为 local_hash: %s",
                self._primary.name(),
                exc,
            )
            self._use_fallback = True
            return self._fallback(input)


def create_embedding_function(settings: Settings | None = None) -> EmbeddingFunction[Documents]:
    """按配置创建 Embedding；测试环境固定 local_hash。

    注意：DeepSeek 官方 API 仅提供 Chat，无 Embedding 端点（会 404）。
    auto 模式优先使用智谱 embedding-2。
    """
    cfg = settings or get_settings()
    local = LocalHashEmbeddingFunction()

    if cfg.app_env == "test" or cfg.novel_embedding_provider == "local_hash":
        return local

    provider = cfg.novel_embedding_provider
    if provider == "auto":
        if cfg.zhipu_api_key:
            provider = "zhipu"
        else:
            logger.info(
                "未配置 ZHIPU_API_KEY，向量记忆使用 local_hash（DeepSeek 无 Embedding API）"
            )
            return local

    if provider == "deepseek":
        logger.warning(
            "DeepSeek 官方未提供 Embedding API（/v1/embeddings 会 404），"
            "建议 NOVEL_EMBEDDING_PROVIDER=zhipu"
        )
        if not cfg.deepseek_api_key:
            logger.warning("未配置 DEEPSEEK_API_KEY，Embedding 使用 local_hash")
            return local
        primary = DeepSeekEmbeddingFunction(
            api_key=cfg.deepseek_api_key,
            api_base=cfg.deepseek_api_base,
            model=cfg.deepseek_embedding_model,
        )
        return _FallbackEmbeddingFunction(primary)

    if provider == "zhipu":
        if not cfg.zhipu_api_key:
            logger.warning("未配置 ZHIPU_API_KEY，Embedding 使用 local_hash")
            return local
        primary = ZhipuEmbeddingFunction(
            api_key=cfg.zhipu_api_key,
            api_base=cfg.zhipu_api_base,
            model=cfg.zhipu_embedding_model,
        )
        return _FallbackEmbeddingFunction(primary)

    return local
