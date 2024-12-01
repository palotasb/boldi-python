from heapq import heappop, heappush
from typing import TextIO

from boldi.cli import CliCtx


def main(ctx: CliCtx, input: TextIO):
    la, lb = [], []
    for line in input:
        ab = line.split()
        a, b = int(ab[0]), int(ab[1])
        heappush(la, a)
        heappush(lb, b)

    dst = 0
    while la:
        a, b = heappop(la), heappop(lb)
        dst += abs(b - a)

    print(dst, file=ctx.stdout)
