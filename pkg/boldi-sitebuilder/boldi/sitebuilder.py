import re
import tomllib
from argparse import ArgumentParser
from collections.abc import Iterator, Mapping
from functools import cache, partial
from pathlib import Path
from shutil import copytree
from types import MappingProxyType
from typing import IO

from jinja2 import Environment, FileSystemLoader
from markdown_it import MarkdownIt
from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.front_matter import front_matter_plugin

from boldi.cli import CliCtx, CliUsageException, esc

external_link_re = re.compile(r"^(?:[\w]+:)?//")


class SiteBuilder:
    source_dir: Path
    target_dir: Path
    site_name: str

    def __init__(self, source_dir: Path, target_dir: Path, site_name: str):
        assert source_dir.is_dir(), f"must be a directory: {source_dir}"
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.site_name = site_name
        self._md = MarkdownIt("gfm-like")
        self._md = self._md.use(anchors_plugin, permalink=True, permalinkSymbol="#")
        self._md = self._md.use(front_matter_plugin)
        self._jinja = Environment(loader=FileSystemLoader(source_dir / "template"))

    def build_all(self) -> None:
        for source_file in self.source_pages_list():
            target_file = self.target_dir / self.source_to_target[source_file]
            target_file.parent.mkdir(parents=True, exist_ok=True)
            with target_file.open("w") as fp:
                self.build_page(source_file, fp)

        copytree(self.source_dir / "template" / "static", self.target_dir / "static", dirs_exist_ok=True)

    def source_pages(self) -> Iterator[Path]:
        for source_file in sorted(self.source_dir.iterdir()):
            if source_file.is_file() and source_file.suffix == ".md":
                yield Path(source_file.name)

    @cache
    def source_pages_list(self) -> list[Path]:
        return list(self.source_pages())

    @property
    def source_to_target(self) -> Mapping[Path, Path]:
        return MappingProxyType(
            {source_page: source_page.with_suffix(".html") for source_page in self.source_pages_list()}
        )

    def build_page(self, source_file: Path, fp: IO):
        assert not source_file.is_absolute(), f"must be relative: {source_file}"
        assert source_file.is_file(), f"must be a file: {source_file}"
        assert source_file.suffix == ".md", f"must be a markdown file: {source_file}"

        jinja_env: dict[str, object] = {}
        tokens = self._md.parse((self.source_dir / source_file).read_text(), jinja_env)

        def walk(tokens: list[Token]):
            for token in tokens:
                if token.type == "inline":
                    assert isinstance(token.children, list)
                    yield from walk(token.children)
                else:
                    yield token

        for token in walk(tokens):
            if token.type == "front_matter":
                try:
                    _front_matter: dict[str, object] | Exception = tomllib.loads(token.content)
                except Exception as ex:
                    _front_matter = ex
            if token.type == "link_open" and (href := token.attrGet("href")):
                assert isinstance(href, str)
                if external_link_re.match(str(token.attrGet("href"))):
                    token.attrSet("target", "_blank")
                if Path(href) in self.source_to_target:
                    # FIXME this works for pages in the root dir but not nested pages
                    token.attrSet("href", self.source_to_target[Path(href)].as_posix())

        markdown = SyntaxTreeNode(tokens)

        def heading_text(node: SyntaxTreeNode) -> str:
            if node.type == "text":
                return node.content
            return "".join(heading_text(child) for child in node.children)

        headings = [(node.tag, heading_text(node)) for node in markdown.walk() if node.type == "heading"]
        title = min(headings, default=("h6", ""))

        html = self._md.renderer.render(tokens, self._md.options, jinja_env)
        template = self._jinja.get_template("index.html.j2")
        stream = template.stream(content=html, title=title[1], site_name=self.site_name)
        stream.dump(fp)


def cli_sitebuilder(ctx: CliCtx, subparser: ArgumentParser):
    subparser.usage = "run a sitebuilder command"
    subparser.add_argument("--source-dir", "-s", type=Path, default=Path("."), help="source directory")
    subparser.add_argument("--target-dir", "-t", type=Path, default=Path("out"), help="target directory")
    subparser.add_argument("--site-name", "-n", type=str, default="my site", help="site name")
    subparser.set_defaults(action=partial(cli_sitebuilder_run, ctx))


def cli_sitebuilder_run(ctx: CliCtx, source_dir: Path, target_dir: Path, site_name: str):
    if not source_dir.is_dir():
        raise CliUsageException(f"{esc(source_dir)} is not a directory")

    sitebuilder = SiteBuilder(source_dir, target_dir, site_name)
    sitebuilder.build_all()
