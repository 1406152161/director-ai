# @author zhangzhihao
"""LLM 输出 JSON 容错解析。"""

import json
import re


def parse_json_from_llm(text: str) -> dict:
    """从 LLM 原始文本中提取并解析 JSON 对象。

    支持去除 markdown ```json 代码块包裹与首尾噪声。
    """
    cleaned = text.strip()

    # 剥离 ```json ... ``` 或 ``` ... ``` 包裹
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    # 截取首个 { 到最后一个 } 之间的内容
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("未找到有效的 JSON 对象")

    json_str = cleaned[start : end + 1]
    return json.loads(json_str)
