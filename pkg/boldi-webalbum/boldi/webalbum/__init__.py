import argparse
import collections
import contextlib
import functools
import itertools
import json
import logging
import math
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import jinja2
import pydantic
import tomllib
from exiftool import ExifToolHelper
from PIL import Image
from unidecode import unidecode

from boldi.build import Builder, BuildSystem, FileHandler, Handler, Stamp, Target

# Asyncio improvements:
# https://pythonspeed.com/articles/two-thread-pools/
# TODO CPU Thread Pool
# TODO Network/Disk/IO thread pool

# Packaging improvements:
# TODO split into independent packages
# * boldi.album
# * boldi.web

# source folder -> image list
# image list -> exif db
# exif db -> exif data
# image list + exif db -> output images
# output images + templates -> output html


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


IMAGE_EXTENSIONS = (".JPG", ".JPEG", ".PNG", ".GIF")
HERE = Path(__file__).parent.resolve()
NON_URL_SAFE_RE = re.compile(r"[^\w\d\.\-\(\)_/]+", re.ASCII)
RELEVANT_EXIF_TAGS = ("Composite:all", "EXIF:all", "File:all", "IPTC:all", "XMP:all")


class FolderConfig(pydantic.BaseModel):
    title: Optional[str] = None
    reversed: bool = False


class AlbumConfig(pydantic.BaseModel):
    title: str
    copyright: str
    source: Path
    target: Path
    folders: dict[Path, FolderConfig] = {}

    def model_post_init(self, __context: Any):
        self.source = self.source.expanduser()
        self.target = self.target.expanduser()


exiftool = ExifToolHelper().__enter__()


def get_exif_tags(image_path: Path) -> dict[str, Any]:
    raw_exif_tags = exiftool.get_tags(str(image_path), RELEVANT_EXIF_TAGS)[0]
    assert isinstance(raw_exif_tags, dict)
    exif_tags = collections.defaultdict(dict)
    for key, value in raw_exif_tags.items():
        assert isinstance(key, str)
        if ":" not in key:
            exif_tags[key] = value
        else:
            category, tag = key.split(":", 1)
            exif_tags[category][tag] = value
    exif_tags["SourceFile"] = image_path.name
    for category, category_tags in exif_tags.items():
        if isinstance(category_tags, dict):
            exif_tags[category] = dict(sorted(category_tags.items()))
    return dict(exif_tags)


def relative_to(path: Path, other: Path) -> Path:
    path, other = Path(path), Path(other)  # actually accept str objects too
    for i, relative_to_parents in enumerate([other] + list(other.parents)):
        if path.is_relative_to(relative_to_parents):
            return Path(*([Path("..")] * i)) / path.relative_to(relative_to_parents)


def to_safe_ascii(s: str) -> str:
    return NON_URL_SAFE_RE.sub("_", unidecode(s))


def human_round(f: float) -> str:
    if not isinstance(f, (int, float)):
        return f

    if 100 < f:
        return f"{round(round(f, 1 - math.floor(math.log10(f))))}"
    elif 20 < f:
        f = round(f, 0)
        i = round(f)
        return f"{i}" if i == f else f"{f}"
    elif 0.5 <= f:
        f = round(f, 1)
        i = round(f)
        return f"{i}" if i == f else f"{f}"
    elif 0 < f:
        return f"1/{human_round(1/f)}"
    elif f == 0.0:
        return "0"
    else:
        return f"-{human_round(-f)}"


@dataclass
class SourceImage:
    path: Path


@dataclass
class SourceFolder:
    path: Path
    subfolders: dict[str, "SourceFolder"] = field(init=False, default_factory=dict)
    images: dict[str, SourceImage] = field(init=False, default_factory=dict)

    def __post_init__(self):
        for item in sorted(self.path.iterdir()):
            name = item.name
            if name.startswith("."):
                pass
            elif item.is_file() and item.suffix.upper() in IMAGE_EXTENSIONS:
                self.images[name] = SourceImage(item)
            elif item.is_dir():
                self.subfolders[name] = SourceFolder(item)


