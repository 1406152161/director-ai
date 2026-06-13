# M3 设计：资产一致性 + 镜头连贯性（M3a + M3b）

> M3 目标：在 M2（脚本→配图→视频→旁白→合成）基础上，通过**角色/场景/道具资产库 + 图生图**解决跨镜头主体漂移，通过**链式真实尾帧 + xfade 转场 + 连续旁白**解决「PPT 硬切」感。开发期继续用免费 Agnes，架构预留 Provider 切换。

## 1. 范围与决策（已确认）

| 项 | 决策 |
|----|------|
| 范围 | **M3a + M3b 一起做** |
| M3b 资产 | **角色 + 场景 + 道具** 各生成设定参考图，后续关键帧用图生图 |
| M3a 衔接 | **链式真实尾帧**（串行）：镜 N 视频末帧 → 镜 N+1 图生视频输入 |
| M3a 合成 | **xfade 交叉淡化**（默认 0.4s）+ **连续旁白音轨**（先拼接 mp3 再混音） |
| 前端 | 进度页展示 **「导演设定」** 资产卡片 + 关键帧缩略图 |
| 数据库 | **启动时自动补列/建表**，禁止要求用户手动删库 |
| 任务 | 仍用 BackgroundTasks（不上 Celery） |
| 回退 | `coherent_mode=false` 时恢复 M2 行为（无资产、并行视频、硬拼接） |
| 模型 | 继续 Agnes 免费 API；不接入付费模型（后续 M4+） |

### 预期与边界

- **会改善**：段间跳变、硬切、旁白停顿、角色/场景/道具跨镜不一致
- **仍受限**：Agnes 单段画面僵硬感、免费 API 排队慢；链式串行后总耗时显著长于 M2
- **诚实目标**：在当前免费模型下把工程侧榨到上限，非对标 Sora/可灵原生长视频

## 2. Pipeline

```
创意输入
   │
   ▼
① 脚本 & 分镜（LLM，含 assets 清单 + 每镜资产引用）
   │
   ▼
② 资产生成 asseting（角色/场景/道具设定图，文生图）  ← 前端展示「导演设定」
   │
   ▼
③ 关键帧 imaging（每镜图生图，extra_body.image=相关资产 URL）
   │
   ▼
④ 视频 videoing（串行链式尾帧）
     镜1：关键帧1 → 图生视频
     镜2：extract_tail(镜1) → 图生视频
     镜N：extract_tail(镜N-1) → 图生视频
     TTS 可与视频等待并行（每镜旁白仍先生成 mp3）
   │
   ▼
⑤ 合成 synthesizing
     单镜：视频 + 该镜旁白 + 硬字幕（时间轴对齐连续音轨）
     成片：xfade 拼接 + 铺连续旁白轨
   │
   ▼
预览 / 下载
```

状态流转：

```
pending → scripting → asseting → imaging → videoing → synthesizing → completed/failed
```

进度建议：`scripting 10→20` · `asseting 20→30` · `imaging 30→50` · `videoing 50→75` · `synthesizing 75→100`

## 3. 脚本 JSON 扩展

LLM 输出在 M2 基础上增加 `assets` 与每镜引用：

```json
{
  "title": "短片标题",
  "assets": {
    "characters": [
      {
        "id": "char_main",
        "name_cn": "橘猫",
        "description_en": "a chubby orange tabby cat, anime style, consistent appearance"
      }
    ],
    "scenes": [
      {
        "id": "scene_tokyo",
        "name_cn": "东京街头",
        "description_en": "Tokyo street at dusk, neon signs, anime background"
      }
    ],
    "props": [
      {
        "id": "prop_umbrella",
        "name_cn": "雨伞",
        "description_en": "transparent umbrella with raindrops"
      }
    ]
  },
  "shots": [
    {
      "index": 1,
      "character_ids": ["char_main"],
      "scene_id": "scene_tokyo",
      "prop_ids": [],
      "scene_cn": "橘猫走在东京街头",
      "image_prompt_en": "... must include char_main stable appearance ...",
      "motion_prompt_en": "...",
      "narration_cn": "...",
      "duration": 4
    }
  ]
}
```

