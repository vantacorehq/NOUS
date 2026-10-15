"""The gate: the point where understanding becomes a requirement, not a hope."""
import fnmatch
from .report import new_dark


def evaluate(root, report, minimum=0.0, critical=(), base=None):
    fails = []
    if report.coverage * 100 < minimum:
        fails.append(f"global comprehension {report.coverage*100:.1f}% < required {minimum:g}%")
    for glob, pct in critical:
        cov = report.coverage_of(lambda p, g=glob: fnmatch.fnmatch(p, g)) * 100
        if cov < pct:
            fails.append(f"critical path '{glob}': {cov:.1f}% < required {pct:g}%")
    if base:
        nd = new_dark(root, report, base)
        if nd:
            fails.append(f"{len(nd)} unit(s) in this change that no human has vouched for:")
            fails += [f"    {r.unit.key} (L{r.unit.start}-{r.unit.end})" for r in nd[:25]]
    return fails
