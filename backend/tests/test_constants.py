# @author zhangzhihao
"""常量映射单元测试。"""

from app.core.constants import (
    ASPECT_TO_SIZE,
    STYLE_TO_PROMPT,
    aspect_to_size,
    aspect_to_video_size,
    duration_to_shot_count,
    style_to_prompt,
)


def test_aspect_to_size_mapping():
    assert ASPECT_TO_SIZE["9:16"] == "768x1344"
    assert ASPECT_TO_SIZE["16:9"] == "1344x768"
    assert ASPECT_TO_SIZE["1:1"] == "1024x1024"
    assert aspect_to_size("9:16") == "768x1344"
    assert aspect_to_size("unknown") == "768x1344"
    assert aspect_to_video_size("9:16") == (768, 1344)
    assert aspect_to_video_size("16:9") == (1344, 768)
    assert aspect_to_video_size("1:1") == (1024, 1024)
    assert aspect_to_video_size("unknown") == (768, 1344)


def test_style_to_prompt_mapping():
    assert "cinematic" in STYLE_TO_PROMPT["cinematic"]
    assert "anime" in STYLE_TO_PROMPT["anime"]
    assert style_to_prompt("documentary") == STYLE_TO_PROMPT["documentary"]
    assert style_to_prompt("unknown") == STYLE_TO_PROMPT["cinematic"]


def test_duration_to_shot_count():
    assert duration_to_shot_count(15) == 4
    assert duration_to_shot_count(30) == 6
    assert duration_to_shot_count(60) == 6
    assert duration_to_shot_count(120) == 6
    assert duration_to_shot_count(5) == 1


def test_duration_to_num_frames():
    from app.core.constants import duration_to_num_frames

    assert duration_to_num_frames(5) == 121
    assert duration_to_num_frames(3) == 81
