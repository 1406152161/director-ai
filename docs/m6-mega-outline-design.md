# M6 设计：千章级分层规划（L0/L1/L2 + 滚动细纲）

> @author zhangzhihao  
> 用户确认：全书不设 1000 硬顶；用户填目标 N 章时，AI 可在 **N±200** 内定最终 `total_chapters`；L2 近端窗口 **60 章**；L1 骨架可见可编辑；远端随写作滚动展开。

## 1. 三层规划

| 层 | 内容 | 批次 | 存储 |
|----|------|------|------|
| **L0** | 世界观/人物/道具/卷弧/伏笔表 + 最终章数 | 1 次 | bible_json + framework_items |
| **L1** | 全书骨架：每章 title + 一句 summary（无 hook） | 25 章/批，锁定前缀 | novel_outline_items (`skeleton`) |
| **L2** | 近端详细：summary 扩写 + hook，对齐弧/伏笔 | 10 章/批 | novel_outline_items (`detailed`) |

## 2. 章数策略

- 用户 `target_chapters`：8–10000（留空由 AI 建议，默认区间 40–120）
- L0 输出 `meta.total_chapters`，若用户指定 T，须满足 **T−200 ≤ total ≤ T+200**
- 卷/弧 `chapter_to` 随 total 自动校验覆盖

## 3. 防幻读

- 每批 L1/L2 输入：**锁定前缀** + **弧段契约** + **衔接锚点**（前 3 章全文）
- 批后程序化校验：index 连续、arc_id 合法、伏笔章号范围
- L2 初始仅 **1..60**；写到第 N 章时若 N+30 无 detailed，触发 `expand_l2(N+1, N+30)`

## 4. API

- `GET /novels/{id}/outline?from=&to=&detail=` 分页读大纲
- `bible_json.outline` 规划完成后为空数组，meta 标记 `outline_in_db: true`
- 写作/校验从 DB 读 outline

## 5. 进度

- `planning` 期间 `progress` = L1 已完成章数 / total * 80
- `planned` = L0+L1 完成且 L2 窗口（1..60）就绪
