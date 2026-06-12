# director-ai 架构设计

> AI 自动视频导演平台 — 让普通用户用一句话生产完整视频（一期），后续扩展图文、小说。

## 1. 产品定位与决策

| 维度 | 决策 |
|------|------|
| 产品形态 | **SaaS 云平台**（多租户、注册即用、计费、任务队列）|
| 首期 MVP | **视频生成线**（最契合"导演"定位，差异化最强）|
| 目标用户 | **C 端普通用户**（极简体验，一句话一键出片）|
| AI 能力来源 | **纯第三方 API**（无需自建 GPU，按量付费，快速上线）|
| 后端 | **Python + FastAPI**（AI 生态最佳，LangGraph/LangChain 原生）|
| 前端 | **React + TypeScript + Vite** |

### 北极星体验

> 一个输入框 + 风格/时长/版式选择 → 点「开始创作」→ 实时进度 → 预览成片 → 下载 / 分发。
> 所有复杂度藏在后端 Pipeline，对用户零门槛。

## 2. 整体架构

```
┌─────────────────────────────────────────────┐
│  前端 React + TS + Vite                       │
│  创意输入 / 进度看板 / 预览播放 / 我的作品      │
└───────────────┬─────────────────────────────┘
                │ REST + SSE/WebSocket（实时进度）
┌───────────────▼─────────────────────────────┐
│  FastAPI 网关                                  │
│  鉴权 · 多租户 · 计费/配额 · 限流 · 任务提交    │
└───────────────┬─────────────────────────────┘
                │
┌───────────────▼─────────────────────────────┐
│  LangGraph 编排引擎  ←→  Celery + Redis 队列   │
│  有状态工作流 · 节点重试 · 进度回传            │
└───────────────┬─────────────────────────────┘
                │
┌───────────────▼─────────────────────────────┐
│  Provider 适配层（可插拔原子能力）             │
│  LLM · 图像 · 视频 · TTS · 字幕 · 合成         │
│  统一接口，屏蔽厂商差异，支持降级与切换        │
└───────────────┬─────────────────────────────┘
                │
┌───────────────▼─────────────────────────────┐
│  存储层                                        │
│  PostgreSQL(业务) · Redis(队列/缓存)           │
│  对象存储 OSS/S3(媒资) · 向量库(角色一致性,可选)│
└─────────────────────────────────────────────┘
```

### 分层职责

| 层 | 职责 | 关键技术 |
|----|------|----------|
| 前端 | 极简交互、实时进度、作品管理 | React 18、TypeScript、Vite、TanStack Query、Zustand |
| API 网关 | 鉴权、多租户、计费、任务提交 | FastAPI、Pydantic、JWT、SQLAlchemy |
| 编排 | 视频生成工作流、状态机、重试 | LangGraph、Celery、Redis |
| 适配层 | 统一封装各 AI 厂商能力 | 自研 Provider 抽象（策略模式）|
| 存储 | 业务数据、媒资、缓存、向量 | PostgreSQL、Redis、MinIO/OSS、Chroma(可选) |

## 3. 视频生成 Pipeline

