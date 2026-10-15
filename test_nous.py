import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from nous.ledger import Ledger
from nous.report import analyze, LIT, DRIFT, DARK
from nous.claims import judge, claim_hash
from nous.gate import evaluate
from nous.units import split

SRC = "def transfer(amount, account):\n    if amount > account.balance:\n        raise ValueError('overdraft')\n    account.balance -= amount\n\ndef audit(log):\n    return [l for l in log if l.flagged]\n"
GOOD = "transfer refuses any amount larger than account balance by raising ValueError for overdraft, otherwise it subtracts amount from account.balance"
GOOD2 = "audit returns every entry from log whose flagged attribute is truthy, as a list comprehension over log"


class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.d, "core"))
        self.f = os.path.join(self.d, "core", "pay.py")
        open(self.f, "w").write(SRC)
        self.led = Ledger(self.d)

    def unit(self, name):
        return next(r.unit for r in analyze(self.d, self.led).rows if r.unit.name == name)

    def states(self):
        return {r.unit.name: r.state for r in analyze(self.d, self.led).rows}

    def test_splits_functions(self):
        self.assertEqual({u.name for u in split("a.py", SRC)}, {"transfer", "audit"})

    def test_lifecycle_dark_lit_drift(self):
        self.assertEqual(set(self.states().values()), {DARK})
        self.led.append(self.unit("transfer"), "ann@x.io", GOOD)
        self.assertEqual(self.states(), {"transfer": LIT, "audit": DARK})
        open(self.f, "w").write(SRC.replace("amount >", "amount >="))
        self.assertEqual(self.states()["transfer"], DRIFT)

    def test_moving_code_keeps_proof(self):
        self.led.append(self.unit("transfer"), "ann@x.io", GOOD)
        a, b = SRC.split("\n\n")
        open(self.f, "w").write("\n\n" + b + "\n\n" + a)
        self.assertEqual(self.states()["transfer"], LIT)

    def test_rubber_stamp_rejected(self):
        code = self.unit("transfer").text
        self.assertFalse(judge(code, "lgtm looks good to me")[0])
        self.assertFalse(judge(code, "this function is very good and does what it should do for everyone involved here")[0])
        self.assertTrue(judge(code, GOOD)[0])
        self.assertFalse(judge(code, GOOD, {claim_hash(GOOD)})[0])

    def test_tamper_detected(self):
        self.led.append(self.unit("transfer"), "a", GOOD)
        self.led.append(self.unit("audit"), "a", GOOD2)
        self.assertTrue(self.led.verify()[0])
        t = open(self.led.path).read().replace('"who": "a"', '"who": "mallory"', 1)
        open(self.led.path, "w").write(t)
        self.assertFalse(self.led.verify()[0])

    def test_gate(self):
        rep = analyze(self.d, self.led)
        self.assertTrue(evaluate(self.d, rep, minimum=50))
        self.assertTrue(evaluate(self.d, rep, critical=[("core/*", 100)]))
        self.assertFalse(evaluate(self.d, rep, minimum=0))
        self.led.append(self.unit("transfer"), "a", GOOD)
        self.led.append(self.unit("audit"), "a", GOOD2)
        self.assertFalse(evaluate(self.d, analyze(self.d, self.led), 100, [("core/*", 100)]))


if __name__ == "__main__":
    unittest.main()
