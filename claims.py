"""The anti-rubber-stamp check.

A claim of understanding must (1) be a real explanation, (2) touch the
actual code, (3) not be copy-pasted. Plug in a stronger interrogator —
an LLM, a quiz, a pair-review bot — with NOUS_JUDGE="your-command":
it receives {"code":..., "claim":...} on stdin and must exit 0 to pass.
"""
import hashlib
import json
import os
import re
import subprocess

KW = set("""self return import from class def none true false elif else while with yield lambda
pass break continue raise except finally assert global nonlocal print this const function var let
async await static void public private int string bool float double char long main args kwargs""".split())


def idents(text):
    return {w for w in re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", text) if w.lower() not in KW}


def judge(code, claim, used=frozenset()):
    if len(claim.split()) < 12:
        return False, "explanation too short — say what it does, why, and what breaks it (>= 12 words)"
    ids = idents(code)
    need = min(2, len(ids))
    hit = {i for i in ids if re.search(r"\b" + re.escape(i) + r"\b", claim)}
    if len(hit) < need:
        return False, f"your explanation never touches the code; mention >= {need} of: {sorted(ids)[:6]}"
    if claim_hash(claim) in used:
        return False, "that exact explanation was already used for another unit"
    cmd = os.environ.get("NOUS_JUDGE")
    if cmd:
        r = subprocess.run(cmd, shell=True, input=json.dumps({"code": code, "claim": claim}),
                           capture_output=True, text=True)
        if r.returncode != 0:
            return False, "interrogator rejected the claim: " + (r.stdout or r.stderr).strip()[:300]
    return True, "ok"


def claim_hash(claim):
    return hashlib.sha256(" ".join(claim.lower().split()).encode()).hexdigest()
