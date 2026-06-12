# @author zhangzhihao
"""分镜脚本生成服务。"""

from dataclasses import dataclass

from app.core.constants import duration_to_shot_count, style_to_prompt
from app.providers.base import LLMProvider, Message
from app.providers.registry import get_llm_provider
from app.utils.json_parse import parse_json_from_llm


@dataclass
class ShotData:
    index: int
    scene_cn: str
    image_prompt_en: str
    narration_cn: str
    duration: int


@dataclass
class ScriptResult:
    title: str
    shots: list[ShotData]


def _build_script_prompt(story: str, style: str, duration: int, shot_count: int) -> str:
    style_hint = style_to_prompt(style)
    return f"""你是一位专业短视频导演。请根据以下创意，生成结构化分镜脚本。

创意：{story}
视觉风格：{style}（英文提示词参考：{style_hint}）
目标时长：约 {duration} 秒
镜头数量：{shot_count} 个（每镜约 4 秒）

请严格输出 JSON，不要输出其他文字。格式如下：
{{
  "title": "短片标题",
  "shots": [
    {{
      "index": 1,
      "scene_cn": "中文画面描述",
      "image_prompt_en": "english image prompt with style/lighting/composition",
      "narration_cn": "该镜头旁白文案",
      "duration": 4
    }}
  ]
}}

要求：
- shots 数组长度必须为 {shot_count}
- image_prompt_en 使用英文，包含画面构图、光线、氛围
- scene_cn 和 narration_cn 使用中文
- index 从 1 开始连续编号
"""


class ScriptService:
    """调用 LLM 生成结构化分镜脚本。"""

    def __init__(self, llm: LLMProvider | None = None) -> None:
        self._llm = llm or get_llm_provider()

    async def generate_script(
        self, story: str, style: str, duration: int
    ) -> ScriptResult:
        shot_count = duration_to_shot_count(duration)
        prompt = _build_script_prompt(story, style, duration, shot_count)

        messages = [
            Message(role="system", content="你是专业短视频分镜编剧，只输出合法 JSON。"),
            Message(role="user", content=prompt),
        ]

        raw = await self._llm.chat(
            messages,
            enable_thinking=True,
            temperature=0.7,
            max_tokens=4096,
        )

        data = parse_json_from_llm(raw)
        title = data.get("title", "未命名短片")
        shots_raw = data.get("shots", [])

        shots: list[ShotData] = []
        for i, item in enumerate(shots_raw[:shot_count]):
            shots.append(
                ShotData(
                    index=item.get("index", i + 1),
                    scene_cn=item.get("scene_cn", ""),
                    image_prompt_en=item.get("image_prompt_en", ""),
                    narration_cn=item.get("narration_cn", ""),
                    duration=item.get("duration", 4),
                )
            )

        return ScriptResult(title=title, shots=shots)
