# GitHub 仓库设置清单

本文记录 **director-ai** 在 GitHub 上的配置项及当前状态。

> 最后更新：2026-06-12

## 配置状态总览

| 配置项 | 状态 | 说明 |
|--------|------|------|
| 仓库描述 | ✅ 已配置 | AI 导演平台完整描述 |
| Topics | ✅ 已配置 | ai, llm, video-generation 等 6 个标签 |
| MIT License | ✅ 已配置 | LICENSE 文件 + GitHub 元数据（合并 main 后生效）|
| 合并后自动删分支 | ✅ 已开启 | `delete_branch_on_merge: true` |
| main 分支保护 | ✅ 已开启 | 要求 PR + CI「仓库结构检查」通过 |
| dev 分支保护 | ✅ 已开启 | 要求 CI「仓库结构检查」通过 |
| Dependabot 安全更新 | ✅ 已开启 | 配合 `.github/dependabot.yml` |
| Secret Scanning | ✅ 已开启 | 公开仓库默认启用 |
| PR / Issue 模板 | ✅ 已配置 | 见 `.github/` 目录 |
| CODEOWNERS | ✅ 已配置 | 自动指定 Review 负责人 |
| FUNDING.yml | ✅ 已配置 | 赞助按钮 |
| Actions 工作流权限 | ✅ 已配置 | Read and write（Release 工作流可正常创建 Release）|
| 私有漏洞报告 | ✅ 已开启 | Security → Report a vulnerability |
| GitHub Wiki | ✅ 已关闭 | 文档统一维护在 `docs/` 目录 |
| GitHub Discussions | ✅ 已开启 | 社区讨论与 Q&A |
| Issue 标签（type/priority）| ✅ 已配置 | type: feature/bug/docs 等 + priority 系列 |
| frontend / backend 脚手架 | ⏸ 待技术栈确认 | 用户提供技术栈后初始化 |

## 1. 分支保护（Branch Protection）

### main 分支规则（已生效）

| 配置项 | 状态 |
|--------|------|
| Require a pull request before merging | ✅ |
| Require status checks to pass（`仓库结构检查`）| ✅ |
| Require branches to be up to date | ✅ |
| Do not allow bypassing（enforce_admins）| ✅ |
| Allow force pushes | ❌ 禁止 |
| Allow deletions | ❌ 禁止 |

### dev 分支规则（已生效）

| 配置项 | 状态 |
|--------|------|
| Require status checks to pass（`仓库结构检查`）| ✅ |
| Allow force pushes | ❌ 禁止 |

## 2. 默认分支与合并策略

| 配置项 | 状态 |
|--------|------|
| Default branch | `main` |
| Allow squash merging | ✅ |
| Allow merge commits | ✅ |
| Allow rebase merging | ✅ |
| Automatically delete head branches | ✅ |

## 3. Actions 权限

| 配置项 | 状态 |
|--------|------|
| Workflow permissions | ✅ Read and write |
| Release 工作流创建 Release | ✅ 可正常执行 |

路径：**Settings → Actions → General → Workflow permissions**

## 4. Dependabot

| 配置项 | 状态 |
|--------|------|
| Dependabot version updates | ✅ 配置文件已提交 |
| Dependabot security updates | ✅ 已开启 |
| Dependabot alerts | ✅ 公开仓库默认启用 |

## 5. 安全功能

| 配置项 | 状态 |
|--------|------|
| Secret scanning | ✅ |
| Secret scanning push protection | ✅ |
| Private vulnerability reporting | ✅ 已开启 |

## 6. 发布流程

```bash
# 1. dev 集成完成后，创建 PR：dev → main
# 2. CI 通过后合并
# 3. 在 main 上打 tag
git checkout main
git pull origin main
git tag -a v0.1.0 -m "v0.1.0: 项目初始化与基础配置"
git push origin v0.1.0
```

Release 工作流会自动创建 GitHub Release。

## 7. 维护命令参考

```bash
# 查看分支保护状态
gh api repos/1406152161/director-ai/branches/main/protection --jq '.required_status_checks.contexts'

# 查看仓库 Topics
gh api repos/1406152161/director-ai --jq '.topics'

# 查看最近 CI 运行
gh run list --repo 1406152161/director-ai --limit 5
```
