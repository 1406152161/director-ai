# M1 设计：创意 → 脚本/分镜 → 配图

> M1 目标：打通第一个端到端闭环——用户输入一句话创意，生成结构化分镜脚本并为每个镜头生成竖屏配图。**不含视频、音频、合成**（后续阶段接入）。

## 1. 范围与决策

| 项 | 决策 |
|----|------|
| 链路 | 创意(中文) → 脚本/分镜(LLM) → 逐镜头配图(Image) → 分镜卡片 / 作品库 |
| AI 能力 | Agnes：`agnes-2.0-flash`（文本）、`agnes-image-2.1-flash`（图像）|
| 默认版式 | 竖屏 9:16 优先 |
| 音频 | 不在 M1（含视频阶段用 Edge-TTS + FFmpeg）|
| 持久化 | SQLite + SQLAlchemy |
| 任务 | FastAPI BackgroundTasks + 前端状态轮询（Celery/SSE 留后续）|
| 配图上限 | 单项目最多 8 张（控速、控免费额度）|

## 2. 端到端链路

```
创意输入(中文)
   │
   ▼
① 脚本 & 分镜（agnes-2.0-flash，开 enable_thinking）
   输出结构化分镜 JSON：镜头号 / 中文画面 / 英文图像提示词 / 旁白文案 / 时长
   │
   ▼
② 逐镜头配图（agnes-image-2.1-flash，9:16）
   英文提示词 + 风格词 → 竖屏图，串行/小并发防限流
   │
   ▼
分镜卡片展示（配图 + 画面描述 + 旁白） / 作品库
```

LangGraph 中 `script_node`、`image_node` 真实实现；`keyframe/video/tts/compose` 继续占位。

## 3. Agnes Provider 实现要点

### 3.1 端点（基于官方文档，注意坑）

| 能力 | 方法与路径 |
|------|-----------|
| 文本 | `POST {AGNES_API_BASE}/v1/chat/completions` |
| 图像 | `POST {AGNES_API_BASE}/v1/images/generations` |
| 视频创建（后续）| `POST {AGNES_API_BASE}/v1/videos` |
| 视频查询（后续）| `GET {AGNES_API_BASE}/agnesapi?video_id=<id>`（**不在 /v1 下**）|

### 3.2 AgnesLLMProvider

- OpenAI 兼容请求：`{model, messages, temperature, max_tokens}`
- 分镜规划开启 `chat_template_kwargs.enable_thinking = true` 提升结构化质量
- 响应取 `choices[0].message.content`
- Context 256K / Max Output 65.5K（按此约束设计 prompt 与 max_tokens）

### 3.3 AgnesImageProvider（参数位置严格）

- 文生图必填：`model`、`prompt`、`size`（如 `"768x1344"`）
- `response_format` **必须放 `extra_body`**（放顶层会 400）
- URL 输出：`extra_body.response_format = "url"` → 取 `data[0].url`
- 图生图（后续）：输入图放 `extra_body.image` 数组，**不要传 `tags`**
- 客户端超时 60–360s

## 4. 关键映射规则（代码常量）

```
版式 → 图像 size：
  9:16  → "768x1344"
  16:9  → "1344x768"
  1:1   → "1024x1024"

风格 → 英文提示词片段：
  cinematic   → "cinematic realism, film still, dramatic lighting"
  anime       → "anime style, vibrant colors, clean lineart"
  documentary → "documentary photography, natural lighting, realistic"
  vlog        → "casual vlog style, bright, candid"

时长 → 镜头数（约每镜 4s，M1 上限 8）：
  15s→4, 30s→7, 60s→min(12,8)=8, 120s→min(20,8)=8
```

## 5. 分镜脚本 JSON 结构

```json
{
  "title": "短片标题",
  "shots": [
    {
      "index": 1,
      "scene_cn": "中文画面描述",
      "image_prompt_en": "english image prompt with style/lighting/composition",
      "narration_cn": "该镜头旁白文案",
      "duration": 4
    }
  ]
}
```

- LLM 必须输出可解析 JSON；解析器需容错（去除 markdown ```json 包裹、首尾噪声）
- 图像提示词用英文（稳定性更好），中文画面/旁白给用户看

## 6. 数据模型（SQLite）

```
Project
  id (uuid) / story / style / duration / aspect_ratio
  status (pending|scripting|imaging|completed|failed)
  progress (0-100) / title / error / created_at
Shot
  id / project_id(FK) / index
  scene_cn / image_prompt_en / narration_cn / duration
  image_url / status
```

## 7. API 设计

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/projects` | 创建项目并触发后台生成，返回 project_id |
| GET | `/api/projects/{id}` | 查询状态、进度、分镜与配图 |
| GET | `/api/projects` | 项目列表（作品库）|
| GET | `/api/health` | 健康检查（已有）|

- 生成走 `BackgroundTasks`；前端轮询 `GET /api/projects/{id}` 获取进度
- 状态流转：pending → scripting → imaging → completed（失败置 failed 并记 error）

## 8. 前端

- HomePage：提交创意 → `POST /api/projects` → 跳进度页
- ProgressPage：轮询展示（脚本生成中 → 配图 3/6 …）
- 结果/详情：竖屏分镜卡片（配图 + 中文画面 + 旁白）
- LibraryPage：项目列表
- 默认版式 9:16

## 9. 测试方案

| 层级 | 用例 | 依赖 |
|------|------|------|
| 单元 | LLM/Image Provider 请求体构造与响应解析（`extra_body`、`data[0].url`）、registry 选 agnes、size/style/duration 映射、JSON 容错解析 | mock httpx，CI 必过 |
| 集成 | 脚本生成（结构化 + markdown 包裹容错）、逐镜头配图、脚本→配图全链路 pending→completed | mock Provider |
| API | 创建 / 查询 / 列表项目 | FastAPI TestClient |
| 端到端冒烟 | 真实 Key 跑「橘猫雨夜东京」→ 出脚本 + 可访问竖屏图 | `@pytest.mark.e2e`，CI 跳过，本地手动 |

**质量门槛**：自动化测试全程 mock 不依赖网络（CI 全绿）；Provider 对 401/400/超时有明确异常；日志脱敏不泄露 API Key；`@author zhangzhihao` + 中文注释；ruff 通过。

## 10. 不在 M1 范围（占位/后续）

- 视频生成（agnes-video-v2.0，异步轮询，单条 ≤441 帧≈18s，多分镜拼接）
- TTS 旁白（Edge-TTS）+ FFmpeg 合成
- Celery 队列、SSE 实时进度
- 多租户、计费、鉴权
