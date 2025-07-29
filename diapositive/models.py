import hashlib
import logging
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from importlib.resources import as_file, files
from numbers import Rational
from pathlib import Path

from pprint import pprint

import hcl2
from jinja2 import Environment, PackageLoader, Template, select_autoescape
from PIL import ExifTags as tags
from PIL import Image

from . import filters
from .util import DLList, Node, get_first, slugify

if sys.version_info[0] == 3 and sys.version_info[1] < 13:
    from mimetypes import guess_type as guess_file_type
else:
    from mimetypes import guess_file_type

FILM_RE = re.compile(r"film ?stock: ?(.*)$", flags=re.IGNORECASE|re.MULTILINE)
logger = logging.getLogger(__name__)


@dataclass
class Copyright:
    artist: str
    years: str
    licence: str

    @classmethod
    def from_config(cls, d: dict[str, str]):
        return cls(
            artist=d["artist"],
            years=d.get("years", str(datetime.now().year)),
            licence=d.get("licence", "all rights reserved"),
        )


@dataclass
class Metadata:
    make: str | None
    model: str | None
    lens_make: str | None
    lens_model: str | None
    focal_length: float | Rational | None
    exposure: float | Rational | None
    aperture: float | Rational | None
    iso: int | None
    film: str | None
    date: datetime | None
    desc: str | None

    @classmethod
    def from_exif(cls, exif: Image.Exif):
        ex = exif._get_merged_dict()
        film = desc = None

        if desc := get_first(ex, tags.Base.ImageDescription, tags.Base.UserComment):
            if g := FILM_RE.search(desc):
                film = g[1].strip()
                desc = FILM_RE.sub("", desc)

        if (exposure := ex.get(tags.Base.ExposureTime)) is None:
            if (exposure := ex.get(tags.Base.ShutterSpeedValue)) is not None:
                # APEX to seconds
                exposure = 1 / (2 ** exposure)

        if (aperture := ex.get(tags.Base.FNumber)) is None:
            if (aperture := ex.get(tags.Base.ApertureValue)) is not None:
                # APEX to f-stop
                aperture = 2 ** (aperture / 2)

        datestr = get_first(ex, tags.Base.DateTimeOriginal, tags.Base.DateTime)
        if datestr is not None:
            date = datetime.strptime(datestr, "%Y:%m:%d %H:%M:%S")
        else:
            date = None

        return cls(
            make=ex.get(tags.Base.Make),
            model=ex.get(tags.Base.Model),
            lens_make=ex.get(tags.Base.LensMake),
            lens_model=ex.get(tags.Base.LensModel),
            focal_length=ex.get(tags.Base.FocalLength),
            exposure=exposure,
            aperture=aperture,
            iso=ex.get(tags.Base.ISOSpeedRatings),
            film=film,
            date=date,
            desc=desc,
        )

@dataclass
class Photo:
    id: str
    src: Path
    data: Image.Image
    metadata: Metadata

    @classmethod
    def from_path(cls, path: Path):
        img = Image.open(path)
        id = hashlib.blake2s(str.encode(str(img.getexif())), digest_size=16).hexdigest()

        return cls(
            id=id,
            src=path,
            data=img,
            metadata=Metadata.from_exif(img.getexif()),
        )

    def write_image(self, max_size: int, outdir: Path, variant: str | None = None, copyright: Copyright | None = None):
        sfx = "png"
        if variant is not None:
            logger.debug(f"writing {variant} image for photo {self.id}")
            sfx = f"{variant}.{sfx}"
        else:
            logger.debug(f"writing image for photo {self.id}")

        photo_path = outdir / f"photo/{self.id}.{sfx}"
        if photo_path.exists():
            return

        im = self.data.copy()
        im.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        exif = Image.Exif()
        if copyright is not None:
            exif[tags.Base.Copyright] = f"{copyright.artist}, {copyright.licence}"
        if self.metadata.desc is not None:
            exif[tags.Base.ImageDescription] = self.metadata.desc

        im.save(photo_path, optimize=True, exif=exif)

    def write(self, index: int, album: "Album", outdir: Path, tmpl: Template):
        photo_path = outdir / "album" / album.id / str(index) / "index.html"
        logger.debug(f"creating directories for photo page: {photo_path}")
        photo_path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"writing photo page for photo {self.id}")
        tmpl.stream(index=index, photo=self, album=album).dump(str(photo_path))


