from collections import Counter, deque
from typing import TextIO

from boldi.cli import CliCtx


def main(ctx: CliCtx, input: TextIO):
    la = deque()
    bc = Counter()
    for line in input:
        ab = line.split()
        a, b = int(ab[0]), int(ab[1])
        la.append(a)
        bc[b] += 1

    similarity = 0
    for a in la:
        similarity += a * bc[a]

    print(similarity, file=ctx.stdout)
