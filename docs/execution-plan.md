# director-ai 执行计划

> @author zhangzhihao  
> 三角色协作：**设计** → **执行 Agent** → **验收**  
> 调用方式：消息开头加 `【阶段：设计|执行|验收|执行+验收】`

---

## 进度总览

| 阶段 | 主题 | 状态 |
|------|------|------|
| **0** | P0 outline SSOT（Replan/Chat/sync） | ✅ 已完成 |
| **1** | 工程卫生 | ✅ 已完成 |
| **2** | 测试补洞 | ✅ T1–T6 已完成 |
| **3** | 产品 UX（质量线 + 编辑） | ✅ U1–U4 已完成 |
| **4** | 部署与文档 | ✅ E5/E6/D1/D2 已完成 |
| **5** | 架构基建（Celery/SSE/视频 UX） | ✅ A2/A3 + 视频 UX 已完成 |
| **6** | 下一迭代（生产对齐 + 闭环） | ✅ 已完成 |

---

## 角色分工

| 角色 | 负责 | 禁止 |
|------|------|------|
| **设计** | 澄清、方案、本文件 / `docs/*-design.md` | 写业务代码 |
| **执行 Agent** | 按任务 ID 改代码、补测试 | 改范围、自报验收通过 |
| **验收** | `pytest` + `npm run build` + diff 审查 | 大改实现 |

**验收命令（固定）：**

```powershell
cd backend; python -m pytest -q
cd frontend; npm run build
```

---

## 阶段 0 — 已完成 ✅

| ID | 内容 | 验收 |
|----|------|------|
| P0-1 | `sync_bible_indexes` 统一 outline DB 同步 | `test_novel_outline_sync.py` 3 例通过 |
| P0-2 | Replan 从 `novel_outline_items` 读写 | 同上 |
| P0-3 | Chat 走 sync 而非仅 `save_bible` | 同上 |

---

## 阶段 1 — 工程卫生

| ID | 任务 | Agent | 交付物 | 验收标准 |
|----|------|-------|--------|----------|
| **E1** | 更新 `CHANGELOG.md` | 执行 | Unreleased 补 M4c/M5/M6/P0 | 条目与 git 历史一致 |
| **E2** | 修正 `.gitignore` | 执行 | 增加 `backend/data/chroma/` | chroma 二进制不被 git 跟踪 |
| **E3** | 补全 `backend/.env.example` | 执行 | Agnes poll、embedding model 等 | 与 `config.py` 字段一一对应 |
| **E4** | 更新 `.cursor/rules/project.mdc` | 执行 | 技术栈改为已落地描述 | 无「待实现」误导 |

**依赖**：无  
**预估**：0.5 天

---

## 阶段 2 — 测试补洞

| ID | 任务 | Agent | 交付物 | 验收标准 |
|----|------|-------|--------|----------|
| **T1** | approve 全流程 API 测试 | 执行 | `test_novel_api.py` 新用例 | needs_review → approve → completed |
| **T2** | chat 改 outline mock 测试 | 执行 | mock LLM 返回 outline updates | DB 第 N 章 title 更新 |
| **T3** | replan 写 3 章后断言 4+ 章变化 | 执行 | `test_novel_outline_sync.py` | mock replan 改 title，ch4+ 含 replan |
| **T4** | rewrite API 测试 | 执行 | 与 U1 同批交付 | needs_review → rewrite → passed/failed |
| **T5** | PATCH 伏笔后 framework 一致性 | 执行 | `test_novel_api.py` | `novel_framework_items` + hybrid |
| **T6** | retry-plan API 测试 | 执行 | failed→planned + 409 冲突 | 不 flaky |

**依赖**：U1 完成后 T4  
**预估**：1 天

---

## 阶段 3 — 产品 UX

### U1 — 重写本章（P1 首选）⭐

| 步骤 | Agent | 内容 |
|------|-------|------|
| 设计 | 设计 | 见下文 §U1 设计 |
| 实现 | 执行 Agent | API + 编排 + 前端按钮 |
| 验收 | 验收 | pytest + build |

**API**

```
POST /api/novels/{id}/chapters/{index}/rewrite
```

- 前置：`chapter.status == needs_review`，`novel.status != writing`
- 行为：后台 `run_rewrite_chapter`，用 `validation_issues` 调 `rewrite_chapter` → 再校验 → finalize 或仍 needs_review
- 409：非 needs_review / 正在写作

**前端**

- `NovelWorkbenchPage`：needs_review 区块增加「重写本章」按钮
- `client.ts`：`rewriteNovelChapter(novelId, index)`

**影响文件**

- `backend/app/services/novel_generation_service.py` — `run_rewrite_chapter`
- `backend/app/api/novels.py` — 路由
- `frontend/src/api/client.ts`
- `frontend/src/pages/NovelWorkbenchPage.tsx`
- `backend/tests/test_novel_api.py`

---

### U2 — Beat 折叠展示

| ID | Agent | 内容 |
|----|-------|------|
| U2-D | 设计 | 正文 Tab 章下读取 `bible.beats[chapterIndex]` 折叠列表 |
| U2-E | 执行 | `NovelWorkbenchPage` + CSS |
| U2-Q | 验收 | 有 beat 的章节可见折叠区 |

