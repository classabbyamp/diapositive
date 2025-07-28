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


@pass_context
def album_url(ctx: Context, item: "Album") -> str:
    site = ctx.get("site")

    return f"{site.base_url}/album/{item.id}"

@pass_context
def photo_url(ctx: Context, idx: int) -> str:
    site = ctx.get("site")
    album = ctx.get("album")

    return f"{site.base_url}/album/{album.id}/{idx}/"


@pass_context
def asset_url(ctx: Context, photo: "Photo", variant: str | None = None) -> str:
    site = ctx.get("site")

    sfx = "png"
    if variant is not None:
        sfx = variant + "." + sfx

    return f"{site.base_url}/photo/{photo.id}.{sfx}"
