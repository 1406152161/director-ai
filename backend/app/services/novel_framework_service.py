# @author zhangzhihao
"""框架记忆条目：DB SSOT + Chroma 索引 + hybrid 检索。"""

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.novel_framework_item import NovelFrameworkItem
from app.services.novel_memory_service import NovelMemoryService

logger = logging.getLogger(__name__)


class NovelFrameworkService:
    """同步 Bible → framework_items，并提供 hybrid 检索。"""

    def __init__(self, db: Session, memory_svc: NovelMemoryService | None = None) -> None:
        self._db = db
        self._memory = memory_svc or NovelMemoryService()

    def sync_from_bible(self, novel_id: str, bible: dict[str, Any]) -> None:
        self._db.query(NovelFrameworkItem).filter(NovelFrameworkItem.novel_id == novel_id).delete()
        items: list[NovelFrameworkItem] = []

        if bible.get("world"):
            items.append(self._mk(
                novel_id, "world", "world_global", "global", None, None, None,
                "世界观", bible["world"], bible["world"],
            ))
        if bible.get("power_system"):
            items.append(self._mk(
                novel_id, "rule", "power_system", "global", None, None, None,
                "体系", bible["power_system"], bible["power_system"],
            ))

        for char in bible.get("characters") or []:
            name = char.get("name") or ""
            if not name:
                continue
            text = f"{name} {char.get('role', '')} {char.get('traits') or char.get('profile', '')}"
            items.append(self._mk(
                novel_id, "character", f"char_{name}", "global", None, None, None,
                name, text, text,
            ))

        for prop in bible.get("items") or []:
            name = prop.get("name") or ""
            if not name:
                continue
            iid = prop.get("id") or f"item_{name}"
            text = (
                f"{name} {prop.get('description', '')} "
                f"意义：{prop.get('significance', '')}"
            )
            items.append(self._mk(
                novel_id, "item", iid, "global", None, None, None,
                name, text, text,
            ))

        for fs in bible.get("foreshadowing") or []:
            fid = fs.get("id") or "fs"
            text = (
                f"伏笔{fid} {fs.get('content', '')} "
                f"埋设{fs.get('plant_chapter')} 回收{fs.get('resolve_chapter')}"
            )
            items.append(self._mk(
                novel_id, "foreshadow", fid, "chapter",
                fs.get("resolve_chapter") or fs.get("plant_chapter"),
                fs.get("plant_chapter"), fs.get("resolve_chapter"),
                fid, fs.get("content", ""), text,
            ))

        for ol in bible.get("outline") or []:
            idx = ol.get("index")
            text = f"第{idx}章 {ol.get('title', '')} {ol.get('summary', '')} {ol.get('hook', '')}"
            items.append(self._mk(
                novel_id, "outline", f"ch_{idx}", "chapter", idx, idx, idx,
                ol.get("title", ""), ol.get("summary", ""), text,
            ))

        for item in items:
            self._db.add(item)
        self._db.commit()
        self._index_to_chroma(novel_id, items)

    @staticmethod
    def _mk(
        novel_id: str,
        item_type: str,
        item_key: str,
        scope: str,
        chapter_index: int | None,
        chapter_from: int | None,
        chapter_to: int | None,
        title: str,
        content: str,
        text_for_embed: str,
    ) -> NovelFrameworkItem:
        return NovelFrameworkItem(
            novel_id=novel_id,
            item_type=item_type,
            item_key=item_key,
            scope=scope,
            chapter_index=chapter_index,
            chapter_from=chapter_from,
            chapter_to=chapter_to,
            title=title,
            content=content,
            text_for_embed=text_for_embed,
            status="confirmed",
        )

    def _index_to_chroma(self, novel_id: str, items: list[NovelFrameworkItem]) -> None:
        if not items:
            return
        client = self._memory._ensure_client()
        name = f"novel_{novel_id}_framework"
        emb = self._memory.embedding_function()
        collection = client.get_or_create_collection(name=name, embedding_function=emb)
        ids, docs, metas = [], [], []
        for item in items:
            ids.append(item.item_key)
            docs.append(item.text_for_embed or item.content)
            metas.append({
                "item_type": item.item_type,
                "chapter_index": item.chapter_index or 0,
                "status": item.status,
            })
        collection.upsert(ids=ids, documents=docs, metadatas=metas)
        logger.info("Framework Chroma 索引 novel=%s count=%s", novel_id, len(ids))

    def query_hybrid(
        self,
        novel_id: str,
        query: str,
        chapter_index: int,
        top_k: int = 5,
    ) -> list[str]:
        """Mandatory 过滤 + 关键词 + 向量 top-k。"""
        results: list[str] = []
        seen: set[str] = set()

        mandatory = (
            self._db.query(NovelFrameworkItem)
            .filter(
                NovelFrameworkItem.novel_id == novel_id,
                NovelFrameworkItem.status == "confirmed",
                NovelFrameworkItem.item_type.in_(["foreshadow", "outline"]),
            )
            .all()
        )
        for item in mandatory:
            if item.item_type == "outline" and item.chapter_index == chapter_index:
                line = f"[大纲] 第{chapter_index}章：{item.content}"
                if line not in seen:
                    seen.add(line)
                    results.append(line)
            if item.item_type == "foreshadow":
                cf, ct = item.chapter_from or 0, item.chapter_to or 0
                if item.chapter_from == chapter_index or item.chapter_to == chapter_index:
                    line = f"[伏笔] {item.title}：{item.content}"
                    if line not in seen:
                        seen.add(line)
                        results.append(line)
                elif cf < chapter_index <= ct:
                    line = f"[伏笔进行中] {item.title}：{item.content}"
                    if line not in seen:
                        seen.add(line)
                        results.append(line)

        keywords = [w for w in query.replace("第", " ").split() if len(w) >= 2][:6]
        if keywords:
            like_items = (
                self._db.query(NovelFrameworkItem)
                .filter(NovelFrameworkItem.novel_id == novel_id)
                .all()
            )
            for item in like_items:
                text = item.text_for_embed or item.content
                if any(k in text for k in keywords):
                    line = f"[{item.item_type}] {text[:120]}"
                    if line not in seen:
                        seen.add(line)
                        results.append(line)

        client = self._memory._ensure_client()
        name = f"novel_{novel_id}_framework"
        emb = self._memory.embedding_function()
        try:
            collection = client.get_collection(name=name, embedding_function=emb)
            if collection.count() > 0:
                vr = collection.query(
                    query_texts=[query],
                    n_results=min(top_k, collection.count()),
                )
                for doc in (vr.get("documents") or [[]])[0]:
                    if doc and doc not in seen:
                        seen.add(doc)
                        results.append(doc)
        except Exception:
            pass

        return results[: top_k + 3]

    def replace_outline_and_foreshadowing(
        self, novel_id: str, bible: dict[str, Any], outline: list, foreshadowing: list
    ) -> dict[str, Any]:
        bible = dict(bible)
        bible["outline"] = outline
        bible["foreshadowing"] = foreshadowing
        self.sync_from_bible(novel_id, bible)
        return bible
