from itertools import product
from typing import TextIO

from boldi.cli import CliCtx


def main(ctx: CliCtx, input: TextIO):
    data = input.readlines()
    directions = list(product((0, 1, -1), (0, 1, -1)))[1:]
    XMAS_es = 0
    for y, line in enumerate(data):
        for x in range(len(line)):
            for direction in directions:
                y_ok = 0 <= y + direction[1] * 3 < len(data)
                x_ok = 0 <= x + direction[0] * 3 < len(line)
                if y_ok and x_ok:
                    X = data[y + direction[1] * 0][x + direction[0] * 0] == "X"
                    M = data[y + direction[1] * 1][x + direction[0] * 1] == "M"
                    A = data[y + direction[1] * 2][x + direction[0] * 2] == "A"
                    S = data[y + direction[1] * 3][x + direction[0] * 3] == "S"
                    XMAS = X and M and A and S
                    XMAS_es += XMAS

    print(XMAS_es, file=ctx.stdout)
