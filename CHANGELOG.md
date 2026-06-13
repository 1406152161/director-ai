# 更新日志

本文件记录项目的所有重要变更，格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 新增

- **M4a 小说线**：顶栏视频/小说/图文 Tab；题材模板（玄幻/都市/悬疑/甜宠/科幻）；规划大纲 + Story Bible + 自动前 3 章；Chroma 向量记忆续写；侧栏改稿对话；站内阅读器 + 导出 MD/TXT
- DeepSeek / 智谱 OpenAI 兼容 LLM Provider；`get_novel_llm_provider()` 独立配置 `NOVEL_LLM_PROVIDER`
- 新表 `novels` / `novel_chapters`；API `/api/novels` 全套；前端 `/novel` 创作页与 `/novel/:id` 工作台
- **M3 资产一致性（M3b）**：脚本输出 `assets` 清单（角色/场景/道具），`AssetService` 文生图设定参考，关键帧 `image_to_image` 图生图
- **M3 镜头连贯性（M3a）**：串行链式真实尾帧衔接、xfade 0.4s 交叉淡化、连续旁白音轨合成
- 新表 `assets`、Shot 扩展 `character_ids/scene_id/prop_ids`
- 启动时幂等迁移 `app/core/migrate.py`（自动补表/补列）
- 配置项 `COHERENT_MODE`（默认 true）、`XFADE_DURATION`（默认 0.4）
- 前端进度页「导演设定」资产卡片网格 + `asseting` 状态展示

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
