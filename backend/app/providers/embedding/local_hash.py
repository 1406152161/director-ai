# @author zhangzhihao
"""无网络依赖的轻量 embedding（测试 / 降级）。"""

import hashlib
import struct

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings


class LocalHashEmbeddingFunction(EmbeddingFunction[Documents]):
    """SHA256 伪向量，CI 与离线降级用。"""

    def __init__(self, dim: int = 384) -> None:
        self._dim = dim

    def name(self) -> str:
        return "local_hash"

    def __call__(self, input: Documents) -> Embeddings:
        embeddings: Embeddings = []
        for text in input:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            floats: list[float] = []
            while len(floats) < self._dim:
                for i in range(0, len(digest) - 3, 4):
                    chunk = digest[i : i + 4]
                    val = struct.unpack("!I", chunk)[0] / 4294967295.0
                    floats.append(val)
                digest = hashlib.sha256(digest).digest()
            embeddings.append(floats[: self._dim])
        return embeddings
