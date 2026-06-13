# @author zhangzhihao
"""Agnes 视频轮询响应解析。"""


def extract_completed_video_url(data: dict, api_base: str) -> str:
    """
    从 completed 轮询结果提取可下载的 http(s) URL。
    字段优先级：remixed_from_video_id → video_url → url
    """
    base = api_base.rstrip("/")
    for key in ("remixed_from_video_id", "video_url", "url"):
        raw = data.get(key)
        if not raw:
            continue
        value = str(raw).strip()
        if value.startswith(("http://", "https://")):
            return value
        if value.startswith("/"):
            return f"{base}{value}"
    raise ValueError(f"completed 响应中缺少可下载视频 URL: {data}")
