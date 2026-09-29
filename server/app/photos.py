"""房源照片处理：压缩转 WebP + 缩略图，落盘本地 UPLOAD_DIR。

photos 数组约定：photos[0] = 封面缩略图（列表卡片用），photos[1:] = 原图（详情轮播，
其中 photos[1] 即封面原图）。
"""
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image, ImageOps

from app.config import UPLOAD_DIR

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_PHOTOS = 9
LONG_EDGE = 1600
THUMB_EDGE = 480
TARGET_SIZE = 500 * 1024  # 原图目标体积


def _save_webp(img: Image.Image, path: Path, long_edge: int, target: int | None = None) -> None:
    img = img.copy()
    img.thumbnail((long_edge, long_edge))
    quality = 80
    while True:
        buf = BytesIO()
        img.save(buf, "WEBP", quality=quality)
        if target is None or buf.tell() <= target or quality <= 40:
            break
        quality -= 20
    path.write_bytes(buf.getvalue())


def _url(path: Path) -> str:
    return "/" + path.as_posix()


def process_photos(files: list[UploadFile]) -> list[str]:
    if not 1 <= len(files) <= MAX_PHOTOS:
        raise HTTPException(400, f"照片数量需 1-{MAX_PHOTOS} 张")

    dir_path = Path(UPLOAD_DIR) / f"{datetime.now():%Y/%m}"
    dir_path.mkdir(parents=True, exist_ok=True)

    originals: list[Path] = []
    for f in files:
        if f.content_type not in ALLOWED_TYPES:
            raise HTTPException(400, f"不支持的图片格式: {f.content_type}")
        data = f.file.read(MAX_FILE_SIZE + 1)
        if len(data) > MAX_FILE_SIZE:
            raise HTTPException(400, "单张图片不能超过 10MB")
        try:
            img = ImageOps.exif_transpose(Image.open(BytesIO(data)))
        except Exception:
            raise HTTPException(400, "图片文件无法解析")
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        path = dir_path / f"{uuid.uuid4().hex}.webp"
        _save_webp(img, path, LONG_EDGE, TARGET_SIZE)
        originals.append(path)

    thumb = originals[0].with_name(f"{originals[0].stem}_thumb.webp")
    _save_webp(Image.open(originals[0]), thumb, THUMB_EDGE)

    return [_url(thumb)] + [_url(p) for p in originals]
