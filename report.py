"""Turn a repo + a ledger into a truth: what is lit, what drifted, what is dark."""
from dataclasses import dataclass, field
from . import gitio
from .units import split, Unit

LIT, DRIFT, DARK = "lit", "drift", "dark"


@dataclass
class Row:
    unit: Unit
    state: str
    vouchers: list = field(default_factory=list)


@dataclass
class Report:
    rows: list

    def _cov(self, rows):
        tot = sum(r.unit.loc for r in rows)
        return (sum(r.unit.loc for r in rows if r.state == LIT) / tot) if tot else 1.0

    @property
    def coverage(self):
        return self._cov(self.rows)

    def coverage_of(self, pred):
        return self._cov([r for r in self.rows if pred(r.unit.path)])

    def by_state(self, s):
        return [r for r in self.rows if r.state == s]

    @property
    def single_point(self):
        return [r for r in self.rows if r.state == LIT and len(set(r.vouchers)) == 1]


def analyze(root, ledger):
    es = ledger.entries()
    by_id, by_key = {}, {}
    for e in es:
        by_id.setdefault(e["unit"], []).append(e["who"])
        by_key.setdefault(e["key"], set()).add(e["unit"])
    rows = []
    for p in gitio.tracked(root):
        src = gitio.read(root, p)
        if src is None:
            continue
        for u in split(p, src):
            if u.id in by_id:
                rows.append(Row(u, LIT, by_id[u.id]))
            elif u.key in by_key:
                rows.append(Row(u, DRIFT))
            else:
                rows.append(Row(u, DARK))
    return Report(rows)


def new_dark(root, report, base):
    """Units a change introduced or altered that nobody has vouched for."""
    out = []
    for p in gitio.changed_files(root, base):
        old = gitio.show(root, base, p)
        old_ids = {u.id for u in split(p, old)} if old else set()
        for r in report.rows:
            if r.unit.path == p and r.state != LIT and r.unit.id not in old_ids:
                out.append(r)
    return out