@dataclass
class TargetImage:
    source: SourceImage
    parent: "TargetFolder"
    path: Path = field(init=False)
    path_3000w: Path = field(init=False)
    path_1500w: Path = field(init=False)
    path_800w: Path = field(init=False)
    exif_path: Path = field(init=False)

    def __post_init__(self):
        self.path = self.parent.path / to_safe_ascii(self.source.path.name)
        self.path_3000w = self.path.with_suffix(f".3000{self.path.suffix}")
        self.path_1500w = self.path.with_suffix(f".1500{self.path.suffix}")
        self.path_800w = self.path.with_suffix(f".800{self.path.suffix}")
        self.exif_path = self.path.with_suffix(f"{self.path.suffix}.exif.json")

    @functools.cached_property
    def exif(self) -> dict[str, Any]:
        return json.loads(self.exif_path.read_text())

    @property
    def title(self) -> str:
        return self.exif["IPTC"].get("ObjectName") or self.source.path.stem

    @property
    def description(self) -> str:
        return self.exif["IPTC"].get("Caption-Abstract") or ""

    @property
    def created_datetime(self) -> Optional[datetime]:
        created_str = self.exif["Composite"].get("DateTimeCreated") or self.exif["Composite"].get("DateTimeOriginal")
        if not created_str:
            return None
        with contextlib.suppress(ValueError):
            return datetime.strptime(created_str, "%Y:%m:%d %H:%M:%S%z")
        with contextlib.suppress(ValueError):
            return datetime.strptime(created_str, "%Y:%m:%d %H:%M:%S")
        return None

    @property
    def width(self) -> int:
        w = self.exif["File"]["ImageWidth"]
        assert w, f"missing width: {self.path.name}"
        return w

    @property
    def height(self) -> int:
        h = self.exif["File"]["ImageHeight"]
        assert h, f"missing height: {self.path.name}"
        return h

    @property
    def rating(self) -> int:
        return self.exif["XMP"].get("Rating", 0)

    @property
    def focal_length(self) -> Optional[float]:
        return self.exif["EXIF"].get("FocalLength")

    @property
    def focal_length_35mm(self) -> Optional[float]:
        return self.exif["Composite"].get("FocalLength35efl")

    @property
    def aperture(self) -> Optional[float]:
        return self.exif["Composite"].get("Aperture")

    @property
    def shutter_speed(self) -> Optional[float]:
        return self.exif["Composite"].get("ShutterSpeed")

    @property
    def iso(self) -> Optional[int]:
        return self.exif["EXIF"].get("ISO")

    @property
    def light_value(self) -> Optional[int]:
        return self.exif["Composite"].get("LightValue")

    @property
    def exposure_compensation(self) -> Optional[int]:
        return self.exif["EXIF"].get("ExposureCompensation")

    @property
    def camera(self) -> str:
        make: str = self.exif["EXIF"].get("Make", "")
        if make == make.upper():
            make = make.capitalize()

        model: str = self.exif["EXIF"].get("Model", "")
        if model.startswith(make):
            make = ""
        return f"{make}{' ' if make and model else ''}{model}"

    @property
    def lens(self) -> str:
        make: str = self.exif["EXIF"].get("LensMake", "")
        if make == make.upper():
            make = make.capitalize()

        model: str = self.exif["EXIF"].get("LensModel", "")
        if model.startswith(make):
            make = ""
        return f"{make}{' ' if make and model else ''}{model}"


