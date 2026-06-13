# @author zhangzhihao
"""小说题材模板与 system prompt。"""

PLAN_MARKER = "【小说规划任务】"
WRITE_MARKER = "【章节写作任务】"
SUMMARY_MARKER = "【章节摘要任务】"
CHAT_MARKER = "【改稿对话任务】"

GENRE_TEMPLATES: dict[str, dict[str, str]] = {
    "xuanhuan": {
        "label": "玄幻",
        "hint": "修炼体系清晰、升级节奏合理、金手指设定自洽，注重境界突破与机缘奇遇。",
    },
    "dushi": {
        "label": "都市",
        "hint": "现实都市背景，情感或职场冲突驱动，人物关系贴近生活但有戏剧张力。",
    },
    "xuanyi": {
        "label": "悬疑",
        "hint": "线索铺设缜密、节奏紧凑、反转合理，保持读者悬念直到揭晓。",
    },
    "tianai": {
        "label": "甜宠",
        "hint": "人物关系甜蜜互动为主，轻冲突高糖节奏，注重情感细节与心动瞬间。",
    },
    "kehuan": {
        "label": "科幻",
        "hint": "未来设定自洽、科技感与未来感并存，核心矛盾围绕技术与人性展开。",
    },
}

VALID_GENRES = frozenset(GENRE_TEMPLATES.keys())


def genre_label(genre: str) -> str:
    """返回题材中文标签。"""
    return GENRE_TEMPLATES.get(genre, {}).get("label", genre)


def build_plan_system_prompt(genre: str) -> str:
    """规划阶段 system prompt。"""
    tpl = GENRE_TEMPLATES.get(genre, GENRE_TEMPLATES["xuanhuan"])
    return (
        f"{PLAN_MARKER}\n"
        "你是一位资深网文策划编辑。根据用户创意输出严格 JSON，不要 markdown 包裹。\n"
        f"题材：{tpl['label']}。写作要点：{tpl['hint']}\n"
        "JSON 字段：title, synopsis, world, characters[{name,role,profile}], "
        "outline[{index,title,summary}]。outline 至少 8 章，index 从 1 递增。"
    )


def build_write_system_prompt(genre: str, word_min: int, word_max: int) -> str:
    """章节写作 system prompt。"""
    tpl = GENRE_TEMPLATES.get(genre, GENRE_TEMPLATES["xuanhuan"])
    return (
        f"{WRITE_MARKER}\n"
        f"你是一位{tpl['label']}小说作家。根据大纲与设定撰写单章正文。\n"
        f"写作要点：{tpl['hint']}\n"
        f"目标篇幅 {word_min}–{word_max} 字（中文），只输出正文，不要标题与说明。\n"
        "禁止开启思考模式，直接输出故事正文。"
    )


def build_summary_system_prompt() -> str:
    """章节摘要 system prompt。"""
    return (
        f"{SUMMARY_MARKER}\n"
        "为刚完成的章节写 200–400 字摘要，涵盖关键情节与人物变化，只输出摘要文本。"
    )


def build_chat_system_prompt() -> str:
    """改稿对话 system prompt。"""
    return (
        f"{CHAT_MARKER}\n"
        "你是小说编辑助手。根据用户改稿意见，输出 JSON：\n"
        '{"reply":"给作者的回复","updates":{"world":"可选","characters":[...],'
        '"outline":[...],"facts":["可选新增事实"]}}\n'
        "updates 中只包含需要修改的字段；不自动重写已发布章节正文。"
    )
