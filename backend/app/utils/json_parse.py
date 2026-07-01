# @author zhangzhihao
"""LLM 输出 JSON 容错解析。"""

import json
import re

_PREVIEW_LEN = 500

# 剥离思考/推理标签（含多行）
_THINKING_TAG_PATTERN = re.compile(
    r"<(?:redacted_)?thinking>[\s\S]*?</(?:redacted_)?thinking>",
    re.IGNORECASE,
)

# markdown 代码块
_CODE_FENCE_PATTERN = re.compile(
    r"```(?:json)?\s*([\s\S]*?)\s*```",
    re.IGNORECASE,
)

# 对象/数组内尾随逗号
_TRAILING_COMMA_PATTERN = re.compile(r",\s*([}\]])")

# 中文弯引号等 → 不破坏 JSON 字符串的替代
_SMART_QUOTE_MAP = str.maketrans({
    "\u201c": "「",
    "\u201d": "」",
    "\u2018": "'",
    "\u2019": "'",
})


def _preview(text: str) -> str:
    return text[:_PREVIEW_LEN]


def _strip_thinking_tags(text: str) -> str:
    return _THINKING_TAG_PATTERN.sub("", text).strip()


def _normalize_llm_json_text(text: str) -> str:
    return text.translate(_SMART_QUOTE_MAP)


def _remove_trailing_commas(json_str: str) -> str:
    return _TRAILING_COMMA_PATTERN.sub(r"\1", json_str)


def _try_close_truncated_json(json_str: str) -> str:
    """尝试闭合被截断的 JSON（补引号与括号）。"""
    in_string = False
    escape = False
    stack: list[str] = []
    for ch in json_str:
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            stack.append("}")
        elif ch == "[":
            stack.append("]")
        elif ch in "}]" and stack and stack[-1] == ch:
            stack.pop()
    result = json_str.rstrip()
    if in_string:
        result += '"'
    result += "".join(reversed(stack))
    return result


def _salvage_outline_objects(text: str) -> list[dict] | None:
    """从损坏文本中提取完整的 outline 条目。"""
    match = re.search(r'"outline"\s*:\s*\[', text)
    if not match:
        return None
    start = match.end()
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
        i += 1
    array_body = text[start : i - 1] if depth == 0 else text[start:]

    items: list[dict] = []
    obj_start = None
    brace = 0
    in_str = False
    esc = False
    for idx, ch in enumerate(array_body):
        if esc:
            esc = False
            continue
        if ch == "\\":
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == "{":
            if brace == 0:
                obj_start = idx
            brace += 1
        elif ch == "}":
            brace -= 1
            if brace == 0 and obj_start is not None:
                chunk = array_body[obj_start : idx + 1]
                try:
                    obj = json.loads(_remove_trailing_commas(chunk))
                    if isinstance(obj, dict) and obj.get("index") is not None:
                        items.append(obj)
                except json.JSONDecodeError:
                    pass
                obj_start = None
    return items if items else None


def _extract_json_candidate(text: str) -> str | None:
    """优先从代码块提取 JSON，否则回退到首尾 {} 或 [] 截取。"""
    fence_match = _CODE_FENCE_PATTERN.search(text)
    if fence_match:
        return fence_match.group(1).strip()

    pairs = (("[", "]"), ("{", "}"))
    first_array = text.find("[")
    first_object = text.find("{")
    if first_array != -1 and (first_object == -1 or first_array < first_object):
        ordered = (pairs[0], pairs[1])
    else:
        ordered = (pairs[1], pairs[0])

    for open_ch, close_ch in ordered:
        start = text.find(open_ch)
        end = text.rfind(close_ch)
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1]
    return None


def parse_json_value_from_llm(text: str):
    """从 LLM 原始文本中提取并解析 JSON 对象或数组。"""
    cleaned = _normalize_llm_json_text(_strip_thinking_tags(text.strip()))
    candidate = _extract_json_candidate(cleaned)

    if candidate is None:
        raise ValueError(f"未找到有效的 JSON。原始文本片段: {_preview(text)}")

    json_str = _remove_trailing_commas(candidate)
    attempts = [json_str, _try_close_truncated_json(json_str)]
    last_exc: json.JSONDecodeError | None = None
    for attempt in attempts:
        try:
            return json.loads(attempt)
        except json.JSONDecodeError as exc:
            last_exc = exc

    salvaged = _salvage_outline_objects(json_str)
    if salvaged is not None:
        return {"outline": salvaged}

    raise ValueError(
        f"JSON 解析失败: {last_exc}。原始文本片段: {_preview(text)}"
    ) from last_exc


def parse_json_from_llm(text: str) -> dict:
    """从 LLM 原始文本中提取并解析 JSON 对象。"""
    value = parse_json_value_from_llm(text)
    if isinstance(value, dict):
        return value
    raise ValueError(
        f"期望 JSON 对象，实际为 {type(value).__name__}。"
        f"原始文本片段: {_preview(text)}"
    )
