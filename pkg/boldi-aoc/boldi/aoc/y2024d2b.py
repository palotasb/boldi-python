from typing import TextIO

from boldi.cli import CliCtx


def main(ctx: CliCtx, input: TextIO):
    print(sum(is_safe(report_s) for report_s in input), file=ctx.stdout)


def parse_report(report_s: str) -> list[int]:
    return [int(level_s) for level_s in report_s.split()]


def is_safe(report_s: str) -> bool:
    report = parse_report(report_s)
    return is_safe_dec(report, True) or is_safe_inc(report, True)


def is_safe_dec(report: list[int], dampen: bool) -> bool:
    return (
        all([1 <= a - b <= 3 for a, b in zip(report, report[1:])])
        or dampen
        and any(is_safe_dec(report[:n] + report[n + 1 :], False) for n in range(len(report)))
    )


def is_safe_inc(report: list[int], dampen: bool) -> bool:
    return (
        all([1 <= b - a <= 3 for a, b in zip(report, report[1:])])
        or dampen
        and any(is_safe_inc(report[:n] + report[n + 1 :], False) for n in range(len(report)))
    )
