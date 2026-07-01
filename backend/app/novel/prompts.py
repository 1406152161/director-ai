# @author zhangzhihao
"""小说题材模板与 system prompt。"""

PLAN_MARKER = "【小说规划任务】"
PLAN_WORLD_MARKER = "【小说世界观规划】"
PLAN_OUTLINE_MARKER = "【小说章节大纲规划】"
PLAN_OUTLINE_SKELETON_MARKER = "【章节骨架规划】"
PLAN_OUTLINE_DETAIL_MARKER = "【章节详细大纲规划】"
VALIDATE_MARKER = "【章节质量校验】"
BEAT_MARKER = "【场景beat规划】"
WRITE_MARKER = "【章节写作任务】"
SUMMARY_MARKER = "【章节摘要任务】"
CHAT_MARKER = "【改稿对话任务】"
EXTRACT_MARKER = "【章节结构化抽取】"
REPLAN_MARKER = "【小说后续大纲调整】"
ROLLING_SUMMARY_MARKER = "【滚动摘要更新】"

GENRE_TEMPLATES: dict[str, dict[str, str]] = {
    "xuanhuan": {
        "label": "玄幻",
        "hint": "修炼体系清晰、升级节奏合理、金手指设定自洽，注重境界突破与机缘奇遇。",
        "system_hint": "必须输出 power_system（境界/功法/资源体系）。",
    },
    "dushi": {
        "label": "都市",
        "hint": "现实都市背景，情感或职场冲突驱动，人物关系贴近生活但有戏剧张力。",
        "system_hint": "power_system 可描述社会规则/行业规则/家族资源。",
    },
    "xuanyi": {
        "label": "悬疑",
        "hint": "线索铺设缜密、节奏紧凑、反转合理，保持读者悬念直到揭晓。",
        "system_hint": "foreshadowing 需与线索链对应，plant/resolve 章号明确。",
    },
    "tianai": {
        "label": "甜宠",
        "hint": "人物关系甜蜜互动为主，轻冲突高糖节奏，注重情感细节与心动瞬间。",
        "system_hint": "characters 须含 growth_arc（情感成长线）。",
    },
    "kehuan": {
        "label": "科幻",
        "hint": "未来设定自洽、科技感与未来感并存，核心矛盾围绕技术与人性展开。",
        "system_hint": "必须输出 power_system（科技/社会制度/能力规则）。",
    },
}

VALID_GENRES = frozenset(GENRE_TEMPLATES.keys())


def genre_label(genre: str) -> str:
    """返回题材中文标签。"""
    return GENRE_TEMPLATES.get(genre, {}).get("label", genre)


def build_plan_world_system_prompt(genre: str) -> str:
    """Phase A：世界观 / 卷弧 / 人物 / 伏笔。"""
    tpl = GENRE_TEMPLATES.get(genre, GENRE_TEMPLATES["xuanhuan"])
    return (
        f"{PLAN_MARKER}\n{PLAN_WORLD_MARKER}\n"
        "你是一位资深网文策划编辑。根据用户创意输出严格 JSON，不要 markdown 包裹。\n"
        f"题材：{tpl['label']}。写作要点：{tpl['hint']}\n"
        f"{tpl['system_hint']}\n"
        "JSON 字段：title, synopsis, world, power_system, "
        "items[{id,name,description,significance,first_chapter}], "
        "characters[{name,role,profile,growth_arc}], "
        "volumes[{id,title,theme,chapter_from,chapter_to,"
        "arcs[{id,title,conflict,chapter_from,chapter_to}]}], "
        "foreshadowing[{id,content,plant_chapter,resolve_chapter,status,linked_characters,"
        "linked_items,linked_beats}], "
        "meta{total_chapters,chapter_count_reason}。"
        "若用户给出目标章数 T，total_chapters 须在 T±200 内并说明 chapter_count_reason；"
        "无目标时根据故事体量建议合理章数。status 初始为 planned。"
    )


def build_plan_skeleton_system_prompt(genre: str) -> str:
    """L1：全书骨架章纲（无 hook）。"""
    tpl = GENRE_TEMPLATES.get(genre, GENRE_TEMPLATES["xuanhuan"])
    return (
        f"{PLAN_MARKER}\n{PLAN_OUTLINE_SKELETON_MARKER}\n"
        "你是一位资深网文策划编辑。输出严格 JSON，不要 markdown 包裹。\n"
        f"题材：{tpl['label']}。\n"
        "JSON：outline[{index,title,summary,arc_id,volume_id}]，"
        "不要输出 hook；summary 仅 1 句话（≤40 字）；"
        "必须承接锁定前缀与弧段契约，不得引入未登记主线人物/道具。"
    )


def build_plan_detail_system_prompt(genre: str) -> str:
    """L2：近端详细章纲（含 hook）。"""
    tpl = GENRE_TEMPLATES.get(genre, GENRE_TEMPLATES["xuanhuan"])
    return (
        f"{PLAN_MARKER}\n{PLAN_OUTLINE_DETAIL_MARKER}\n"
        "你是一位资深网文策划编辑。在已有骨架上扩写详细章纲，输出严格 JSON。\n"
        f"题材：{tpl['label']}。\n"
        "JSON：outline[{index,title,summary,hook,arc_id,volume_id}]，"
        "summary 可扩至 80 字，hook 必填且承接上一章；"
        "字符串内勿使用未转义英文双引号。"
    )


