import re
from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from shutil import copytree
from typing import IO

from jinja2 import Environment, FileSystemLoader
from markdown_it import MarkdownIt
from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode
from mdformat.renderer import MDRenderer

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
        self._jinja = Environment(loader=FileSystemLoader(source_dir / "template"))

    def target_path(self, source_file: Path) -> Path:
        assert not source_file.is_absolute(), f"must be relative: {source_file}"
        return self.target_dir / source_file.with_suffix(".html")

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
            if token.type == "link_open" and external_link_re.match(str(token.attrGet("href"))):
                token.attrSet("target", "_blank")

        markdown = SyntaxTreeNode(tokens)

        headings = [
            (node.tag, self.node_to_text(node), self.node_to_html(node))
            for node in markdown.walk()
            if node.type == "heading"
        ]
        title = min(headings, key=lambda x: x[0], default=("h6", "", ""))

        html = self._md.renderer.render(tokens, self._md.options, jinja_env)
        template = self._jinja.get_template("index.html.j2")
        stream = template.stream(content=html, title=title[1], site_name=self.site_name)
        stream.dump(fp)

    def node_to_html(self, node: SyntaxTreeNode) -> str:
        return self._md.renderer.render(node.to_tokens(), self._md.options, {}).strip()

    def node_to_text(self, node: SyntaxTreeNode) -> str:
        md_renderer = MDRenderer()
        return " ".join(md_renderer.render(child.to_tokens(), self._md.options, {}).strip() for child in node.children)

    def build_all(self) -> None:
        for source_file in self.source_dir.iterdir():
            relative_source_file = Path(source_file.name)
            if source_file.is_file() and source_file.suffix == ".md":
                target_file = self.target_path(relative_source_file)
                target_file.parent.mkdir(parents=True, exist_ok=True)
                with target_file.open("w") as fp:
                    self.build_page(source_file, fp)

        copytree(self.source_dir / "template" / "static", self.target_dir / "static", dirs_exist_ok=True)


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
