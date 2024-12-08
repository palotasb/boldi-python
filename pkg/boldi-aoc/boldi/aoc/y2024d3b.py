import re
from typing import TextIO

from boldi.cli import CliCtx

RE = re.compile(r"(?:mul\((\d+),(\d+)\))|do\(\)|don't\(\)")


def main(ctx: CliCtx, input: TextIO):
    result = 0
    enabled = True
    for line in input:
        for match in re.finditer(RE, line):
            if match[0] == "do()":
                enabled = True
            elif match[0] == "don't()":
                enabled = False
            elif enabled:
                result += int(match[1]) * int(match[2])

    print(result, file=ctx.stdout)
