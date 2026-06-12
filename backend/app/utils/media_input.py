# @author zhangzhihao
"""媒资输入解析：本地 outputs 路径 → Agnes 可接受的 image 参数。"""

import base64
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_MIME_BY_SUFFIX = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def resolve_local_image_path(image_ref: str, outputs_dir: str) -> Path | None:
    """将 /outputs/... 或 file:// 引用解析为本地文件路径。"""
    ref = image_ref.strip()
    if ref.startswith("/outputs/"):
        rel = ref.removeprefix("/outputs/").lstrip("/")
        return Path(outputs_dir) / rel
    if ref.startswith("file://"):
        return Path(ref.removeprefix("file://"))
    return None


def path_to_data_uri(path: Path) -> str:
    """本地图片文件 → Data URI Base64（Agnes 图像 API 兼容格式）。"""
    suffix = path.suffix.lower()
    mime = _MIME_BY_SUFFIX.get(suffix, "image/jpeg")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def path_to_base64(path: Path) -> str:
    """本地图片文件 → 标准 Base64 字符串（长度必为 4 的倍数）。"""
    return base64.b64encode(path.read_bytes()).decode("ascii")


def normalize_video_image_input(image_ref: str, outputs_dir: str) -> str:
    """
    规范化 Agnes Video 的 image 字段：
    - http(s) URL 原样返回
    - data:image/... 原样返回
    - /outputs/ 或 file:// 本地路径 → Base64（避免把路径字符串误当 base64）
    """
    ref = image_ref.strip()
    if not ref:
        raise ValueError("视频输入图为空")
    if ref.startswith(("http://", "https://", "data:image")):
        return ref

    local_path = resolve_local_image_path(ref, outputs_dir)
    if local_path is None or not local_path.is_file():
        raise ValueError(f"无法解析本地视频输入图: {image_ref}")

    logger.info("视频输入图由本地路径转为 Base64: %s", local_path)
    return path_to_base64(local_path)
