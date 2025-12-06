from datetime import UTC, datetime
from numbers import Rational
from typing import TYPE_CHECKING

from jinja2 import pass_context
from jinja2.runtime import Context

if TYPE_CHECKING:
    from .models import Album, Photo

__all__ = [
    "exposure",
    "fnumber",
    "album_url",
    "photo_url",
    "asset_url",
    "isodate",
]


def exposure(raw: float | Rational | None) -> str | None:
    if raw is not None:
        if isinstance(raw, float):
            if 0 < raw < 0.25001:
                return f"1/{int(0.5 + 1/raw)}"
            return f"{raw:.1f}"

        if 0 < float(raw) < 1:
            return f"{raw.numerator:d}/{raw.denominator:d}"
        elif raw.denominator == 1:
            return f"{raw.numerator:d}"
        return f"{raw:.1f}"
    return None


def fnumber(raw: float | Rational | None) -> str | None:
    if raw is not None:
        if isinstance(raw, Rational):
            raw = float(raw)

        if 0 < raw < 1:
            return f"{raw:.2f}"
        return f"{raw:.1f}"
    return None


def album_url(item: Album) -> str:
    return f"/album/{item.id}"

@pass_context
def photo_url(ctx: Context, idx: int) -> str:
    album = ctx.get("album")
    return f"/album/{album.id}/{idx}/"


def asset_url(photo: Photo, variant: str | None = None) -> str:
    sfx = "png"
    if variant is not None:
        sfx = variant + "." + sfx
    return f"/photo/{photo.id}.{sfx}"


def isodate(d: datetime) -> str:
    if d.tzinfo is None:
        d = d.replace(tzinfo=UTC)
    return d.isoformat()
