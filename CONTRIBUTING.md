# 贡献指南

感谢你对 **director-ai** 的关注与贡献。本文说明如何参与开发、提交代码以及遵循的协作规范。

## 开始之前

1. Fork 本仓库，或确认你已被添加为协作者。
2. 克隆仓库并切换到 `dev` 分支：

```bash
git clone https://github.com/1406152161/director-ai.git
cd director-ai
git checkout dev
git pull origin dev
```

3. 复制环境变量模板（后端模块就绪后使用）：

```bash
cp .env.example .env
```

4. 阅读 [docs/branch-strategy.md](docs/branch-strategy.md) 了解分支与发布流程。

## 分支命名规范

| 前缀 | 用途 | 示例 |
|------|------|------|
| `feature/` | 新功能 | `feature/script-generation` |
| `fix/` | Bug 修复 | `fix/keyframe-inherit` |
| `docs/` | 文档变更 | `docs/api-readme` |
| `chore/` | 构建/工具/依赖 | `chore/ci-setup` |
| `hotfix/` | 生产紧急修复（从 `main` 切出） | `hotfix/video-export` |

**规则：**

- 日常开发从 `dev` 切出功能分支，完成后 PR 合并回 `dev`。
- 禁止直接向 `main` 推送代码。
- 功能分支合并后应及时删除。

## 提交信息规范

采用 [Conventional Commits](https://www.conventionalcommits.org/) 格式，**建议使用中文描述**：

```
<类型>(<可选范围>): <简短说明>

<可选正文：说明动机、影响范围>
```

### 类型说明

| 类型 | 含义 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档变更 |
| `style` | 代码格式（不影响逻辑） |
| `refactor` | 重构 |
| `test` | 测试相关 |
| `chore` | 构建、CI、依赖等 |
| `perf` | 性能优化 |

### 示例

```
feat(backend): 新增分镜脚本生成接口

fix(frontend): 修复关键帧继承时角色服装丢失

docs: 更新 README 部署说明

chore: 补齐 GitHub 项目基础配置
```

## Pull Request 流程

1. 确保本地分支已同步最新 `dev`。
2. 提交代码并推送到你的 Fork 或远程分支。
3. 创建 PR，**目标分支选择 `dev`**（紧急修复除外）。
4. 填写 PR 模板中的变更说明与测试方式。
5. 等待 CI 通过并完成 Code Review。
6. 合并后删除功能分支。

## 代码规范

- 新增源码文件（Java/Kotlin/Vue/TS/XML 等）类级注释统一使用 `@author zhangzhihao`。
- 保持改动最小化，匹配现有代码风格。
- 注释只解释非显而易见的业务逻辑。
- 禁止提交 `.env`、密钥、Token 等敏感信息。

## 本地检查（待前后端初始化后启用）

```bash
# 前端（示例）
cd frontend && npm run lint && npm run test

# 后端（示例）
cd backend && ruff check . && pytest
```

## 问题反馈

- Bug 报告：使用 [Bug 报告模板](.github/ISSUE_TEMPLATE/bug_report.yml)
- 功能建议：使用 [功能建议模板](.github/ISSUE_TEMPLATE/feature_request.yml)
- 安全漏洞：请参阅 [SECURITY.md](SECURITY.md)，**请勿在公开 Issue 中披露**

## 许可证

贡献的代码将按 [MIT License](LICENSE) 授权。