@dataclass
class TargetFolder:
    source: SourceFolder
    parent: Optional["TargetFolder"]
    album_config: AlbumConfig
    path: Path = None
    config: FolderConfig = field(init=False)
    parents: list["TargetFolder"] = field(init=False, default_factory=list)
    subfolders: dict[str, "TargetFolder"] = field(init=False, default_factory=dict)
    images: dict[str, TargetImage] = field(init=False, default_factory=dict)
    total_image_count: int = field(init=False)

    def __post_init__(self):
        self.path = self.path or self.parent.path / to_safe_ascii(self.source.path.name)

        self.config = FolderConfig()
        for folder_config in self.album_config.folders.keys():
            if self.source.path == self.album_config.source / folder_config:
                self.config = self.album_config.folders[folder_config]

        parent = self.parent
        while parent:
            self.parents.insert(0, parent)
            parent = parent.parent

        subfolder_iter = self.source.subfolders.values()
        if self.config.reversed:
            subfolder_iter = reversed(subfolder_iter)
        for source_subfolder in subfolder_iter:
            subfolder = TargetFolder(source_subfolder, self, self.album_config)
            if subfolder.total_image_count != 0:
                self.subfolders[subfolder.path.name] = subfolder
        for source_image in self.source.images.values():
            image = TargetImage(source_image, self)
            self.images[image.path.name] = image
        subfolders_image_count = sum(s.total_image_count for s in self.subfolders.values())
        self.total_image_count = len(self.images) + subfolders_image_count

    @functools.cached_property
    def title(self) -> str:
        return self.config.title or self.source.path.name

    @functools.cached_property
    def cover_image(self) -> TargetImage:
        candidate_album_images = itertools.chain(
            self.images.values(),
            [subfolder.cover_image for subfolder in self.subfolders.values() if subfolder.cover_image],
        )
        return max(candidate_album_images, key=lambda image: image.rating)

    def path_to_folder(self, path: Path) -> Optional["TargetFolder"]:
        if path == self.path:
            return self
        elif path.is_relative_to(self.path):
            for subfolder in self.subfolders.values():
                if (maybe_subfolder := subfolder.path_to_folder(path)) is not None:
                    return maybe_subfolder

    def path_to_image(self, path: Path) -> Optional[TargetImage]:
        folder = self.path_to_folder(Path(*path.parts[:-1]))
        return folder.images.get(path.name) if folder else None


@dataclass
class TargetFolderHandler(FileHandler):
    album: "Album"

    def maybe_target_folder(self, target: Target) -> Optional[TargetFolder]:
        return self.album.target_root.path_to_folder(Path(target))

    def target_folder(self, target: Target) -> TargetFolder:
        maybe_target_folder = self.maybe_target_folder(target)
        assert maybe_target_folder
        return maybe_target_folder

    def can_handle(self, target: Target) -> bool:
        return self.maybe_target_folder(target) is not None

    async def rebuild_impl(self, target: Target, builder: Builder):
        target_folder = self.target_folder(target)

        target_folder.path.mkdir(parents=True, exist_ok=True)
        await builder.add_source(target_folder.source.path)

        for subfolder in target_folder.subfolders.values():
            await builder.build(subfolder.path)

        for image in target_folder.images.values():
            await builder.build(image.path)

        index_html = target_folder.path / "index.html"

        index_template = self.album.env.get_template("index.html.j2")
        stream = index_template.stream({"folder": target_folder})
        with open(index_html, "w") as fp:
            stream.dump(fp)
        for template_file in (HERE / "templates").iterdir():
            await builder.add_source(template_file)

        await builder.add_source(__file__)


