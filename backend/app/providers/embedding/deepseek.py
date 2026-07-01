# @author zhangzhihao
"""DeepSeek OpenAI 兼容 Embeddings API。"""

import logging

import httpx
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

logger = logging.getLogger(__name__)


class DeepSeekEmbeddingFunction(EmbeddingFunction[Documents]):
    """调用 POST /v1/embeddings。"""

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.deepseek.com",
        model: str = "deepseek-embedding",
        timeout: float = 60.0,
    ) -> None:
        self._api_key = api_key
        self._api_base = api_base.rstrip("/")
        self._model = model
        self._timeout = timeout

    def name(self) -> str:
        return "deepseek"

    def __call__(self, input: Documents) -> Embeddings:
        if not input:
            return []
        url = f"{self._api_base}/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self._model, "input": list(input)}
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url, json=payload, headers=headers)
        if response.status_code >= 400:
            raise RuntimeError(
                f"DeepSeek Embedding 失败 ({response.status_code}): {response.text[:300]}"
            )
        data = response.json()
        items = sorted(data.get("data") or [], key=lambda x: x.get("index", 0))
        vectors = [item["embedding"] for item in items]
        if len(vectors) != len(input):
            raise RuntimeError("DeepSeek Embedding 返回数量与输入不一致")
        return vectors
