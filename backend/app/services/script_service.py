# @author zhangzhihao
"""分镜脚本生成服务。"""

import logging
from dataclasses import dataclass, field

from app.core.constants import duration_to_shot_count, style_to_prompt
from app.providers.base import LLMProvider, Message
from app.providers.registry import get_llm_provider
from app.utils.json_parse import parse_json_from_llm

logger = logging.getLogger(__name__)

_RETRY_HINT = (
    "上次输出不是合法 JSON，请只输出严格合法的 JSON 对象，"
    "不要包含任何解释、思考或代码块标记"
)


@dataclass
class CharacterAssetData:
    id: str
    name_cn: str
    description_en: str


@dataclass
class SceneAssetData:
    id: str
    name_cn: str
    description_en: str


@dataclass
class PropAssetData:
    id: str
    name_cn: str
    description_en: str


@dataclass
class AssetsData:
    characters: list[CharacterAssetData] = field(default_factory=list)
    scenes: list[SceneAssetData] = field(default_factory=list)
    props: list[PropAssetData] = field(default_factory=list)


@dataclass
class ShotData:
    index: int
    scene_cn: str
    image_prompt_en: str
    motion_prompt_en: str
    narration_cn: str
    duration: int
    character_ids: list[str] = field(default_factory=list)
    scene_id: str | None = None
    prop_ids: list[str] = field(default_factory=list)


@dataclass
class ScriptResult:
    title: str
    shots: list[ShotData]
    assets: AssetsData = field(default_factory=AssetsData)


def _build_script_prompt(story: str, style: str, duration: int, shot_count: int) -> str:
    style_hint = style_to_prompt(style)
    return f"""你是一位专业短视频导演。请根据以下创意，生成结构化分镜脚本。

创意：{story}
视觉风格参数：{style}（英文提示词参考：{style_hint}，仅当创意未明确风格时使用）
目标时长：约 {duration} 秒
镜头数量：{shot_count} 个（每镜约 4 秒）

请严格输出 JSON，不要输出其他文字。格式如下：
{{
  "title": "短片标题",
  "assets": {{
    "characters": [
      {{
        "id": "char_main",
        "name_cn": "主角色中文名",
        "description_en": "a chubby orange tabby cat, anime style, consistent appearance"
      }}
    ],
    "scenes": [
      {{
        "id": "scene_main",
        "name_cn": "主场景中文名",
        "description_en": "Tokyo street at dusk, neon signs, anime background"
      }}
    ],
    "props": [
      {{
        "id": "prop_umbrella",
        "name_cn": "道具中文名",
        "description_en": "transparent umbrella with raindrops"
      }}
    ]
  }},
  "shots": [
    {{
      "index": 1,
      "character_ids": ["char_main"],
      "scene_id": "scene_main",
      "prop_ids": [],
      "scene_cn": "中文画面描述",
      "image_prompt_en": "english image prompt with style/lighting/composition",
      "motion_prompt_en": "english motion prompt: camera movement, subject action",
      "narration_cn": "该镜头旁白文案",
      "duration": 4
    }}
  ]
}}

要求：
- shots 数组长度必须为 {shot_count}
- image_prompt_en 使用英文，包含画面构图、光线、氛围
- motion_prompt_en 使用英文，描述镜头运动（如 slow pan、tracking shot）、
  主体动作与镜头语言，保持主体与 image_prompt_en 一致
- scene_cn 和 narration_cn 使用中文
- index 从 1 开始连续编号

【资产清单 — M3 导演设定】
- 必须从创意提取 1 个主角色（characters）、1 个主场景（scenes）；道具可选 0–2 个（props）
- 每个 character.description_en 为跨镜稳定外观锚点，含物种、外观、风格
- 每镜 character_ids / scene_id / prop_ids 必须引用 assets 中已声明的 id
- 每个 image_prompt_en 必须包含关联角色的稳定外观描述

【核心约束 — 必须严格遵守】
1. 主体保留：必须严格保留创意中的核心主体、角色、物种、数量与风格，禁止替换。
   - 禁止把动物拟人化或替换成人类（例：创意是「橘猫」，所有镜头主体必须是同一只橘猫，不能变成人）
   - 禁止遗漏、替换或偷换创意中的关键主体
2. 主体一致性锚点：先根据创意确定贯穿全片的「核心主体稳定描述」
   （含物种、外观、关键特征）和「统一视觉风格」。
   - 每个镜头的 image_prompt_en 都必须包含该核心主体的稳定外观描述，
     确保跨镜头主角一致、不漂移
3. 风格写入：每个 image_prompt_en 必须把视觉风格明确写入英文提示词
   （如 anime style、cinematic 等），且必须与创意文字中的风格一致
4. 风格优先级：创意中明确表达的风格（如「动漫版」「anime」「写实」等）为最高优先；
   仅当创意未提及风格时，才参考上述视觉风格参数
"""