**Prompt 约束（script_service）**：

- 必须从创意提取 1 个主角色、1 个主场景；道具可选（0–2 个）
- 每个 `character.description_en` 为跨镜稳定外观锚点
- 每镜 `character_ids/scene_id/prop_ids` 必须引用已声明 asset id
- 保留 M2 已有主体保留、风格优先级等约束

## 4. 数据模型

### 新表 `assets`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String(36) PK | UUID |
| project_id | FK projects | |
| asset_type | String(16) | `character` / `scene` / `prop` |
| asset_key | String(64) | 脚本内 id，如 `char_main` |
| name_cn | String(128) | |
| description_en | Text | |
| image_url | Text nullable | 设定图 URL |
| status | String(16) | pending/completed/failed |

### `shots` 扩展

| 字段 | 类型 | 说明 |
|------|------|------|
| character_ids | Text | JSON 数组字符串，如 `["char_main"]` |
| scene_id | String(64) nullable | |
| prop_ids | Text | JSON 数组字符串 |

### 启动迁移 `app/core/migrate.py`

- `init_db()` 后调用 `run_migrations(engine)`
- SQLite：检查 `assets` 表是否存在，不存在则 `CREATE`
- 检查 `shots` 缺失列 → `ALTER TABLE shots ADD COLUMN ...`
- 检查 `projects` 缺失列（若需要）同理
- **幂等**：重复启动不报错
- 单元测试覆盖 migrate 逻辑（mock inspector）

## 5. Provider 扩展

### ImageProvider 新增

```python
async def image_to_image(
    self, prompt: str, reference_urls: list[str], **kwargs
) -> ImageResult: ...
```

### AgnesImageProvider

- 端点仍为 `POST {api_base}/v1/images/generations`
- `extra_body.image = reference_urls`（URL 数组）
- `response_format` 仍放 `extra_body`
- 无参考图时回退 `text_to_image`

### Mock ImageProvider

- 同步实现 `image_to_image`，返回可区分 mock URL

## 6. 服务层

### AssetService（新）

- `generate_assets(project_id, assets_meta, aspect_ratio, on_done)` 
- 逐资产文生图（小并发 ≤2）
- 写入 `assets` 表，回调更新 asseting 进度

### ImageService 改造

- `generate_keyframes(shots, assets_map, style, aspect_ratio, on_shot_done)`
- 每镜收集引用资产 URL → `image_to_image`
- Prompt = `shot.image_prompt_en` + 关联资产 `description_en` 摘要

### FFmpegService 扩展

**extract_last_frame(video_path, output_image_path) -> Path**

```bash
ffmpeg -sseof -0.1 -i input.mp4 -frames:v 1 -q:v 2 output.jpg
```

**concat_clips_xfade(clip_paths, output_path, xfade_duration=0.4) -> Path**

- 用 `xfade` 滤镜链拼接（非 concat demuxer）
- 需计算每段 offset（前段时长 - xfade_duration 累加）
- mock 测试断言 filter_complex 含 `xfade`

**build_continuous_audio(audio_paths, output_path) -> Path**

- `ffmpeg -i 1.mp3 -i 2.mp3 ... -filter_complex concat=n=N:v=0:a=1`

**compose_final_with_continuous_audio(video_path, continuous_audio, srt_entries, output_path)**

- 成片铺一条连续旁白轨；字幕按累计时间轴烧录（多段 SRT 或 ASS）
- 若实现复杂，M3 可简化为：单镜仍烧字幕，成片只混连续旁白（不重复烧字幕）

### generation_service 改造

**coherent_mode=true（默认）**：

1. 脚本 → 保存 shots + assets meta
2. asseting → AssetService
3. imaging → ImageService.generate_keyframes
4. videoing **串行 for 循环**（不用 gather 并发视频）：
   - shot[0]：input = keyframe image_url
   - shot[i>0]：download prev raw_video → extract_last_frame → 本地 jpg 路径或上传后 URL 给 video API
   - 每镜内：`gather(video_task, tts_task)` 仍可并行
