import re
from typing import TextIO

from boldi.cli import CliCtx

RE = re.compile(r"mul\((\d+),(\d+)\)")


def main(ctx: CliCtx, input: TextIO):
    result = 0
    for line in input:
        for match in re.finditer(RE, line):
            result += int(match[1]) * int(match[2])

    print(result, file=ctx.stdout)
