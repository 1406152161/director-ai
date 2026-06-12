# director-ai

AI 导演平台 — 从灵感到成片的工业化创作工作流（Script → Asset → Keyframe → Video），由 Cursor 辅助生成与迭代。

[![CI](https://github.com/1406152161/director-ai/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/1406152161/director-ai/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## 功能阶段（规划）

| 阶段 | 说明 |
|------|------|
| 剧本 | 创意输入 → 故事 → 分镜脚本 |
| 资产 | 角色 / 场景 / 道具一致性管理 |
| 镜头 | 关键帧生成、九宫格分镜、视频合成 |

## 分支说明

| 分支 | 用途 |
|------|------|
| `main` | 稳定发布 |
| `dev` | 日常开发（**默认工作分支**） |
| `feature/*` | 新功能分支，合并到 `dev` |
| `fix/*` | Bug 修复分支 |
| `hotfix/*` | 生产紧急修复，合并到 `main` |

详细流程见 [docs/branch-strategy.md](docs/branch-strategy.md)。

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/1406152161/director-ai.git
cd director-ai

# 切换到 dev 分支
git checkout dev

# 复制环境变量模板（后端就绪后使用）
cp .env.example .env

# 创建功能分支开始开发
git checkout -b feature/your-feature-name
```

## 项目结构

```
director-ai/
├── frontend/          # 导演工作台 UI（React + TypeScript + Vite）
├── backend/           # API 与 Pipeline 编排
├── docs/              # 设计文档与 GitHub 设置说明
├── .cursor/rules/     # Cursor AI 项目规则
├── .github/           # CI/CD、Issue/PR 模板、Dependabot
├── CONTRIBUTING.md    # 贡献指南
├── CHANGELOG.md       # 更新日志
├── LICENSE            # MIT 开源许可
└── SECURITY.md        # 安全策略
```

## 协作规范

- 提交信息：遵循 [Conventional Commits](https://www.conventionalcommits.org/)，建议使用中文描述
- 贡献流程：请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)
- 行为准则：请参阅 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- GitHub 设置：请参阅 [docs/github-setup.md](docs/github-setup.md)

## 发布

版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。在 `main` 分支打 tag 后，Release 工作流会自动创建 GitHub Release：

```bash
git tag -a v0.1.0 -m "v0.1.0: 描述"
git push origin v0.1.0
```

变更记录见 [CHANGELOG.md](CHANGELOG.md)。

## 许可证

本项目采用 [MIT License](LICENSE) 开源。
