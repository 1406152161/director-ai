# M4a+ 设计：规划加厚（卷/弧/章/beat + 伏笔表 + 可选审大纲）

> **历史文档**：部分决策已被 M5/M6 取代（如 `plan_mode` 已移除、章数上限见 M6 10000、`review` 流见 M5 确认规划）。实现以代码与 `docs/m5-hub-novel-ux-design.md`、`docs/m6-mega-outline-design.md` 为准。

> 在 M4a 小说线基础上加厚规划层，支撑中长篇骨架与连贯写作。第 1 项（设定与大纲 UI）已完成；本文档为第 2 项实现依据。

## 1. 已确认决策

| 项 | 决策 |
|----|------|
| 规划层级 | **卷 → 弧 → 章 → 场景 beat**（beat 仅对待写章生成） |
| 伏笔 | **完整表**：id / 内容 / 埋设章 / 计划回收章 / 状态 / 关联人物 / 关联道具 / 关联 beat |
| 生成模式 | **可选**：`auto` 一键规划+写前 N 章；`review` 规划完暂停，用户审大纲后「开始写作」 |
| 首写章数 | 用户可选 **1–10**，默认 **3** |
| 全书章级大纲 | **动态**，硬上限 **60 章**（title + summary，不含全书 beat） |
| 卷/弧 | 按章数自动划分；60 章约 2 卷 × 多弧 |

## 2. Story Bible 扩展 Schema

```json
{
  "meta": {
    "total_chapters": 40,
    "initial_write_count": 3,
    "plan_mode": "auto",
    "target_chapters_user": 40
  },
  "world": "世界观摘要",
  "power_system": "修炼/规则/科技体系（题材相关，可为空）",
  "characters": [{
    "name": "", "role": "", "profile": "",
    "growth_arc": "起点→转折→终点"
  }],
  "volumes": [{
    "id": "v1", "title": "", "theme": "", "chapter_from": 1, "chapter_to": 20,
    "arcs": [{
      "id": "v1a1", "title": "", "conflict": "", "chapter_from": 1, "chapter_to": 8
    }]
  }],
  "outline": [{
    "index": 1, "title": "", "summary": "", "hook": "",
    "arc_id": "v1a1", "volume_id": "v1"
  }],
  "foreshadowing": [{
    "id": "fs1", "content": "", "plant_chapter": 2, "resolve_chapter": 15,
    "status": "planned",
    "linked_characters": [], "linked_items": [], "linked_beats": []
  }],
  "beats": {
    "1": [{"index": 1, "scene": "", "goal": "", "conflict": "", "outcome": ""}]
  },
  "facts": []
}
```

`beats` 键为章 index 字符串，仅已规划/待写章有 beat 列表。

## 3. 规划流程（两阶段 LLM）

```
输入：premise + genre + target_chapters + initial_write_count + plan_mode

Phase A — plan_world
  输出：world, power_system, characters, volumes, foreshadowing, meta.total_chapters

Phase B — plan_outline
  输入：Phase A 结果 + target_chapters 上限
  输出：outline[]（与 arc/volume 对齐，每章 hook）

校验：
  - outline.length 在 8..60
  - foreshadowing plant/resolve 章号 ∈ [1, total_chapters]
  - volumes/arcs chapter 范围覆盖 outline

落库 → status:
  - plan_mode=review → planned（暂停，不写正文）
  - plan_mode=auto   → writing → 写前 initial_write_count 章
```

## 4. 写作流程变更

每章写作前（若 `beats[chapter_index]` 不存在）：

1. 调用 `generate_beats(chapter_index)` — 3–6 个场景 beat  
2. 注入 prompt：Bible 摘要 + 本章 outline + beats + due 伏笔（resolve_chapter ≤ 当前章 或 status=planted 且接近 resolve）  
3. 写正文 → 摘要 → Chroma → 更新 facts + 伏笔 status（plant 章写入后 marked planted）

续写下一章：同上，受 outline 与 total_chapters 限制。

## 5. API 变更

### POST `/api/novels`

```json
{
  "premise": "...",
  "genre": "xuanhuan",
  "plan_mode": "auto",
  "initial_write_count": 3,
  "target_chapters": 40
}
```

| 字段 | 默认 | 约束 |
|------|------|------|
| plan_mode | auto | auto \| review |
| initial_write_count | 3 | 1–10 |
| target_chapters | null | 8–60，null 时由 LLM 在 Phase A 决定 |

### POST `/api/novels/{id}/start-writing`

`plan_mode=review` 且 status=`planned` 时，开始写前 `initial_write_count` 章。

### 状态

新增 `planned`：规划完成，等待用户确认写作。

## 6. 前端

### 创作页 `/novel`

- 生成模式：一键生成 / 先审大纲  
- 首写章数：1–10  
- 目标章数：8–60（可选，留空则 AI 建议）

### 工作台

- 设定面板：卷/弧树、伏笔表、人物成长线、power_system  
- `planned` 状态显示「确认大纲，开始写作」  
- beat 可在章大纲下折叠展示（有则显示）

## 7. 测试

- Mock LLM 返回两阶段 JSON  
- schema 校验、review 流程、start-writing、beat 生成 hook  
- 不依赖外网 Key

## 8. 范围外（M4c）

- 卷末 replan、60 章以后扩纲  
- 写后结构化抽取加厚（第 3 项）  
- 真 embedding（第 4 项）
