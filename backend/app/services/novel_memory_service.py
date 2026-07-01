# @author zhangzhihao
"""Chroma 向量记忆与 Story Bible 读写。"""

import json
import logging
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings
from app.providers.embedding.factory import create_embedding_function

logger = logging.getLogger(__name__)


def parse_bible(bible_json: str) -> dict[str, Any]:
    """解析 Story Bible JSON。"""
    if not bible_json or bible_json.strip() in ("", "{}"):
        return _empty_bible()
    data = json.loads(bible_json)
    return _normalize_bible(data)


def _empty_bible() -> dict[str, Any]:
    return {
        "meta": {},
        "world": "",
        "power_system": "",
        "items": [],
        "facts": [],
        "characters": [],
        "outline": [],
        "volumes": [],
        "foreshadowing": [],
        "beats": {},
    }


def _normalize_bible(data: dict[str, Any]) -> dict[str, Any]:
    base = _empty_bible()
    for key in base:
        if key in data:
            base[key] = data[key]
    if isinstance(data.get("meta"), dict):
        base["meta"] = {**base.get("meta", {}), **data["meta"]}
    return base


def merge_bible_updates(bible: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    """将改稿对话返回的 updates 合并进 Story Bible。"""
    merged = dict(bible)
    for key in ("world", "outline", "power_system", "volumes", "foreshadowing", "beats", "meta"):
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
    if bible.get("power_system"):
        parts.append(f"体系/规则：{bible['power_system']}")
    chars = bible.get("characters") or []
    if chars:
        char_lines = []
        for c in chars:
            line = f"- {c.get('name', '?')}（{c.get('role', '')}）：{c.get('traits') or c.get('profile', '')}"
            if c.get("growth_arc"):
                line += f"｜成长线：{c['growth_arc']}"
            char_lines.append(line)
        parts.append("人物：\n" + "\n".join(char_lines))
    facts = bible.get("facts") or []
    if facts:
        parts.append("已发生事实：\n" + "\n".join(f"- {f}" for f in facts[-8:]))
    return "\n\n".join(parts)


def foreshadowing_for_chapter(bible: dict[str, Any], chapter_index: int) -> list[dict[str, Any]]:
    """取出本章应埋设/回收/仍在进行的伏笔。"""
    result: list[dict[str, Any]] = []
    for fs in bible.get("foreshadowing") or []:
        plant = fs.get("plant_chapter") or 0
        resolve = fs.get("resolve_chapter") or 0
        status = fs.get("status", "planned")
        if plant == chapter_index or resolve == chapter_index:
            result.append(fs)
        elif status == "planted" and plant < chapter_index <= resolve:
            result.append(fs)
    return result


def beats_to_prompt(beats: list[dict[str, Any]]) -> str:
    """场景 beat 格式化为 prompt。"""
    if not beats:
        return "（暂无 beat，按大纲自由发挥）"
    lines = []
    for b in beats:
        lines.append(
            f"{b.get('index', '?')}. {b.get('scene', '')} "
            f"目标：{b.get('goal', '')} 冲突：{b.get('conflict', '')} 结果：{b.get('outcome', '')}"
        )
    return "\n".join(lines)


def foreshadowing_to_prompt(items: list[dict[str, Any]], chapter_index: int) -> str:
    """伏笔要求格式化为 prompt。"""
    if not items:
        return "（本章无特殊伏笔任务）"
    lines = []
    for fs in items:
        plant = fs.get("plant_chapter")
        resolve = fs.get("resolve_chapter")
        action = []
        if plant == chapter_index:
            action.append("须埋设")
        if resolve == chapter_index:
            action.append("须回收")
        prefix = "、".join(action) if action else "保持呼应"
        lines.append(
            f"- [{fs.get('id', '?')}] {prefix}：{fs.get('content', '')} "
            f"(埋设第{plant}章→回收第{resolve}章)"
        )
    return "\n".join(lines)


def update_foreshadowing_after_chapter(bible: dict[str, Any], chapter_index: int) -> dict[str, Any]:
    """根据写完的章号更新伏笔状态。"""
    updated = []
    for fs in bible.get("foreshadowing") or []:
        item = dict(fs)
        plant = item.get("plant_chapter")
        resolve = item.get("resolve_chapter")
        status = item.get("status", "planned")
        if plant == chapter_index and status == "planned":
            item["status"] = "planted"
        if resolve == chapter_index:
            item["status"] = "resolved"
        updated.append(item)
    bible["foreshadowing"] = updated
    return bible


def get_beats_for_chapter(bible: dict[str, Any], chapter_index: int) -> list[dict[str, Any]]:
    """读取已缓存的章 beat。"""
    beats_map = bible.get("beats") or {}
    return beats_map.get(str(chapter_index)) or beats_map.get(chapter_index) or []


def save_beats_for_chapter(bible: dict[str, Any], chapter_index: int, beats: list[dict[str, Any]]) -> dict[str, Any]:
    """缓存章 beat 到 bible。"""
    beats_map = dict(bible.get("beats") or {})
    beats_map[str(chapter_index)] = beats
    bible["beats"] = beats_map
    return bible


def get_initial_write_count(bible: dict[str, Any], default: int = 3) -> int:
    meta = bible.get("meta") or {}
    count = meta.get("initial_write_count", default)
    return max(1, min(10, int(count)))


def get_plan_mode(bible: dict[str, Any]) -> str:
    return (bible.get("meta") or {}).get("plan_mode", "auto")


class NovelMemoryService:
    """章节摘要向量存储与检索。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = None
        self._embedding_fn = create_embedding_function(self._settings)

    def embedding_function(self):
        return self._embedding_fn

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

    def drop_collection(self, novel_id: str) -> None:
        """删除小说向量集合（幂等）。"""
        client = self._ensure_client()
        name = self._collection_name(novel_id)
        try:
            client.delete_collection(name)
        except Exception:
            logger.debug("Chroma 集合不存在或已删除: %s", name)

    def append_fact_to_bible(self, bible: dict[str, Any], fact: str) -> dict[str, Any]:
        """追加关键事实到 Story Bible。"""
        facts = list(bible.get("facts", []))
        if fact and fact not in facts:
            facts.append(fact)
        bible["facts"] = facts
        return bible
