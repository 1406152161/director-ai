# 分支策略

本文定义 **director-ai** 的分支模型、命名规范、合并流程与发布规范。

## 分支模型

```
main ──────────────────────────────► 稳定发布（受保护）
  ▲
  │  Release PR（dev 集成测试通过后）
  │
dev ─── feature/* ───► 日常集成开发
  │
  └── fix/* / docs/* / chore/*
```

## 分支说明

| 分支 | 用途 | 是否受保护 | 合并方式 |
|------|------|------------|----------|
| `main` | 稳定发布分支，对应线上/正式发布 | ✅ 是 | 仅通过 PR，需 CI 通过 |
| `dev` | 日常开发集成分支 | 推荐保护 | PR 合并，CI 通过 |
| `feature/*` | 新功能开发 | 否 | PR → `dev` |
| `fix/*` | Bug 修复 | 否 | PR → `dev` |
| `docs/*` | 文档变更 | 否 | PR → `dev` |
| `chore/*` | 工具/CI/依赖 | 否 | PR → `dev` |
| `hotfix/*` | 生产紧急修复 | 否 | PR → `main`，再同步回 `dev` |

## 日常开发流程

```bash
# 1. 同步最新 dev
git checkout dev
git pull origin dev

# 2. 创建功能分支
git checkout -b feature/your-feature-name

# 3. 开发并提交（遵循 Conventional Commits）
git add .
git commit -m "feat(frontend): 新增导演工作台网格视图"

# 4. 推送并创建 PR → dev
git push -u origin feature/your-feature-name
```

## 发布流程

1. 在 `dev` 上完成集成测试，更新 `CHANGELOG.md`。
2. 创建 PR：`dev` → `main`，填写变更说明。
3. CI 通过后合并到 `main`。
4. 在 `main` 上打语义化版本 tag：

```bash
git checkout main
git pull origin main
git tag -a v0.2.0 -m "v0.2.0: 首个可运行 MVP"
git push origin v0.2.0
```

5. GitHub Actions 会自动创建 Release（见 `.github/workflows/release.yml`）。

## 语义化版本

遵循 [SemVer](https://semver.org/lang/zh-CN/)：

| 变更类型 | 版本号递增 | 示例 |
|----------|------------|------|
| 不兼容 API 变更 | MAJOR | 1.0.0 → 2.0.0 |
| 向下兼容的新功能 | MINOR | 0.1.0 → 0.2.0 |
| 向下兼容的 Bug 修复 | PATCH | 0.1.0 → 0.1.1 |

## Hotfix 流程

生产环境出现紧急 Bug 时：

```bash
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug

# 修复、测试、提交
git commit -m "fix: 修复视频导出失败"

# PR → main，合并后打 patch tag
git tag -a v0.1.1 -m "v0.1.1: 修复视频导出"
git push origin v0.1.1

# 同步修复到 dev
git checkout dev
git merge main
git push origin dev
```

## GitHub 分支保护建议

在仓库 **Settings → Branches → Branch protection rules** 中配置：

### `main` 分支

- ✅ Require a pull request before merging
- ✅ Require status checks to pass（选择 `CI / 仓库结构检查`）
- ✅ Do not allow bypassing the above settings
- ✅ Restrict pushes（禁止直接 push）

### `dev` 分支（推荐）

- ✅ Require a pull request before merging（可选，小团队可放宽）
- ✅ Require status checks to pass

详细操作步骤见 [github-setup.md](github-setup.md)。

## 分支清理

- 功能分支合并后 **7 天内删除**。
- GitHub 可开启 **Automatically delete head branches**（Settings → General）。
