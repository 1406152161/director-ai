---
name: director-qa
description: >-
  director-ai 验收阶段：回归测试、构建、diff 审查、通过/不通过结论。
  Use when the user says 【阶段：验收】, after 执行 Agent delivery, or before declaring work done.
---

# 验收阶段

## 必须做

1. **亲自跑命令**（不得只复述执行 Agent 自测）：

```powershell
cd backend; python -m pytest -q
cd frontend; npm run build
```

2. 针对改动跑定向测试（若适用）
3. 审查 `git diff`：是否符合设计、有无越界改动、明显 bug/安全问题
4. 可选：Task `bugbot` 做变更审查（用户要求时）
5. 给出明确结论：**通过** 或 **不通过** + 阻塞项列表

## 禁止

- 大段重写实现（只报问题；修复交回执行 Agent）
- 在无测试结果时宣布通过

## 输出模板

```markdown
## 验收结论
通过 / 不通过

## 回归结果
- backend pytest: …
- frontend build: …

## 审查发现
- 🔴 阻塞：…
- 🟡 建议：…

## 下一步
- 通过 → …
- 不通过 → 【阶段：执行】修复 …
```

## 小任务合并

用户指定 `【阶段：执行+验收】` 时：同一轮可先执行再验收，但 **验收 checklist 仍必须跑完**，且结论单独一节，不得与实现摘要混写。
