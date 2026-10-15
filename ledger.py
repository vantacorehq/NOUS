"""Append-only, hash-chained, optionally HMAC-signed ledger of understanding.

Every entry commits to the previous one. Rewrite history and the chain breaks:
`nous verify` will say exactly where.
"""
import hashlib
import hmac
import json
import os
import time
from .claims import claim_hash

GENESIS = "0" * 64


def _canon(d):
    return json.dumps(d, sort_keys=True, separators=(",", ":")).encode()


class Ledger:
    def __init__(self, root):
        self.dir = os.path.join(root, ".nous")
        self.path = os.path.join(self.dir, "ledger.jsonl")

    def entries(self):
        if not os.path.exists(self.path):
            return []
        with open(self.path, encoding="utf-8") as fh:
            return [json.loads(l) for l in fh if l.strip()]

    def used_claims(self):
        return {e["claim_hash"] for e in self.entries()}

    def append(self, unit, who, claim):
        os.makedirs(self.dir, exist_ok=True)
        es = self.entries()
        body = {"v": 1, "unit": unit.id, "key": unit.key, "loc": unit.loc, "who": who,
                "claim": claim, "claim_hash": claim_hash(claim),
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "prev": es[-1]["hash"] if es else GENESIS}
        secret = os.environ.get("NOUS_KEY")
        if secret:
            body["sig"] = hmac.new(secret.encode(), _canon(body), hashlib.sha256).hexdigest()
        body["hash"] = hashlib.sha256(_canon(body)).hexdigest()
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(body, sort_keys=True) + "\n")
        return body

    def verify(self):
        prev, secret = GENESIS, os.environ.get("NOUS_KEY")
        for i, e in enumerate(self.entries(), 1):
            body = {k: v for k, v in e.items() if k != "hash"}
            if body["prev"] != prev:
                return False, f"entry {i}: chain broken (history was rewritten)"
            if hashlib.sha256(_canon(body)).hexdigest() != e["hash"]:
                return False, f"entry {i}: contents were tampered with"
            if secret and "sig" in body:
                sig = body.pop("sig")
                good = hmac.new(secret.encode(), _canon(body), hashlib.sha256).hexdigest()
                if not hmac.compare_digest(sig, good):
                    return False, f"entry {i}: signature invalid"
            prev = e["hash"]
        return True, f"{len(self.entries())} entries, chain intact"
