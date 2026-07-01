# M5 设计：平台首页 + 小说规划确认流 + 工作台信息架构

> @author zhangzhihao  
> 依据用户 2025-06 需求：首页分区、我的作品 Tab、规划→确认→选章数→写作、向量索引时机。

## 1. 目标

| 目标 | 说明 |
|------|------|
| 平台感 | 默认进入**总览首页**，展示各产品线入口，而非直接进入视频表单 |
| 作品库 | 「我的作品」视频/小说 **Tab + 数量角标** |
| 小说创建 | **先整本规划 → 分区审阅/微调 → 确认 → 选本次写几章 → 开写** |
| 向量记忆 | 规划确认后索引 Story Bible；每章写后增量更新（沿用 M4c） |
| 工作台 | 顶栏 **正文 / 世界观 / 大纲**；左栏章节目录；右侧改稿对话 |

## 2. 路由与导航

```
/                     → HubPage（总览首页，默认 landing）
/video                → VideoCreatePage（原 HomePage 表单）
/video/progress/:id   → ProgressPage（原 /progress/:id，保留重定向）
/novel                → NovelCreatePage（仅 premise + 题材 + 目标章数）
/novel/:id            → NovelWorkbenchPage（规划审阅 / 阅读 / 续写）
/novel/:id/plan       → 可选：规划确认专用路由（Phase 1 可合并在 workbench）
/library              → LibraryPage（Tab: 视频 | 小说，带角标）
```

**Header 调整**

- Logo → `/`
- 主导航：`首页` | `视频` | `小说` | `我的作品`
- 移除 Header 内「视频/小说」双 Tab（避免与首页重复）

## 3. Hub 首页（HubPage）

**布局**：宽屏（max-width ~1100px），留白充足，深色/浅色中性配色延续现有 `#1a1a2e` 品牌色。

**区块**

| 卡片 | 文案 | 跳转 |
|------|------|------|
| 短视频 | 一句话生成完整短片 | `/video` |
| 长篇小说 | 规划世界观与大纲，AI 连载写作 | `/novel` |
| 图文 | `/article` | 预览占位 | 创建页 + 预览 |
| 我的作品 | 查看全部视频与小说 | `/library` |

**可选**：最近 3 条作品快捷入口（视频+小说混合时间排序）。

## 4. 我的作品（LibraryPage）

```
[ 视频 (n) ] [ 小说 (m) ]
─────────────────────────
卡片列表（当前 Tab）
```

- 默认 Tab：`localStorage` 记住上次；无记录时 **视频**
- 角标：当前 Tab 列表 length
- 空状态引导到对应专区

## 5. 小说创建流（重构）

### 5.1 原则

- **取消**创建页的 `plan_mode: auto`（一键规划+写作）
- **统一**为：创建 → 仅触发 **Phase A+B 规划** → `status=planned` → 进入工作台审阅
- **首写章数**不在创建页填写，在 **确认规划后** 由用户选择（1–20）

### 5.2 用户步骤

```
Step 0  /novel
        输入 premise、题材、目标章数(8–60，可空)
        POST /novels → background: plan only

Step 1  /novel/:id  (status=planning → planned)
        顶栏默认「大纲」或「世界观」Tab
        左侧导航：世界观 | 体系 | 人物 | 道具 | 卷弧 | 伏笔 | 章节大纲
        点击分区 → 主区展示可编辑内容（结构化表单 + 只读摘要）

Step 2  用户微调
        - 单字段 inline 编辑 + 保存 PATCH
        - 或右侧「改稿对话」自然语言（已有 chat API）
        保存后：sync framework_items + Chroma

Step 3  底部「确认规划，开始写作」
        弹出：本次撰写章数 [1–20]，默认 3
        POST /novels/:id/start-writing { write_count: N }

Step 4  写作中 status=writing → completed（批次结束）
        底部「续写章节」+ 章数选择 [1–20]
        POST /novels/:id/chapters/next { write_count: N }
```

### 5.3 规划内容 Schema 扩展

在 Story Bible 增加 **`items`**（道具/关键物）：

```json
"items": [{
  "id": "item1",
  "name": "古玉",
  "description": "传承载体",
  "significance": "贯穿主线",
  "first_chapter": 1
}]
```

- Phase A prompt 增加 `items[]` 输出
- `NovelFrameworkService.sync_from_bible` 索引 item
- `NovelEntityService.seed_from_bible` 同步 type=item

### 5.4 向量索引时机

| 时机 | 动作 |
|------|------|
| `apply_plan` 完成 | sync framework_items + Chroma（已有） |
| 用户 PATCH 某分区 | `save_bible` + re-sync |
| 每章写后 | postwrite 增量（已有） |

### 5.5 API 变更

| 接口 | 变更 |
|------|------|
| `POST /novels` | 移除 `plan_mode`、`initial_write_count`；仅 premise/genre/target_chapters |
| `PATCH /novels/:id/bible` | **新增**：结构化更新 world/characters/items/... |
| `POST /novels/:id/start-writing` | body: `{ write_count: 1..20 }` |
| `POST /novels/:id/chapters/next` | body: `{ write_count: 1..20 }` |
| `run_novel_generation` | 规划完 **仅** `planned`，不写正文 |

### 5.6 状态机

```
pending → planning → planned → writing → completed
                              ↘ review_required
failed ←──────────────────────────────────
```

- `planned`：等待用户确认规划
- `completed`：本批次写作结束（非全书完结）；有大纲未写仍可续写

## 6. 工作台信息架构

```
┌──────────────────────────────────────────────────────────────┐
│ 书名 · 题材 · 状态 badge          [正文] [世界观] [大纲]      │
├──────────┬───────────────────────────────┬─────────────────────┤
│ 章节目录  │ 主内容区                       │ 改稿对话           │
│ (固定)   │ Tab=正文 → 章节全文             │ (planned 时强调)   │
│          │ Tab=世界观 → 分区卡片/编辑器     │                    │
│          │ Tab=大纲 → 卷弧分组章纲         │                    │
└──────────┴───────────────────────────────┴─────────────────────┘
│ Footer: [确认规划并开始] / [续写 N 章] / 导出 / 调整后续大纲    │
└──────────────────────────────────────────────────────────────┘
```

**planned 态**

- 自动打开「世界观」或左侧「章节大纲」
- Footer 主按钮：确认规划 + 章数选择
- 「续写」禁用

**needs_review**

- 批次停止；须放行后继续

## 7. 实施分期

### Phase A — 壳层与导航（前端为主）

- HubPage、路由调整、Library Tab+角标、Header 改造
- 视频页 `/video` 迁移

### Phase B — 后端创建流

- 规划-only 生成；start-writing / continue 支持 write_count
- PATCH bible API；items schema + sync

### Phase C — 工作台 UX

- 顶栏三 Tab、规划分区编辑、确认弹窗、续写章数
- planned 默认视图

### Phase D — 验收

- pytest 覆盖新 API
- 手动：创建 → planned → 编辑 → 写 3 章 → 续写 5 章 → library 角标

## 8. 待产品确认（见对话）

- 道具是否独立 Tab，还是合并在「世界观」
- 规划分区编辑：表单直编 vs 仅对话改稿
- Hub 是否展示最近作品
- 视频旧链接 `/progress/:id` 是否 301 到 `/video/progress/:id`
