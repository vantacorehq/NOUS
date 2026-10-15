"""Thin, dependency-free git + filesystem access."""
import os
import subprocess
from .units import EXTS

SKIP_DIRS = {".git", ".nous", "node_modules", "venv", ".venv", "__pycache__", "dist", "build"}


def git(root, *args):
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    return r.returncode, r.stdout


def tracked(root):
    code, out = git(root, "ls-files")
    paths = out.splitlines() if code == 0 and out.strip() else _walk(root)
    return sorted(p for p in paths if os.path.splitext(p)[1] in EXTS)


def _walk(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            yield os.path.relpath(os.path.join(d, f), root)


def read(root, path):
    p = os.path.join(root, path)
    try:
        if os.path.getsize(p) > 1_000_000:
            return None
        with open(p, encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


def identity(root):
    code, out = git(root, "config", "user.email")
    return out.strip() if code == 0 and out.strip() else os.environ.get("USER", "unknown")


def changed_files(root, base):
    code, out = git(root, "diff", "--name-only", f"{base}...HEAD")
    if code != 0:
        code, out = git(root, "diff", "--name-only", base)
    return out.splitlines() if code == 0 else []


def show(root, ref, path):
    code, out = git(root, "show", f"{ref}:{path}")
    return out if code == 0 else None