@dataclass
class Album(Node):
    id: str
    title: str
    src: Path
    cover: Photo
    photos: list[Photo]

    @classmethod
    def from_path(cls, path: Path):
        id = slugify(path.name)
        title = id
        cover_idx = 1

        metafile = path / "album.hcl"
        if metafile.exists():
            with metafile.open("r") as f:
                meta = hcl2.load(f)
                pprint(meta)
            title = meta.get("title", title)
            cover_idx = meta.get("cover", cover_idx)

        photos = []
        for itm in sorted(path.glob("*")):
            if itm.is_file():
                if (mime := guess_file_type(itm)[0]) is not None and mime.startswith("image/"):
                    photos.append(Photo.from_path(itm))

        if not (0 < cover_idx <= len(photos)):
            logger.warning(f"cover index {cover_idx} for album '{id}' outside range (photos in album: {len(photos)})")
            cover_idx = 1

        return cls(
            id=id,
            title=title,
            src=path,
            cover=photos[cover_idx-1],
            photos=photos,
        )

    def write(self, outdir: Path, tmpl: Template):
        album_path = outdir / "album" / self.id / "index.html"
        album_path.parent.mkdir(parents=True, exist_ok=True)
        tmpl.stream(album=self).dump(str(album_path))

    def __len__(self) -> int:
        return len(self.photos)


@dataclass
class Site:
    base_url: str
    title: str
    thumb_size: int
    image_size: int
    copyright: Copyright
    albums: DLList[Album]

    @classmethod
    def from_config(cls, path: Path):
        with path.open("r") as f:
            cfg = hcl2.load(f)
            pprint(cfg)

        if "copyright" in cfg:
            copyright = Copyright.from_config(cfg["copyright"])
        else:
            raise ValueError("missing copyright info")

        return cls(
            base_url=cfg["base_url"],
            title=cfg.get("title", "diapositive"),
            thumb_size=cfg.get("thumb_size", 512),
            image_size=cfg.get("image_size", 2500),
            copyright=copyright,
            albums=DLList(),
        )

    def read_albums(self, path: Path):
        albums = []
        for itm in sorted(path.glob("*")):
            if itm.is_dir() and not itm.name == "_site":
                albums.append(Album.from_path(itm))
        self.albums = DLList(albums)

    def write(self, outdir: Path):
        if outdir.exists():
            shutil.rmtree(outdir)
        outdir.mkdir(parents=True)

        env = Environment(
            loader=PackageLoader("diapositive"),
            autoescape=select_autoescape(),
        )
        env.globals["site"] = self
        for f in filters.__all__:
            env.filters[f] = getattr(filters, f)

        with as_file(files("diapositive.static")) as static:
            shutil.copytree(static, outdir / "static")
        env.get_template("index.html").stream().dump(str(outdir / "index.html"))

        (outdir / "album").mkdir(parents=True)
        env.get_template("redirect.html").stream(dest="/").dump(str(outdir / "album/index.html"))
        (outdir / "photo").mkdir(parents=True)
        env.get_template("redirect.html").stream(dest="/").dump(str(outdir / "photo/index.html"))

        env.get_template("404.html").stream().dump(str(outdir / "404.html"))

        for album in self.albums:
            album.write(outdir, env.get_template("album.html"))

            for idx, photo in enumerate(album.photos, start=1):
                photo.write(idx, album, outdir, env.get_template("photo.html"))
                photo.write_image(self.thumb_size, outdir, variant="thm", copyright=self.copyright)
                photo.write_image(self.image_size, outdir, copyright=self.copyright)
