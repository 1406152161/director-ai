# M4a 设计：小说线（一句话 → 大纲 → 章节 → 续写）

> M4a 目标：在保留视频 Tab 的前提下，新增**小说创作线**——预设题材、规划大纲与人物、自动生成前 3 章、Chroma 向量记忆续写、站内阅读 + 导出 MD/TXT。借鉴 OpenNovel / NOVIX 的「规划 → 写作 → 记忆」分层，首版不做多 Agent 审稿与平台发布。

## 1. 范围与决策（已确认）

| 项 | 决策 |
|----|------|
| 产品策略 | 视频质量债见 `backlog-quality.md`；**先出小说产品** |
| 协作 | 单 Composer 实现；大脑设计 + 回测验收 |
| 首版范围 | 大纲 + 人物卡 + **自动前 3 章** + **「续写下一章」** + Chroma 记忆 |
| 单章篇幅 | **2500–3500 字**（中文） |
| 题材模板 | **玄幻 / 都市 / 悬疑 / 甜宠 / 科幻** |
| LLM | **可配置**；小说线独立 `novel_llm_provider`，默认 **deepseek**；备选 **zhipu**、**agnes** |
| 记忆 | **ChromaDB** 本地持久化（章节摘要 + 设定片段向量检索） |
| 真相文件 | SQLite JSON 字段存 **Story Bible**（世界观/人物/已发生关键事实） |
| 交互 | **向导为主** + **侧栏对话改稿**（改大纲/人设，不替代主流程） |
| 交付 | **站内阅读器**（章节目录）+ **导出 MD/TXT** |
| 前端壳 | 顶栏 **三 Tab**：视频 / 小说 / 图文（图文 Tab 占位「敬请期待」） |
| 任务 | BackgroundTasks（与视频线一致） |
| 部署 | 本轮不做；本地 + GitHub |
| CI | **不修改** `.github/workflows/` |

## 2. 用户流程

```
小说 Tab → 选题材模板 + 输入一句话创意
    → 后台：规划(plan) → 写第1–3章(write) → 每章后更新摘要入 Chroma + 更新 Story Bible
    → 小说工作台：左章节列表 / 中阅读区 / 右改稿对话
    → 用户点「续写下一章」→ 检索记忆 + 写作 → 刷新阅读
    → 导出 MD 或 TXT
```

状态流转：

```
pending → planning → writing → completed / failed
续写单章：chapter_status = pending → writing → completed / failed
```

## 3. 后端架构

```
app/
├── api/novels.py              # REST
├── models/novel.py            # Novel, NovelChapter
├── schemas/novel.py
├── services/
│   ├── novel_service.py       # CRUD、导出
│   ├── novel_plan_service.py  # 规划 prompt + JSON 解析
│   ├── novel_write_service.py # 章节写作
│   ├── novel_memory_service.py# Chroma + Story Bible 更新/检索
│   └── novel_generation_service.py  # BackgroundTasks 编排
├── novel/
│   ├── graph.py               # LangGraph 占位/轻量编排（plan → write chapters）
│   └── prompts.py             # 题材模板与 system prompt
├── providers/llm/
│   ├── deepseek.py            # OpenAI 兼容
│   └── zhipu.py               # OpenAI 兼容
└── core/migrate.py            # 补 novels / novel_chapters 表
```

### 3.1 LLM Provider

新增 OpenAI 兼容 Provider（httpx → `/v1/chat/completions`）：

| Provider | 配置项 | 默认 base |
|----------|--------|-----------|
| deepseek | `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL=deepseek-chat` | `https://api.deepseek.com` |
| zhipu | `ZHIPU_API_KEY`, `ZHIPU_MODEL=glm-4-flash` | `https://open.bigmodel.cn/api/paas/v4` |

注册表增加 `deepseek`、`zhipu`；**小说线**通过 `get_novel_llm_provider()` 读取 `novel_llm_provider`（默认 `deepseek`），与视频线 `llm_provider` 分离。

Mock LLM：返回固定 JSON 大纲与短章节正文，供 CI。

### 3.2 Story Bible + Chroma

**Story Bible**（`novels.bible_json`）结构示意：

```json
{
  "world": "世界观摘要",
  "facts": ["已发生关键事实1", "..."],
  "characters": [{"name": "...", "role": "...", "traits": "..."}],
  "outline": [{"index": 1, "title": "...", "summary": "..."}]
}
```

**Chroma**：

- 路径：`CHROMA_PERSIST_DIR=./data/chroma`（可配置，gitignore）
- 每本小说一个 collection：`novel_{id}`
- 写入：每章完成后 `summary`（200–400 字）+ 可选段落 embedding
- 续写/改稿前：`query` 取 top-k（默认 5）相关片段 + 注入 prompt

依赖：`chromadb>=0.5.0`（写入 requirements.txt / pyproject.toml）

### 3.3 规划（Plan）

输入：创意 + 题材模板 key  
输出 JSON（`parse_json_from_llm`）：

```json
{
  "title": "书名",
  "synopsis": "简介",
  "characters": [{"name": "...", "role": "...", "profile": "..."}],
  "outline": [{"index": 1, "title": "章标题", "summary": "本章要点"}],
  "world": "世界观"
}
```

要求：`outline` 至少 8 章（便于续写）；首版只**自动生成前 3 章**正文。

### 3.4 写作（Write）

