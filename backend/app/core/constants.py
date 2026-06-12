# @author zhangzhihao
"""M1 业务常量：版式、风格、时长映射。"""

from typing import Final

# 版式 → Agnes 图像 size
ASPECT_TO_SIZE: Final[dict[str, str]] = {
    "9:16": "768x1344",
    "16:9": "1344x768",
    "1:1": "1024x1024",
}

# 风格 → 英文提示词片段
STYLE_TO_PROMPT: Final[dict[str, str]] = {
    "cinematic": "cinematic realism, film still, dramatic lighting",
    "anime": "anime style, vibrant colors, clean lineart",
    "documentary": "documentary photography, natural lighting, realistic",
    "vlog": "casual vlog style, bright, candid",
}

# M2 单项目镜头数上限
MAX_SHOTS: Final[int] = 6

# 每镜头约 4 秒
SECONDS_PER_SHOT: Final[int] = 4

# Agnes 视频合法帧数（须满足 8n+1 且 ≤441）
VALID_VIDEO_FRAME_COUNTS: Final[list[int]] = [81, 121, 161, 241, 441]


def duration_to_shot_count(duration: int) -> int:
    """目标时长（秒）→ 镜头数，上限 MAX_SHOTS。"""
    count = max(1, round(duration / SECONDS_PER_SHOT))
    return min(count, MAX_SHOTS)


def aspect_to_size(aspect_ratio: str) -> str:
    """版式转图像尺寸，未知版式回退竖屏。"""
    return ASPECT_TO_SIZE.get(aspect_ratio, ASPECT_TO_SIZE["9:16"])


def style_to_prompt(style: str) -> str:
    """风格转英文提示词片段，未知风格回退电影感。"""
    return STYLE_TO_PROMPT.get(style, STYLE_TO_PROMPT["cinematic"])


def duration_to_num_frames(
    seconds: int,
    frame_rate: int = 24,
    max_frames: int = 441,
) -> int:
    """时长（秒）→ 最接近的合法 num_frames（8n+1，上限 max_frames）。"""
    target = max(1, seconds) * frame_rate
    candidates = [f for f in VALID_VIDEO_FRAME_COUNTS if f <= max_frames]
    if not candidates:
        return VALID_VIDEO_FRAME_COUNTS[0]
    return min(candidates, key=lambda f: abs(f - target))
