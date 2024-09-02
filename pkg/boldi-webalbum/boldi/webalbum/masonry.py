import argparse
from pathlib import Path

import jinja2

HERE = Path(__file__).parent.resolve()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "-o", type=Path, default="masonry.html")
    args = parser.parse_args()
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(HERE / "templates"))
    with open(args.output, "wt") as fp:
        env.get_template("masonry.html.j2").stream().dump(fp)


if __name__ == "__main__":
    main()