5. synthesizing：
   - 每镜 compose_shot_clip（视频+该镜 mp3+字幕，时长对齐逻辑同 M2）
   - build_continuous_audio → concat_clips_xfade → 可选 final mux 连续旁白

**coherent_mode=false**：保持现有 M2 逻辑不变（便于 A/B 对比）

## 7. 配置项（config.py + .env.example）

```env
COHERENT_MODE=true
XFADE_DURATION=0.4
```

## 8. API 与 Schema

### AssetResponse

```python
class AssetResponse(BaseModel):
    id: str
    asset_type: str
    asset_key: str
    name_cn: str
    description_en: str
    image_url: str | None
    status: str
```

### ProjectResponse 增加

```python
assets: list[AssetResponse] = []
```

### project_service

- `save_script` 扩展：解析 assets + shot 引用字段
- `save_asset_image(project_id, asset_key, url)`
- `update_asseting_progress(project_id, completed, total)`
- `to_response` 附带 assets 列表

## 9. 前端

### `client.ts`

- `AssetResponse` 类型
- `ProjectResponse.assets`

### `ProgressPage.tsx`

- STATUS_LABEL 增加 `asseting: '资产生成中'`
- **导演设定**区块：`project.assets` 网格展示（角色/场景/道具标签 + 设定图）
- asseting 阶段提示：`资产 2/5`
- imaging 阶段可展示已有关键帧缩略图（shots.image_url）

样式：复用 `.shot-grid`，新增 `.asset-grid` / `.asset-card` / `.asset-type-badge`

## 10. 测试方案（mock，CI 不依赖网络/ffmpeg）

| 层级 | 用例 |
|------|------|
| 单元 | 脚本 JSON 含 assets 解析；migrate 补列；Agnes img2img 请求体；尾帧提取命令；xfade offset 计算；连续音轨 concat 命令 |
| 集成 | coherent 全链路 pending→completed（mock Provider + mock subprocess） |
| 集成 | coherent_mode=false 仍走 M2 路径 |
| API | GET project 含 assets、status=asseting |
| e2e | 真实 Key + ffmpeg，`@pytest.mark.e2e`，CI 跳过 |

**质量门槛**：非 e2e 全程 mock；日志不泄露 Key；`@author zhangzhihao` + 中文注释；`pytest` 全绿。

## 11. 不改动 CI

FFmpeg / Agnes 相关测试 mock subprocess，**不修改 `.github/workflows/`**。

## 12. 不在 M3 范围

- Celery / Redis 队列
- 多租户 / 鉴权 / 计费
- 付费 SOTA 视频 Provider（可灵/Seedance）
- BGM
- Agnes keyframes 模式（已选尾帧链式为主方案）

## 13. 文件清单（Composer 实现参考）

| 文件 | 动作 |
|------|------|
| `docs/m3-design.md` | 本文档 |
| `backend/app/core/migrate.py` | 新增 |
| `backend/app/core/database.py` | init_db 调用 migrate |
| `backend/app/core/config.py` | coherent_mode, xfade_duration |
| `backend/app/models/asset.py` | 新增 Asset ORM |
| `backend/app/models/project.py` | Shot 扩展字段 |
| `backend/app/providers/base.py` | ImageProvider.image_to_image |
| `backend/app/providers/image/agnes.py` | 实现 img2img |
| `backend/app/providers/image/mock.py` | 实现 img2img |
| `backend/app/services/asset_service.py` | 新增 |
| `backend/app/services/script_service.py` | assets JSON + ShotData 扩展 |
| `backend/app/services/image_service.py` | generate_keyframes |
| `backend/app/services/ffmpeg_service.py` | extract/xfade/continuous audio |
| `backend/app/services/generation_service.py` | M3 编排 |
| `backend/app/services/project_service.py` | assets CRUD + 进度 |
| `backend/app/schemas/project.py` | AssetResponse |
| `backend/tests/*` | 覆盖上述 |
| `frontend/src/api/client.ts` | Asset 类型 |
| `frontend/src/pages/ProgressPage.tsx` | 导演设定 UI |
| `backend/.env.example` | 新配置项 |
| `CHANGELOG.md` | Unreleased 记录 M3 |
