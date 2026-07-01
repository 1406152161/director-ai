# 更新日志

本文件记录项目的所有重要变更，格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 新增

- **U1 重写本章**：`POST .../chapters/{index}/rewrite` + 工作台按钮
- **U2 Beat 折叠**：正文 Tab 下场景 beat 可展开
- **U3 卷弧/伏笔 PATCH**：世界观 Tab 表单编辑 + API 字段
- **U4 规划导航**：工作台左栏「目录 / 规划」切换（planned 态默认规划）+ 分区滚动定位
- **T1–T2/T4–T6** 测试：approve 全流程、chat outline sync、rewrite、replan、retry-plan、framework sync（含道具 PATCH）
- **UX**：视频创建页 API 失败提示；测试库 SQLite StaticPool 修复 client+db_session 一致性
- **A3 SSE**：`/api/projects|novels/{id}/events` 推送进度，前端 EventSource 替代 2s 轮询（失败时降级）
- **A2 Celery**：`USE_CELERY` 开关 + 7 个 director.* 任务，API 经 `task_dispatch` 统一调度
- **阶段 6**：ProgressHub Redis pub/sub、视频 retry、小说测试/UX、SSE 重连、DELETE 作品、Alembic 骨架
- **阶段 5**：JWT 鉴权骨架、图文 API/前端、视频质量 prompt 优化、PostgreSQL 文档
- **E5/D1**：`docs/deployment.md`、README 快速开始、根 `.env.example` 索引
- **M6 千章规划**：L0/L1/L2 分层、`novel_outline_items` 表、outline 分页 API、规划 checkpoint 续跑
- **M5 平台 UX**：Hub 首页、作品库 Tab、规划确认流、工作台三 Tab、大纲 50 章/页
- **M4c 质量线**：写后校验、自动重写、needs_review 拦截、实体/框架 hybrid 检索、智谱 embedding
- **M4a+**：卷/弧/beat/伏笔/planned 写作流
- **P0 outline SSOT**：`sync_bible_indexes`、Replan/Chat 与 DB 大纲同步
- **Agent 协作**：三角色 rules/skills（设计 / 执行 / 验收）
- **执行计划**：`docs/execution-plan.md`

### 变更

- 小说规划：`bible_json.outline` 规划完成后为空，SSOT 在 DB
- `retry-plan` 断点续跑，保留已生成大纲

### 新增（历史 · M4a / M3）

- **M4a 小说线**：顶栏视频/小说/图文 Tab；题材模板；Chroma 向量记忆续写；侧栏改稿对话；导出 MD/TXT
- DeepSeek / 智谱 LLM Provider；`/api/novels` 全套
- **M3 资产一致性 + 镜头连贯性**：coherent_mode、xfade、图生图链式尾帧

### 变更

- Pipeline 状态流转：`scripting → asseting → imaging → videoing → synthesizing`
- `coherent_mode=false` 时完整回退 M2 并行视频 + concat demuxer 硬拼接

### 待办

- 视频线质量债见 `docs/backlog-quality.md`
- 添加 commitlint + husky（代码起步后启用）

## [0.1.0] - 2026-06-12

### 新增

- 项目基础配置：LICENSE、CONTRIBUTING、SECURITY、行为准则
- GitHub 协作模板：PR 模板、Issue 模板、CODEOWNERS、FUNDING.yml
- CI/CD：持续集成、Dependabot、Release 工作流
- 分支策略文档与目录结构规划
- Cursor 项目规则（`.cursor/rules/project.mdc`）
- GitHub 仓库在线配置：分支保护、Topics、Dependabot 安全更新

### 变更

- 完善 README 说明与开发指引
- 更新 `docs/github-setup.md` 配置状态清单

## [0.0.1] - 2026-06-12

### 新增

- 初始化仓库与 README

[Unreleased]: https://github.com/1406152161/director-ai/compare/v0.1.0...dev
[0.1.0]: https://github.com/1406152161/director-ai/releases/tag/v0.1.0
[0.0.1]: https://github.com/1406152161/director-ai/commit/0bc2b43