def _parse_assets(data: dict) -> AssetsData:
    """从 LLM JSON 解析资产清单。"""
    raw = data.get("assets") or {}
    characters = [
        CharacterAssetData(
            id=item.get("id", f"char_{i}"),
            name_cn=item.get("name_cn", ""),
            description_en=item.get("description_en", ""),
        )
        for i, item in enumerate(raw.get("characters") or [])
    ]
    scenes = [
        SceneAssetData(
            id=item.get("id", f"scene_{i}"),
            name_cn=item.get("name_cn", ""),
            description_en=item.get("description_en", ""),
        )
        for i, item in enumerate(raw.get("scenes") or [])
    ]
    props = [
        PropAssetData(
            id=item.get("id", f"prop_{i}"),
            name_cn=item.get("name_cn", ""),
            description_en=item.get("description_en", ""),
        )
        for i, item in enumerate(raw.get("props") or [])
    ]
    return AssetsData(characters=characters, scenes=scenes, props=props)


class ScriptService:
    """调用 LLM 生成结构化分镜脚本。"""

    def __init__(self, llm: LLMProvider | None = None) -> None:
        self._llm = llm or get_llm_provider()

    async def _request_script(self, messages: list[Message]) -> str:
        return await self._llm.chat(
            messages,
            temperature=0.7,
            max_tokens=8192,
        )

    async def generate_script(
        self, story: str, style: str, duration: int
    ) -> ScriptResult:
        shot_count = duration_to_shot_count(duration)
        prompt = _build_script_prompt(story, style, duration, shot_count)

        messages = [
            Message(role="system", content="你是专业短视频分镜编剧，只输出合法 JSON。"),
            Message(role="user", content=prompt),
        ]

        raw = await self._request_script(messages)
        try:
            data = parse_json_from_llm(raw)
        except ValueError as first_exc:
            logger.warning("分镜 JSON 首次解析失败，将重试: %s", first_exc)
            messages.append(Message(role="assistant", content=raw))
            messages.append(Message(role="user", content=_RETRY_HINT))
            raw = await self._request_script(messages)
            try:
                data = parse_json_from_llm(raw)
            except ValueError as retry_exc:
                logger.error("分镜 JSON 解析失败，原始输出片段: %s", raw[:500])
                raise retry_exc

        title = data.get("title", "未命名短片")
        shots_raw = data.get("shots", [])
        assets = _parse_assets(data)

        # 无资产时回退默认主角色/主场景，保证 M3 链路可跑
        if not assets.characters:
            assets.characters.append(
                CharacterAssetData(
                    id="char_main",
                    name_cn="主角",
                    description_en="main character, consistent appearance across shots",
                )
            )
        if not assets.scenes:
            assets.scenes.append(
                SceneAssetData(
                    id="scene_main",
                    name_cn="主场景",
                    description_en="main scene background, consistent setting",
                )
            )

        default_char = assets.characters[0].id
        default_scene = assets.scenes[0].id

        shots: list[ShotData] = []
        for i, item in enumerate(shots_raw[:shot_count]):
            char_ids = item.get("character_ids") or [default_char]
            scene_id = item.get("scene_id") or default_scene
            prop_ids = item.get("prop_ids") or []
            shots.append(
                ShotData(
                    index=item.get("index", i + 1),
                    scene_cn=item.get("scene_cn", ""),
                    image_prompt_en=item.get("image_prompt_en", ""),
                    motion_prompt_en=item.get("motion_prompt_en", ""),
                    narration_cn=item.get("narration_cn", ""),
                    duration=item.get("duration", 4),
                    character_ids=char_ids,
                    scene_id=scene_id,
                    prop_ids=prop_ids,
                )
            )

        return ScriptResult(title=title, shots=shots, assets=assets)