每章 prompt 注入：Story Bible 摘要 + Chroma 检索 + 本章 outline + 上一章末尾 ~500 字  
`max_tokens` 足够（≥8192）；**禁止** `enable_thinking`  
目标字数 2500–3500，写后统计 `word_count`（中文按字符数近似）

### 3.5 改稿对话（Chat）

`POST /api/novels/{id}/chat`  
body: `{ "message": "把女主改成更主动的性格" }`  
逻辑：LLM 输出**修订后的 bible_json 片段或 outline**，后端 merge 进 Story Bible；**不自动重写已发布章节**（M4a 范围）。返回 assistant 回复 + 更新后的 novel。

## 4. 数据模型

### `novels`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | |
| premise | Text | 用户创意 |
| genre | String(32) | xuanhuan/dushi/xuanyi/tianai/kehuan |
| title | String(256) | |
| synopsis | Text | |
| bible_json | Text | Story Bible JSON |
| status | String(16) | pending/planning/writing/completed/failed |
| progress | int | 0–100 |
| error | Text nullable | |
| created_at | datetime | |

### `novel_chapters`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | |
| novel_id | FK | |
| index | int | 从 1 开始 |
| title | String(256) | |
| content | Text | 正文 |
| summary | Text | 章节摘要（供 Chroma） |
| word_count | int | |
| status | String(16) | pending/writing/completed/failed |

## 5. API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/novels` | 列表 |
| POST | `/api/novels` | 创建并后台生成（body: premise, genre） |
| GET | `/api/novels/{id}` | 详情 + chapters |
| POST | `/api/novels/{id}/chapters/next` | 续写下一章 |
| POST | `/api/novels/{id}/chat` | 改稿对话 |
| GET | `/api/novels/{id}/export?format=md\|txt` | 下载 |

## 6. 前端

### 路由

| 路径 | 页面 |
|------|------|
| `/` | 视频创作（现有 HomePage） |
| `/novel` | 小说创作表单 |
| `/novel/:novelId` | 工作台（章节列表 + 阅读 + 侧栏 chat） |
| `/library` | 扩展：视频项目 + 小说列表（或小说单独 `/novel/library`） |

### 顶栏 Tab

`视频 | 小说 | 图文(敬请期待)`

### 小说创作页

- 题材下拉（五类中文标签）
- 创意 textarea
- 提交 → 跳转 `/novel/:id` 轮询进度

### 工作台

- 左：章节目录 + 状态
- 中：选中章正文阅读
- 右：改稿对话（简易 chat UI）
- 底：`续写下一章` | `导出 Markdown` | `导出 TXT`

## 7. 题材模板（prompt 片段）

| key |  label | 写作提示要点 |
|-----|--------|--------------|
| xuanhuan | 玄幻 | 修炼体系、升级节奏、金手指 |
| dushi | 都市 | 现实背景、情感或职场冲突 |
| xuanyi | 悬疑 | 线索、反转、节奏紧凑 |
| tianai | 甜宠 | 人物关系、高糖互动、轻冲突 |
| kehuan | 科幻 | 设定自洽、未来感、核心矛盾 |

## 8. 配置（.env.example）

```env
# 小说线 LLM（与视频 llm_provider 独立）
NOVEL_LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
ZHIPU_API_KEY=
ZHIPU_API_BASE=https://open.bigmodel.cn/api/paas/v4
ZHIPU_MODEL=glm-4-flash
CHROMA_PERSIST_DIR=./data/chroma
NOVEL_INITIAL_CHAPTERS=3
NOVEL_TARGET_WORDS_MIN=2500
NOVEL_TARGET_WORDS_MAX=3500
```

## 9. 测试方案（mock，CI 无 Key / 无 Chroma 网络）

| 层级 | 用例 |
|------|------|
| 单元 | 规划 JSON 解析；DeepSeek/Zhipu 请求体 mock；Chroma service mock；字数统计 |
| 集成 | POST novel → mock LLM → completed + 3 chapters |
| 集成 | 续写下一章 → 第 4 章出现 |
| API | export md/txt Content-Disposition |
| 前端 | lint + build |

**质量门槛**：`pytest -q` 全绿；`npm run lint && npm run build` 通过；`@author zhangzhihao`；中文注释。

## 10. 不在 M4a 范围

- 图文 Tab 实现（仅占位）
- 番茄/公众号发布
- Reviewer 多 Agent、去 AI 味检测
- 用户登录 / SaaS / 计费
- 向量库换 Pinecone 等云服务

## 11. 文件清单（Composer 参考）

| 文件 | 动作 |
|------|------|
| `docs/m4-novel-design.md` | 本文档 |
| `backend/app/models/novel.py` | 新增 |
| `backend/app/schemas/novel.py` | 新增 |
| `backend/app/api/novels.py` | 新增 |
| `backend/app/services/novel_*.py` | 新增 |
| `backend/app/novel/prompts.py` | 新增 |
| `backend/app/providers/llm/deepseek.py`, `zhipu.py` | 新增 |
| `backend/app/providers/registry.py` | 扩展 novel provider |
| `backend/app/core/config.py`, `migrate.py` | 扩展 |
| `backend/requirements.txt` | +chromadb |
| `frontend/src/pages/Novel*.tsx` | 新增 |
| `frontend/src/App.tsx` | Tab + 路由 |
| `frontend/src/api/client.ts` | novel API |
| `backend/tests/test_novel_*.py` | 新增 |
| `CHANGELOG.md` | Unreleased |
| `.gitignore` | +data/chroma |
