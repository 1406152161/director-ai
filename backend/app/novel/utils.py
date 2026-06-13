# @author zhangzhihao
"""小说字数统计等工具。"""

import re


def count_chinese_words(text: str) -> int:
    """中文篇幅按非空白字符数近似。"""
    return len(re.sub(r"\s+", "", text))
