# M4c 质量路线图（质量优先）

> 目标：**主线不跑偏、人设不崩、伏笔能收、设定少矛盾**。向量检索放 Q4；先做校验、硬注入、replan。

## 里程碑

| 阶段 | 内容 | 状态 |
|------|------|------|
| **Q1** | 写后校验 + 低分自动重写 1 次 + 失败标黄 + 拦截续写 | ✅ 已实现 |
| **Q2** | 实体注册表 + Mandatory 分层 Prompt + 伏笔回收注入埋设章片段 | ✅ 已实现 |
| **Q3** | 写后结构化抽取 + 卷/弧 replan + 滚动摘要 | ✅ 已实现 |
| **Q4** | framework_items + hybrid 检索 + **DeepSeek/智谱 Embedding** | ✅ 已实现 |

---

## Q1：写后校验 + 重写 + 拦截

### 流程

```
写正文 → 校验(规则+LLM)
  → 通过：入库 summary/Chroma/facts/伏笔状态，status=completed
  → 不通过：带 issues 重写 1 次 → 再校验
      → 仍不通过：status=needs_review，不写记忆，novel=review_required，停止批量续写
```

### 校验项

| 项 | 方式 |
|----|------|
| 字数区间 | 规则 |
| 正文非空 | 规则 |
| beat 覆盖 | LLM |
| 本章伏笔任务（埋/收） | LLM + 规则对照 plant/resolve 章号 |
| 与 outline 对齐 | LLM |
| 与人设/世界观明显冲突 | LLM |

### 通过标准

- `score >= 70` 且 `passed=true`（LLM JSON）
- 规则项全部通过

### 数据

`novel_chapters` 新增：

- `validation_status`: pending | passed | needs_review
- `validation_score`: int
- `validation_issues`: JSON 数组字符串

`novels.status` 新增值：`review_required`

### API

- 续写 / 批量写作前：若存在 `needs_review` 章节 → 409
- 前端展示 issues，后续 Q1+ 可加「确认放行 / 重写本章」

---

## Q2：实体表 + Mandatory Prompt（设计摘要）

- 表：`novel_entities`（character/item/location/timeline）
- 写前 P0 块：本章 outline、beats、due 伏笔、涉及实体 confirmed 状态
- 回收伏笔：注入埋设章原文片段（DB 按 chapter_id 截取）

---

## Q3：抽取 + Replan + 摘要（设计摘要）

- 写后抽取 → `draft` → `confirmed` 才进记忆
- 每 10–20 章 replan 未写 outline（已写 locked）
- 卷/弧/全书滚动摘要字段入 bible 或独立表

---

## Q4：Hybrid 检索（设计摘要）

- SSOT：结构化 framework_items
- Chroma：confirmed 片段 + 章摘要，BM25 + embedding