**依赖**：无  
**预估**：0.5 天

---

### U3 — 卷弧 / 伏笔表单 PATCH

| ID | Agent | 内容 |
|----|-------|------|
| U3-D | 设计 | 扩展 `NovelBiblePatch` + `patch_bible` 支持 volumes/foreshadowing |
| U3-E | 执行 | 世界观 Tab 可编辑卷弧/伏笔 + 保存 |
| U3-Q | 验收 | PATCH 后 GET novel 字段一致 + framework sync |

**依赖**：无（sync 已有）  
**预估**：1–2 天

---

### U4 — M5 左侧分区导航 ✅

工作台左栏「目录 / 规划」切换；`planned` 态默认规划导航，跳转正文/世界观/大纲 Tab。

---

## 阶段 4 — 部署与文档 ✅

| ID | 任务 | 交付物 |
|----|------|--------|
| **E5** | 根 `.env.example` 索引 | 指向 backend/frontend 模板 |
| **E6** | `CHANGELOG.md` 补 U1–U4、T1–T6 | Unreleased 条目 |
| **D1** | `docs/deployment.md` | 本地/生产部署说明 |
| **D2** | 过时文档标注 | `m4a-plus-plan-design.md` 历史说明 |

---

## 阶段 6 — 下一迭代详细计划（2026-06-13 全库审计）

> **最大风险：** `USE_CELERY=true` 时 Worker 在独立进程，`ProgressHub` 内存广播 API 进程收不到 → SSE 静默失效。

### 6.0 现状快照

| 域 | 已具备 | 主要缺口 |
|----|--------|----------|
| 小说 API | 18 路由 + M4c/M6 | L2 滚动测、postwrite 自动 replan 测、validate 失败路径 |
| 视频 API | 4 路由 + M3 管线 | 无 retry/delete；仅 Agnes+mock |
| 前端 | M5 Phase A–C | 工作台 mutation 错误、大纲卷弧分组、SSE 重连 |
| 基建 | Celery 7 任务 + SSE | 跨进程进度；`pipeline/graph.py` 死代码 |

### 6.1 P0 — 生产正确性 ✅

### 6.2 P1 — 小说闭环 ✅

### 6.3 P2 — 视频补齐 ✅

### 6.4 P3 — 工程卫生 ✅

P3-1 标签统一 · P3-2 ProgressBar/StatusBadge/QueryState · P3-3 OutlinePanel 拆分 · P3-4 pipeline/graph 废弃标注 · P3-5 DELETE 作品 API · P3-6 Alembic 骨架

### 6.5 建议排期

Sprint A：P0 · Sprint B：P1-1～3+测试 · Sprint C：P1-4～7 · Sprint D：P2 · Sprint E：P3

**只选一件：P0-1 Celery+SSE**

---

## 阶段 5 — 远期 backlog

| ID | 内容 | 状态 |
|----|------|------|
| A1 | PostgreSQL + pgvector | ✅ Alembic 骨架 + 部署文档 |
| A2 | Celery 替代 BackgroundTasks | ✅ |
| A3 | SSE 进度推送 | ✅ |
| A4 | SaaS 登录 / 多租户 | ✅ 骨架（AUTH_ENABLED 可选） |
| A5 | 视频线生产 Provider 配置文档 | ✅ deployment.md |
| A6 | 图文产品线 | ✅ API + 创建/预览页 |

---

## 当前迭代排期（建议）

```
Week 1
  Mon   E1–E4 工程卫生          [执行 → 验收]
  Tue   U1 重写本章             [设计 ✅ → 执行 → 验收]
  Wed   T1 + T4 测试            [执行 → 验收]
  Thu   U2 Beat UI              [执行 → 验收]
  Fri   U3 卷弧/伏笔 PATCH      [设计 → 执行 → 验收]

Week 2+
  阶段 4 按产品优先级单独立项
```

---

## 任务领取方式

对用户：

```
【阶段：执行】做 E1–E4
【阶段：执行】做 U1
【阶段：验收】
```

对 Agent：读本文 ID → 只做范围内文件 → 交付模板见 `.cursor/skills/director-implement/SKILL.md`

---

## 变更记录

| 日期 | 说明 |
|------|------|
| 2026-06-13 | 初版；P0 完成；阶段 1+U1 启动 |
| 2026-06-13 | E1–E4 完成；U1 重写本章 API/前端/测试交付 |
| 2026-06-13 | T1 approve 全流程 + T2 chat outline sync 测试 |
| 2026-06-13 | U2 Beat 折叠展示 + U3 卷弧/伏笔 PATCH |
| 2026-06-13 | E5/D1 部署文档 + U4 规划导航 + T3/T5/T6 测试 |
| 2026-06-13 | A2 Celery + A3 SSE + 视频 UX；阶段 6 下一迭代计划 |
| 2026-06-13 | 阶段 6 全量：Redis SSE、视频 retry、小说测试/UX、SSE 重连 |
| 2026-06-13 | 阶段 5：JWT 鉴权、图文线、视频质量优化、PostgreSQL/Alembic |
