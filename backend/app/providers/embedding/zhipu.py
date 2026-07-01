# @author zhangzhihao
"""智谱 OpenAI 兼容 Embeddings API（中文语义检索备选）。"""

import httpx
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings


class ZhipuEmbeddingFunction(EmbeddingFunction[Documents]):
    """调用智谱 embedding-2。"""

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://open.bigmodel.cn/api/paas/v4",
        model: str = "embedding-2",
        timeout: float = 60.0,
    ) -> None:
        self._api_key = api_key
        self._api_base = api_base.rstrip("/")
        self._model = model
        self._timeout = timeout

    def name(self) -> str:
        return "zhipu"

    def __call__(self, input: Documents) -> Embeddings:
        if not input:
            return []
        url = f"{self._api_base}/embeddings"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self._model, "input": list(input)}
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url, json=payload, headers=headers)
        if response.status_code >= 400:
            raise RuntimeError(
                f"智谱 Embedding 失败 ({response.status_code}): {response.text[:300]}"
            )
        data = response.json()
        items = sorted(data.get("data") or [], key=lambda x: x.get("index", 0))
        return [item["embedding"] for item in items]
