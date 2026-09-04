#!/usr/bin/env python3
"""Turns on Velocity forwarding in Paper's own global config.

Paper owns paper-global.yml: it has a schema version, it migrates the file between releases,
and it rewrites it. Shipping a whole copy of that file means guessing a version - which is
exactly how this deployment ended up logging "Loading a newer configuration than is supported
(33 > 31)" and running on defaults it did not intend.

So this edits the two keys the deployment actually owns, in whatever file Paper generated, and
leaves the rest alone. If the file does not exist yet, a minimal one is written without a
version, so Paper migrates it up on first start instead of being told a version we invented.
"""
import os
import sys
from pathlib import Path

MINIMAL = """# Written by landmc-deploy. Paper owns this file and will fill in the rest on first start.
proxies:
  velocity:
    enabled: true
    online-mode: true
    secret: '{secret}'
"""


def patch(path: Path, secret: str) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    in_proxies = in_velocity = False
    changed = []

    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())

        if indent == 0 and stripped.endswith(":"):
            in_proxies = stripped == "proxies:"
            in_velocity = False
        elif in_proxies and indent == 2 and stripped.endswith(":"):
            in_velocity = stripped == "velocity:"
        elif in_velocity and indent == 4:
            if stripped.startswith("enabled:"):
                line = "    enabled: true"
            elif stripped.startswith("secret:"):
                line = f"    secret: '{secret}'"

        changed.append(line)

    return "\n".join(changed) + "\n"


def main() -> int:
    path = Path(sys.argv[1])
    secret = os.environ.get("FORWARDING_SECRET", "")
    if not secret:
        print("FORWARDING_SECRET is empty", file=sys.stderr)
        return 1

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        path.write_text(patch(path, secret), encoding="utf-8")
        print(f"patched {path}")
    else:
        path.write_text(MINIMAL.format(secret=secret), encoding="utf-8")
        print(f"wrote {path}")

    path.chmod(0o600)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
