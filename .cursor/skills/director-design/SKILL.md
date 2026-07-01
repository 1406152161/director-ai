---
name: director-design
description: >-
  director-ai 方案设计阶段：澄清需求、提问、架构权衡、编写 docs/*-design.md。
  Use when the user says 【阶段：设计】, asks for a plan/design/architecture, or starts
  a new feature without an approved design doc.
---

# 设计阶段

## 输入

- 用户需求（可能不完整）
- 现有代码 / `docs/` 设计文档

## 必须做

1. **先判断是否要提问**（任一条成立则必须先问用户）：
   - 需求含糊或缺少验收标准
   - 2 套以上合理方案
   - breaking API、DB 迁移、默认行为变更
2. 调研现有实现（只读），避免重复造轮子
3. 输出方案：目标、范围、非目标、影响文件、API/表变更、风险、测试策略
4. 较大功能写入或更新 `docs/<topic>-design.md`（@author zhangzhihao）
5. 列出 **需用户确认的点**；未确认前不得进入执行阶段

## 禁止

- 写业务代码（`backend/`、`frontend/` 源码）
- 替验收宣布「可以通过」
- 未经确认擅自扩大范围

## 输出模板

```markdown
## 方案摘要
（1–3 句）

## 范围
- 做：…
- 不做：…

## 设计要点
…

## 影响文件
- …

## 验收标准
- [ ] …

## 待确认
1. …
```

## Handoff

用户确认（或明确「按假设执行」）后，提示下一条消息使用：`【阶段：执行】` + 设计文档路径。