借鉴 [Pixelle-Video](https://github.com/AIDC-AI/Pixelle-Video) 的全自动流水线与 [BigBanana-AI-Director](https://github.com/shuyu-labs/BigBanana-AI-Director) 的 Script→Asset→Keyframe 工业化工作流。

```
创意输入（1 句话 / 1-200 字）
   │
   ▼
① 脚本 & 分镜（LLM）
   故事扩写 → 分镜脚本（每镜：旁白/台词、画面描述、时长、镜头语言）
   │
   ▼
② 资产生成（图像，保证一致性）
   角色设定图 / 场景图 / 道具图 —— 复用以保证跨镜头一致
   │
   ▼
③ 关键帧（图像）
   每个分镜首帧（可选尾帧），读取角色+场景上下文
   │
   ▼
④ 视频片段（图生视频 / 首尾帧插值）
   逐镜头生成动态片段
   │
   ▼
⑤ 配音（TTS）  →  ⑥ 字幕（时间轴对齐）
   │
   ▼
⑦ BGM（背景音乐 / 音效）
   │
   ▼
⑧ 合成（FFmpeg）：片段 + 配音 + 字幕 + BGM → 成片 MP4
   │
   ▼
预览 / 下载 / 分发
```

### 工程要点

- **节点级可视化与重试**：每个步骤状态实时回传，失败可单独重跑（借鉴 kaka-02/ai-director 的 Pipeline 可视化）。
- **角色一致性**：资产阶段生成的角色/场景图作为后续关键帧的参考输入（Context 注入），降低"不连戏"。
- **异步长任务**：视频生成耗时长，全程走 Celery 队列，前端 SSE/WebSocket 订阅进度。
- **成本可控**：分级模型（草稿用便宜模型预览，定稿再用高质量模型）、结果缓存、幂等重试。

## 4. Provider 适配层（核心设计）

所有 AI 能力通过统一接口封装，配置驱动，可热切换厂商，避免供应商锁定。

```python
# 统一能力接口（示意）
class VideoProvider(Protocol):
    async def image_to_video(self, image_url: str, prompt: str, duration: int) -> VideoResult: ...

class LLMProvider(Protocol):
    async def chat(self, messages: list[Message], **kw) -> str: ...
```

| 能力 | 起步推荐（高性价比） | 可选替代 |
|------|----------------------|----------|
| LLM（脚本/分镜）| DeepSeek | OpenAI、通义千问、Kimi |
| 文生图 / 图生图 | 即梦 Seedream、通义万相 | 可灵、OpenAI gpt-image |
| 图生视频 / 文生视频 | 可灵 Kling、即梦 Seedance | Vidu、海螺、Runway |
| TTS 配音 | Edge-TTS（免费）| 阿里云、Minimax、火山 |
| 字幕 | 脚本时间轴对齐（无需额外 API）| Whisper、云 ASR |
| BGM | 内置素材库 | Suno（可选）|

## 5. 数据模型（核心表）

```
users              用户（多租户、配额、计费）
projects           项目（一次创作任务）
  ├─ story         创意/故事
  ├─ script        分镜脚本（JSON：镜头数组）
  ├─ assets        资产（角色/场景/道具图）
  ├─ shots         镜头（关键帧、视频片段、配音、字幕）
  └─ output        成片（MP4、封面、时长）
pipeline_runs      Pipeline 执行记录（节点状态、重试、耗时）
provider_configs   各厂商 API 配置（密钥走环境变量/密钥管理）
usage_records      用量与计费记录
```

## 6. 目录结构（规划）

```
director-ai/
├── frontend/                # React + TS + Vite
│   ├── src/
│   │   ├── pages/           # 首页输入 / 进度 / 预览 / 作品库
│   │   ├── components/
│   │   ├── api/             # 接口封装
│   │   └── store/           # 状态管理
│   └── package.json
├── backend/                 # FastAPI
│   ├── app/
│   │   ├── main.py          # 入口
│   │   ├── api/             # 路由（projects/pipeline/auth/settings）
│   │   ├── core/            # 配置、鉴权、依赖
│   │   ├── pipeline/        # LangGraph 工作流 + 节点
│   │   ├── providers/       # Provider 适配层（llm/image/video/tts）
│   │   ├── models/          # SQLAlchemy 模型
│   │   ├── schemas/         # Pydantic
│   │   ├── tasks/           # Celery 任务
│   │   └── services/        # 业务服务
│   ├── pyproject.toml
│   └── requirements.txt
└── docs/
```

## 7. 分阶段路线图

| 阶段 | 目标 | 交付 |
|------|------|------|
| **M0** 脚手架 | 前后端骨架跑通、Provider 抽象、CI 接入 lint/test | 可启动的空架子 |
| **M1** 最小闭环 | 一句话 → 单/少分镜 → 配图 → 配音 → 合成 → 出片 | 端到端 Demo（图生视频可后置）|
| **M2** 工业化 | 多分镜 + 角色一致性 + 节点重试 + 进度看板 | 完整视频生成体验 |
| **M3** SaaS 化 | 注册登录、多租户、配额计费、任务队列扩展 | 可对外的云平台 |
| **M4** 多模态扩展 | 复用编排引擎，接入图文线、小说线 | 三合一内容平台 |

## 8. 引擎复用（面向图文/小说扩展）

视频线沉淀的「LangGraph 编排 + Provider 适配 + 长期记忆」是通用底座：

- **图文线**：复用 LLM + 图像能力，替换合成节点为「排版/卡片生成」（借鉴 content-agent、moka）。
- **小说线**：复用编排 + 记忆，引入多智能体（规划/写作/编辑/审稿/记忆）与向量长期记忆（借鉴 OpenNovel、InkFlow）。

## 9. 安全与成本

- API 密钥统一走环境变量 / 密钥管理，绝不入库（见 `SECURITY.md`）。
- 计费与配额前置校验，防止恶意刷量。
- 草稿/预览用低成本模型，定稿再升级，控制单次成本。
- 媒资走对象存储 + CDN，降低带宽与存储成本。

## 10. 参考开源项目

| 项目 | 借鉴点 |
|------|--------|
| [Pixelle-Video](https://github.com/AIDC-AI/Pixelle-Video) | 全自动短视频流水线、原子能力组合、直连 API 设计 |
| [BigBanana-AI-Director](https://github.com/shuyu-labs/BigBanana-AI-Director) | Script→Asset→Keyframe 工业化工作流、角色一致性 |
| [kaka-02/ai-director](https://github.com/kaka-02/ai-director) | Pipeline 可视化、节点失败重试、FastAPI 全栈 |
| [OpenNovel](https://github.com/Cppys/OpenNovel) | LangGraph 多智能体、向量长期记忆（小说线）|
| [content-agent](https://github.com/qiuxchao/content-agent) | 多平台图文生成、配图策略（图文线）|
