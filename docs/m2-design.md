# M2 设计：视频生成 + 旁白 + 合成成片

> M2 目标：在 M1（脚本/分镜 + 配图）基础上，打通到**成片**——每个镜头图生视频(Agnes) + Edge-TTS 旁白，FFmpeg 多镜头拼接合成竖屏 MP4。

## 1. 范围与决策

| 项 | 决策 |
|----|------|
| 链路 | 脚本(含运动提示) → 配图(M1) → 每镜头[图生视频 ‖ TTS 配音] → FFmpeg 合成 → 成片 MP4 |
| 视频能力 | Agnes `agnes-video-v2.0`（图生视频，配图作输入图）|
| 旁白 | Edge-TTS（中文音色，免费无 Key）|
| 字幕 | FFmpeg **烧录中文硬字幕**（用 narration_cn）|
| BGM | M2 不加 |
| 任务 | BackgroundTasks + **asyncio 并发**（不上 Celery）|
| 提速 | 多镜头视频**并发**（信号量≈3）、TTS 与视频**并行**、镜头数 ≤6、单镜 ~5s |
| 版式 | 竖屏 9:16 |

## 2. 提速策略（核心）

视频慢的根源是免费 API 异步排队 + 串行累加。M2 的工程优化：

1. **多镜头视频并发**：用 `asyncio.gather` + `Semaphore(3)` 同时提交多个视频任务并并发轮询，总时长 ≈ 最慢一段而非累加
2. **TTS 与视频并行**：TTS 很快，与视频任务同时跑
3. **限制规模**：M2 镜头数上限 6、单镜 ~5s（121 帧）
4. **Provider 可切换**：未来要更快可接入付费高优先级视频 API（架构已留口）

> 免费 API 的排队优先级是速度天花板，工程并发能榨干可用并发；进一步提速需付费档或更快模型（如 LTX-Video）。

## 3. Pipeline

```
创意 → ① 脚本/分镜(含 motion_prompt_en) → ② 配图(M1)
   → ③ 每镜头并发：
        ├─ 图生视频(Agnes，配图作输入图 + motion_prompt_en)
        └─ Edge-TTS 配音(narration_cn)            ← 与视频并行
   → ④ 每镜头 FFmpeg 合成（视频 + 配音 + 烧字幕，时长对齐）
   → ⑤ 拼接所有镜头 → 成片 MP4
```

状态流转：`pending → scripting → imaging → videoing → synthesizing → completed/failed`

## 4. 数据结构扩展

```
分镜 JSON 的 shot 增加字段：
  motion_prompt_en  # 镜头运动/动作英文提示词（镜头运动、主体动作、镜头语言）

Shot 模型新增：
  motion_prompt_en / video_url / audio_url / clip_url / clip_status
Project 模型新增：
  output_url  # 最终成片 MP4
```

分镜 prompt 增加要求：为每个镜头额外生成 `motion_prompt_en`（描述主体动作、镜头运动如 slow pan / tracking shot、保持主体一致）。

## 5. Agnes 视频接入

- **创建**：`POST {api_base}/v1/videos`
  - `model=agnes-video-v2.0`、`prompt=motion_prompt_en`、`image=配图URL`、`num_frames`、`frame_rate=24`
- **时长 → num_frames**（须 8n+1 且 ≤441）：每镜 ~5s → `121`；映射函数取最接近的合法值（81/121/161/241/441）
- **轮询**：`GET {api_base}/agnesapi?video_id=<id>`，间隔 5s，`status=completed` 时取 **`remixed_from_video_id`**（成片 URL，字段名特殊）
- 超时上限（如单镜 10 分钟）、失败重试一次、错误明确

## 6. Edge-TTS 旁白

- 依赖 `edge-tts`（免费，无需 Key）
- 中文音色默认 `zh-CN-XiaoxiaoNeural`（可配）
- `narration_cn` → mp3，记录时长用于合成对齐

## 7. FFmpeg 合成

- 通过 `subprocess` 调用本地 `ffmpeg`；不存在时抛明确错误（提示安装）
- **单镜头合成**：视频片段 + 配音 → 时长对齐 + 烧录字幕
  - **时长对齐策略**：取 `max(视频时长, 音频时长)`；视频不足则定格末帧补足，音频不足则静音补足
  - **字幕**：用 `subtitles` 滤镜烧录 narration_cn（需中文字体，随项目内置或系统字体）
- **拼接**：concat 所有镜头片段 → 输出竖屏 9:16 MP4 到对象存储/本地 `outputs/`
- 关键：分辨率/帧率统一，避免拼接失败

## 8. 任务编排（BackgroundTasks + 并发）

```python
# 伪代码
await script()                       # 串行
await images()                       # M1，逐镜配图（已并发≤2）
# 视频与配音并行，多镜头并发
sem = Semaphore(3)
await gather(*[per_shot(shot) for shot in shots])   # 每镜内部：视频 ‖ TTS
await synthesize()                   # FFmpeg 合成
```

- 进度细化：`videoing` 阶段按完成镜头数更新（视频 3/6）
- 失败隔离：单镜失败标记该镜，尽量产出其余（或整体失败，M2 先整体失败 + 明确 error）

## 9. API 与前端

- `ProjectResponse` 增加 `output_url`，shot 增加 `video_url/audio_url/clip_status`
- 成片完成后前端用 `<video>` 播放 `output_url` + 下载按钮
- 进度页展示视频生成阶段（videoing/synthesizing）与逐镜进度

## 10. 测试方案（mock，CI 不依赖网络/ffmpeg）

| 层级 | 用例 | 依赖 |
|------|------|------|
| 单元 | Agnes 视频 Provider：创建请求构造、轮询解析 `remixed_from_video_id`、时长→帧映射(8n+1)；TTS service（mock edge-tts）；FFmpeg service（mock subprocess，断言命令参数正确，**不真正跑 ffmpeg**）| mock |
| 集成 | 脚本(含 motion)→配图→视频→配音→合成 全链路 pending→completed | mock Provider/subprocess |
| API | 项目状态含 output_url/视频字段 | TestClient |
| e2e | 真实 Key + 本地 ffmpeg 跑一条出片 | `@pytest.mark.e2e`，CI 跳过 |

**质量门槛**：所有非 e2e 测试全程 mock，**不依赖网络、不依赖真实 ffmpeg、无 Key 可跑**（CI 全绿）；ffmpeg/agnes 错误明确；日志不泄露 Key；`@author zhangzhihao` + 中文注释。

## 11. 不改动 CI

FFmpeg 相关测试用 mock subprocess，**CI 不需要安装 ffmpeg**，因此**不修改 `.github/workflows/`**（避免 workflow 权限问题）。本地真实合成需用户自行安装 FFmpeg。

## 12. 不在 M2 范围（后续）

- Celery 队列、SSE 实时进度（M3）
- BGM、转场特效、多版式批量
- 角色一致性资产库（跨镜头参考图复用，M3+）
- 多租户、计费、鉴权
