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


def _preview(text: str) -> str:
    return text[:_PREVIEW_LEN]


def _strip_thinking_tags(text: str) -> str:
    return _THINKING_TAG_PATTERN.sub("", text).strip()


def _extract_json_candidate(text: str) -> str | None:
    """优先从代码块提取 JSON，否则回退到首尾花括号截取。"""
    fence_match = _CODE_FENCE_PATTERN.search(text)
    if fence_match:
        return fence_match.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


def _remove_trailing_commas(json_str: str) -> str:
    return _TRAILING_COMMA_PATTERN.sub(r"\1", json_str)


def parse_json_from_llm(text: str) -> dict:
    """从 LLM 原始文本中提取并解析 JSON 对象。

    支持剥离推理标签、markdown 代码块包裹、尾随逗号与首尾噪声。
    """
    cleaned = _strip_thinking_tags(text.strip())
    candidate = _extract_json_candidate(cleaned)

    if candidate is None:
        raise ValueError(f"未找到有效的 JSON 对象。原始文本片段: {_preview(text)}")

    json_str = _remove_trailing_commas(candidate)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"JSON 解析失败: {exc}。原始文本片段: {_preview(text)}"
        ) from exc
