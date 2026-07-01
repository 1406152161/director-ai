# @author zhangzhihao
"""小说实体注册表服务。"""

import json
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.novel_entity import NovelEntity


def _slug(name: str) -> str:
    s = re.sub(r"\s+", "_", name.strip())[:48]
    return s or "unknown"


class NovelEntityService:
    """人物/道具/地点实体 CRUD 与 prompt 格式化。"""

    def __init__(self, db: Session) -> None:
        self._db = db

    def seed_from_bible(self, novel_id: str, bible: dict[str, Any]) -> None:
        """从规划 Bible 初始化 confirmed 人物实体。"""
        self._db.query(NovelEntity).filter(NovelEntity.novel_id == novel_id).delete()
        for char in bible.get("characters") or []:
            name = char.get("name") or ""
            if not name:
                continue
            key = f"char_{_slug(name)}"
            data = {
                "role": char.get("role", ""),
                "profile": char.get("traits") or char.get("profile", ""),
                "growth_arc": char.get("growth_arc", ""),
                "location": "",
                "knows": "",
            }
            self._db.add(
                NovelEntity(
                    novel_id=novel_id,
                    entity_type="character",
                    entity_key=key,
                    name=name,
                    data_json=json.dumps(data, ensure_ascii=False),
                    status="confirmed",
                    last_chapter_index=0,
                )
            )
        for prop in bible.get("items") or []:
            name = prop.get("name") or ""
            if not name:
                continue
            key = f"item_{_slug(name)}"
            data = {
                "description": prop.get("description", ""),
                "significance": prop.get("significance", ""),
                "first_chapter": prop.get("first_chapter", 0),
            }
            self._db.add(
                NovelEntity(
                    novel_id=novel_id,
                    entity_type="item",
                    entity_key=key,
                    name=name,
                    data_json=json.dumps(data, ensure_ascii=False),
                    status="confirmed",
                    last_chapter_index=0,
                )
            )
        self._db.commit()

    def list_confirmed(self, novel_id: str) -> list[NovelEntity]:
        return (
            self._db.query(NovelEntity)
            .filter(NovelEntity.novel_id == novel_id, NovelEntity.status == "confirmed")
            .all()
        )

    def entities_to_prompt(self, entities: list[NovelEntity]) -> str:
        if not entities:
            return "（暂无实体注册表）"
        lines = []
        for ent in entities:
            data = json.loads(ent.data_json or "{}")
            extra = []
            if data.get("location"):
                extra.append(f"位置：{data['location']}")
            if data.get("knows"):
                extra.append(f"已知：{data['knows']}")
            suffix = "；".join(extra)
            profile = data.get("profile") or data.get("traits_delta") or ""
            line = f"- {ent.name}（{data.get('role', ent.entity_type)}）：{profile}"
            if suffix:
                line += f"｜{suffix}"
            lines.append(line)
        return "\n".join(lines)

    def apply_extraction(self, novel_id: str, chapter_index: int, updates: list[dict]) -> None:
        for item in updates or []:
            key = item.get("entity_key") or ""
            if not key:
                continue
            ent = (
                self._db.query(NovelEntity)
                .filter(NovelEntity.novel_id == novel_id, NovelEntity.entity_key == key)
                .first()
            )
            patch = item.get("updates") or {}
            if ent:
                data = json.loads(ent.data_json or "{}")
                data.update({k: v for k, v in patch.items() if v})
                ent.data_json = json.dumps(data, ensure_ascii=False)
                ent.last_chapter_index = chapter_index
            else:
                data = dict(patch)
                data.setdefault("role", item.get("entity_type", ""))
                self._db.add(
                    NovelEntity(
                        novel_id=novel_id,
                        entity_type=item.get("entity_type", "character"),
                        entity_key=key,
                        name=item.get("name", key),
                        data_json=json.dumps(data, ensure_ascii=False),
                        status="confirmed",
                        last_chapter_index=chapter_index,
                    )
                )
        self._db.commit()