@dataclass
class TargetImageHandler(FileHandler):
    album: "Album"

    def maybe_target_image(self, target: Target) -> Optional[TargetImage]:
        return self.album.target_root.path_to_image(Path(target))

    def target_image(self, target: Target) -> TargetImage:
        maybe_target_image = self.maybe_target_image(target)
        assert maybe_target_image
        return maybe_target_image

    def can_handle(self, target: Target) -> bool:
        return self.maybe_target_image(target) is not None

    def stamp(self, target: Target) -> Stamp:
        image = self.target_image(target)
        return "; ".join(
            FileHandler.stamp(self, path)
            for path in [
                image.path,
                image.path_3000w,
                image.path_1500w,
                image.path_800w,
                image.exif_path,
            ]
        )

    async def rebuild_impl(self, target: Target, builder: Builder):
        image = self.target_image(target)

        shutil.copy(image.source.path, image.path)

        with Image.open(image.path) as pil_image:
            w, h = 3000, round(3000 / pil_image.size[0] * pil_image.size[1])
            with pil_image.resize((w, h)) as resized_image:
                resized_image.save(
                    image.path_3000w,
                    quality=95,
                    dpi=(
                        240,
                        240,
                    ),
                )
            w, h = 1500, round(1500 / pil_image.size[0] * pil_image.size[1])
            with pil_image.resize((w, h)) as resized_image:
                resized_image.save(
                    image.path_1500w,
                    quality=95,
                    dpi=(
                        240,
                        240,
                    ),
                )
            w, h = 800, round(800 / pil_image.size[0] * pil_image.size[1])
            with pil_image.resize((w, h)) as resized_image:
                resized_image.save(
                    image.path_800w,
                    quality=95,
                    dpi=(
                        240,
                        240,
                    ),
                )

        with open(image.exif_path, "w") as fp:
            json.dump(get_exif_tags(image.source.path), fp, indent=2)

        await builder.add_source(image.source.path)
        await builder.add_source(image.path_3000w)
        await builder.add_source(image.path_1500w)
        await builder.add_source(image.path_800w)
        await builder.add_source(image.exif_path)


@dataclass
class StaticHandler(Handler):
    album: "Album"
    files: dict[str, Path] = field(init=False)

    def __post_init__(self):
        self.files = {
            f"static/{file.name}": self.album.target_static / file.name
            for file in sorted((HERE / "templates" / "static").iterdir())
        }

    def can_handle(self, target: Target) -> bool:
        return target == "//static"

    def stamp(self, target: Target) -> Stamp:
        return "; ".join(FileHandler.stamp(self, file) for file in self.files.values())

    async def rebuild_impl(self, target: Target, builder: Builder):
        self.album.target_static.mkdir(parents=True, exist_ok=True)
        for source, target in self.files.items():
            await builder.add_source(HERE / "templates" / source)
            template = self.album.env.get_template(source)
            stream = template.stream()
            with open(target, "w") as fp:
                stream.dump(fp)


@dataclass
class Album(BuildSystem):
    config: AlbumConfig
    target_root: TargetFolder = field(init=False)
    target_static: Path = field(init=False)
    env: jinja2.Environment = field(init=False)

    def __post_init__(self):
        self.target_root = TargetFolder(SourceFolder(self.config.source), None, self.config, self.config.target)
        self.target_static = self.target_root.path / "static"

        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(HERE / "templates"),
            autoescape=True,
            keep_trailing_newline=True,
            line_statement_prefix="%%",
            line_comment_prefix="%#",
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.globals = {
            "album": self,
            "root": self.target_root.path,
        }
        self.env.filters["relative_to"] = relative_to
        self.env.filters["to_safe_ascii"] = to_safe_ascii
        self.env.filters["human_round"] = human_round

        self.handlers.append(TargetFolderHandler(self))
        self.handlers.append(TargetImageHandler(self))
        self.handlers.append(StaticHandler(self))
        self.handlers.append(FileHandler())

    async def init(self):
        await self.load_build_db()

    async def render(self):
        await self.build("//static")
        await self.build(self.target_root.path)
        await self.save_build_db()


async def main():
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler())
    parser = argparse.ArgumentParser()
    parser.add_argument("album_config_path", type=Path)
    args = parser.parse_args()
    album_config_path: Path = args.album_config_path
    with open(album_config_path, "rb") as album_config_file:
        album_config_dict = tomllib.load(album_config_file)

    album_config = AlbumConfig(**album_config_dict)

    album = Album(album_config.target / "build.db.json", album_config)
    await album.init()
    await album.render()


exiftool.__exit__(None, None, None)