def build_plan_outline_system_prompt(genre: str) -> str:
    """Phase B：章级大纲。"""
    tpl = GENRE_TEMPLATES.get(genre, GENRE_TEMPLATES["xuanhuan"])
    return (
        f"{PLAN_MARKER}\n{PLAN_OUTLINE_MARKER}\n"
        "你是一位资深网文策划编辑。基于已给世界观与卷弧，输出严格 JSON，不要 markdown 包裹。\n"
        f"题材：{tpl['label']}。\n"
        "JSON 字段：outline[{index,title,summary,hook,arc_id,volume_id}]，"
        "index 从 1 递增，每章须对应 arc_id/volume_id（与 volumes 中 id 一致）。\n"
        "硬性要求：只输出合法 JSON；字符串内勿使用英文双引号，对话用中文「」或单引号；"
        "summary/hook 各控制在 80 字以内，避免超长导致截断。"
    )


def build_validate_system_prompt(genre: str) -> str:
    """写后质量校验 system prompt。"""
    tpl = GENRE_TEMPLATES.get(genre, GENRE_TEMPLATES["xuanhuan"])
    return (
        f"{VALIDATE_MARKER}\n"
        f"你是{tpl['label']}小说责编。对照大纲、beat、伏笔任务审阅章节正文，输出严格 JSON：\n"
        '{"passed":true/false,"score":0-100,"issues":["问题1",...],'
        '"checks":{"beat_coverage":true/false,"foreshadowing":true/false,'
        '"outline_alignment":true/false,"consistency":true/false}}\n'
        f"通过标准：score>={70} 且 beat/伏笔/大纲/一致性无严重问题。不要 markdown 包裹。"
    )


def build_rewrite_system_prompt(genre: str, word_min: int, word_max: int) -> str:
    """校验失败后的重写 system prompt。"""
    tpl = GENRE_TEMPLATES.get(genre, GENRE_TEMPLATES["xuanhuan"])
    return (
        f"{WRITE_MARKER}\n"
        f"你是一位{tpl['label']}小说作家。上一版未通过责编校验，请按问题清单修订后重写整章。\n"
        f"目标篇幅 {word_min}–{word_max} 字（中文），只输出正文。"
    )


def build_beat_system_prompt(genre: str) -> str:
    """单章场景 beat 规划。"""
    tpl = GENRE_TEMPLATES.get(genre, GENRE_TEMPLATES["xuanhuan"])
    return (
        f"{BEAT_MARKER}\n"
        f"你是一位{tpl['label']}小说编剧。为单章规划 3–6 个场景 beat，输出 JSON 数组，"
        "不要 markdown 包裹。每项：{index,scene,goal,conflict,outcome}。"
    )


def build_plan_system_prompt(genre: str) -> str:
    """兼容旧调用：等同 Phase A。"""
    return build_plan_world_system_prompt(genre)


def build_write_system_prompt(genre: str, word_min: int, word_max: int) -> str:
    """章节写作 system prompt。"""
    tpl = GENRE_TEMPLATES.get(genre, GENRE_TEMPLATES["xuanhuan"])
    return (
        f"{WRITE_MARKER}\n"
        f"你是一位{tpl['label']}小说作家。根据大纲、场景 beat 与伏笔要求撰写单章正文。\n"
        f"写作要点：{tpl['hint']}\n"
        f"目标篇幅 {word_min}–{word_max} 字（中文），只输出正文，不要标题与说明。\n"
        "须落实本章应埋设/回收的伏笔；禁止开启思考模式，直接输出故事正文。"
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
        '{"reply":"给作者的回复","updates":{"world":"可选","power_system":"可选",'
        '"characters":[...],"outline":[...],"volumes":[...],"foreshadowing":[...],'
        '"facts":["可选新增事实"]}}\n'
        "updates 中只包含需要修改的字段；不自动重写已发布章节正文。"
    )


def build_extract_system_prompt() -> str:
    return (
        f"{EXTRACT_MARKER}\n"
        "从刚完成章节抽取结构化信息，输出 JSON：\n"
        '{"facts":["新事实"],"entity_updates":[{"entity_key":"char_x","entity_type":"character",'
        '"name":"...","updates":{"location":"","knows":"","traits_delta":""}}],'
        '"foreshadowing_updates":[{"id":"fs1","status":"planted|resolved"}]}\n'
        "只输出 JSON。"
    )


def build_replan_system_prompt(genre: str) -> str:
    tpl = GENRE_TEMPLATES.get(genre, GENRE_TEMPLATES["xuanhuan"])
    return (
        f"{REPLAN_MARKER}\n"
        f"你是{tpl['label']}小说策划。根据已写内容与 Story Bible，调整**未写章节** outline，"
        "已写章节 locked 不可改。输出 JSON："
        '{"outline":[{"index":N,"title":"","summary":"","hook":"","arc_id":"","volume_id":""}],'
        '"foreshadowing":[{"id":"","content":"","plant_chapter":0,"resolve_chapter":0,'
        '"status":"planned|planted","linked_characters":[],"linked_items":[]}]}'
    )


def build_rolling_summary_system_prompt() -> str:
    return (
        f"{ROLLING_SUMMARY_MARKER}\n"
        "根据本章摘要更新滚动摘要，输出 JSON："
        '{"book":"全书500字内","volume":"当前卷800字内","arc":"当前弧1200字内"}'
    )

