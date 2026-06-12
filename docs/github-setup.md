# GitHub 仓库设置清单

本文提供 **director-ai** 在 GitHub 上需要手动完成的配置步骤（无法通过代码仓库文件自动生效的部分）。

## 1. 分支保护（Branch Protection）

路径：**Settings → Branches → Add branch protection rule**

### main 分支规则

| 配置项 | 建议值 | 说明 |
|--------|--------|------|
| Branch name pattern | `main` | 保护稳定发布分支 |
| Require a pull request before merging | ✅ | 禁止直接 push |
| Require approvals | 1（可选） | 至少一人 Review |
| Require status checks to pass | ✅ | 勾选 `CI / 仓库结构检查` |
| Require branches to be up to date | ✅ | 合并前需同步最新 main |
| Do not allow bypassing | ✅ | 管理员也受约束 |
| Restrict who can push | ✅（可选） | 限制直接推送权限 |

### dev 分支规则（推荐）

| 配置项 | 建议值 |
|--------|--------|
| Branch name pattern | `dev` |
| Require status checks to pass | ✅ |
| Require a pull request before merging | 可选 |

## 2. 默认分支与合并策略

路径：**Settings → General**

- **Default branch**：开发阶段可保持 `main`；若团队主要在 `dev` 工作，可在 README 中明确 `dev` 为日常分支（当前已说明）。
- **Allow merge commits**：✅
- **Allow squash merging**：✅（推荐用于功能分支合并，保持历史整洁）
- **Allow rebase merging**：可选
- **Automatically delete head branches**：✅ 合并后自动删除功能分支

## 3. Actions 权限

路径：**Settings → Actions → General**

- **Actions permissions**：Allow all actions and reusable workflows
- **Workflow permissions**：Read and write permissions（Release 工作流需要 `contents: write`）

## 4. Dependabot

路径：**Settings → Code security and analysis**

启用以下选项：

- ✅ Dependabot alerts
- ✅ Dependabot security updates
- ✅ Dependabot version updates（配置文件已位于 `.github/dependabot.yml`）

## 5. 安全功能

路径：**Settings → Code security and analysis**

- ✅ Secret scanning（若仓库为 Public 或组织已启用）
- ✅ Private vulnerability reporting（配合 `SECURITY.md`）

## 6. Issue / PR 模板

已通过以下文件自动生效，无需额外配置：

- `.github/pull_request_template.md`
- `.github/ISSUE_TEMPLATE/bug_report.yml`
- `.github/ISSUE_TEMPLATE/feature_request.yml`

## 7. 使用 gh CLI 快速配置（可选）

若已安装 [GitHub CLI](https://cli.github.com/) 且已登录，可执行：

```bash
# 为 main 启用基础分支保护（需仓库管理员权限）
gh api repos/1406152161/director-ai/branches/main/protection \
  --method PUT \
  -f required_status_checks='{"strict":true,"contexts":["仓库结构检查"]}' \
  -f enforce_admins=true \
  -F required_pull_request_reviews='{"required_approving_review_count":0}' \
  -f restrictions=null
```

> 注意：CI status check 名称需在 Actions 首次运行后才能准确匹配；若命令失败，请在网页端手动配置。

## 8. 发布首个版本

```bash
git checkout main
git merge dev
git tag -a v0.1.0 -m "v0.1.0: 项目初始化与基础配置"
git push origin main
git push origin v0.1.0
```

Release 工作流会自动在 GitHub Releases 页面创建发布记录。
