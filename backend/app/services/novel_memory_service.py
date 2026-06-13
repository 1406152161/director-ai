# @author zhangzhihao
"""Chroma 向量记忆与 Story Bible 读写。"""

import hashlib
import json
import logging
import struct
from pathlib import Path
from typing import Any

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class LocalHashEmbeddingFunction(EmbeddingFunction[Documents]):
    """无网络依赖的轻量 embedding，避免 CI 下载 ONNX 模型。"""

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


def parse_bible(bible_json: str) -> dict[str, Any]:
    """解析 Story Bible JSON。"""
    if not bible_json or bible_json.strip() in ("", "{}"):
        return {"world": "", "facts": [], "characters": [], "outline": []}
    return json.loads(bible_json)


def merge_bible_updates(bible: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    """将改稿对话返回的 updates 合并进 Story Bible。"""
    merged = dict(bible)
    for key in ("world", "outline"):
        if key in updates and updates[key]:
            merged[key] = updates[key]

    if "characters" in updates and updates["characters"]:
        existing = {c.get("name"): c for c in merged.get("characters", [])}
        for char in updates["characters"]:
            name = char.get("name")
            if name and name in existing:
                existing[name].update(char)
            elif name:
                existing[name] = char
        merged["characters"] = list(existing.values())

    if "facts" in updates and updates["facts"]:
        facts = list(merged.get("facts", []))
        for fact in updates["facts"]:
            if fact and fact not in facts:
                facts.append(fact)
        merged["facts"] = facts

    return merged


def bible_to_prompt_summary(bible: dict[str, Any]) -> str:
    """将 Story Bible 压缩为 prompt 上下文。"""
    parts = []
    if bible.get("world"):
        parts.append(f"世界观：{bible['world']}")
    chars = bible.get("characters") or []
    if chars:
        char_lines = [
            f"- {c.get('name', '?')}（{c.get('role', '')}）：{c.get('traits') or c.get('profile', '')}"
            for c in chars
        ]
        parts.append("人物：\n" + "\n".join(char_lines))
    facts = bible.get("facts") or []
    if facts:
        parts.append("已发生事实：\n" + "\n".join(f"- {f}" for f in facts[-8:]))
    return "\n\n".join(parts)


class NovelMemoryService:
    """章节摘要向量存储与检索。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = None
        self._embedding_fn = LocalHashEmbeddingFunction()

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        import chromadb  # noqa: PLC0415

        persist_dir = Path(self._settings.chroma_persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(persist_dir))
        return self._client

    def _collection_name(self, novel_id: str) -> str:
        return f"novel_{novel_id}"

    def _get_collection(self, novel_id: str):
        client = self._ensure_client()
        return client.get_or_create_collection(
            name=self._collection_name(novel_id),
            embedding_function=self._embedding_fn,
        )

    def add_chapter_summary(
        self, novel_id: str, chapter_index: int, title: str, summary: str
    ) -> None:
        """写入章节摘要到 Chroma。"""
        if not summary.strip():
            return
        collection = self._get_collection(novel_id)
        doc_id = f"ch_{chapter_index}"
        collection.upsert(
            ids=[doc_id],
            documents=[summary],
            metadatas=[{"chapter_index": chapter_index, "title": title}],
        )
        logger.info("Chroma 写入 novel=%s chapter=%s", novel_id, chapter_index)

    def query_relevant(self, novel_id: str, query: str, top_k: int = 5) -> list[str]:
        """检索与 query 相关的章节摘要片段。"""
        client = self._ensure_client()
        name = self._collection_name(novel_id)
        try:
            collection = client.get_collection(
                name=name,
                embedding_function=self._embedding_fn,
            )
        except Exception:
            return []

        if collection.count() == 0:
            return []

        result = collection.query(query_texts=[query], n_results=min(top_k, collection.count()))
        docs = result.get("documents") or [[]]
        return [d for d in docs[0] if d]

    def append_fact_to_bible(self, bible: dict[str, Any], fact: str) -> dict[str, Any]:
        """追加关键事实到 Story Bible。"""
        facts = list(bible.get("facts", []))
        if fact and fact not in facts:
            facts.append(fact)
        bible["facts"] = facts
        return bible
