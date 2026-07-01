# 技术质量 Backlog（可渐进优化，不阻塞产品发布）

> 记录 M3 实测后已知的技术/质量项。**策略：先出可用产品，本清单在后续版本迭代消化。**

## 成片质量

| 项 | 现状 | 优先级 | 备注 |
|----|------|--------|------|
| 角色/场景/道具跨镜一致性 | 资产三视图 prompt + 全局主体锚点 | P1 | 图生图参考策略已加强 |
| 段间音画微同步 | xfade + apad 连续旁白 | P2 | 成片混音 apad 对齐 |
| 单段画面僵硬感 | Agnes 免费模型天花板 | P3 | 接付费 SOTA 视频 API 时跃迁 |
| 分镜叙事连贯 | 相邻镜头承接 prompt 约束 | P2 | script_service 已补充 |

## 工程稳健性

| 项 | 现状 | 优先级 | 备注 |
|----|------|--------|------|
| 任务队列 Celery + Redis | `USE_CELERY=true` + Worker | 完成 | 默认仍 BackgroundTasks |
| 媒资下载失败 | 已加重试 + Agnes 鉴权 | 监控 | 弱网/CDN 偶发仍可能失败 |
| DB 迁移 | 启动 auto migrate（SQLite） | P2 | 上 PostgreSQL 时需正式 migration |
| SSE/WebSocket 实时进度 | 工作台 SSE + 轮询降级 | 完成 | ProgressPage / NovelWorkbench |

## 前端 / 体验小项

| 项 | 现状 | 优先级 | 备注 |
|----|------|--------|------|
| 成片下载链接 | 已修 Vite `/outputs` 代理 | 完成 | dev 需重启 frontend |
| 空输入 / API 失败提示 | 创建页 + 进度页 + 作品库 | 完成 | 后端离线、错误 detail、失败引导 |
| 生产环境 `VITE_API_BASE` | 有 `.env.example` | P1 | 部署时必须配置 |

## 明确不在「质量债」里、属于产品线的

见 [architecture.md](./architecture.md) M3 SaaS / M4 多模态 —— **登录、多租户、计费、作品库、部署、图文/小说** 等按产品 Backlog 推进，不与上表混为一谈。

---

最后更新：2026-06-13（M3 实测后）
