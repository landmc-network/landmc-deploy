#!/usr/bin/env python3
"""Points a world at the plugin that generates it, in Paper's own bukkit.yml.

Paper owns bukkit.yml the same way it owns paper-global.yml: it fills in every missing default
and rewrites the file. Shipping a whole copy means the deployment and the server disagree about
everything the copy does not mention, which is how this repository once ended up running on
defaults it never chose.

So this sets one key - worlds.<world>.generator - in whatever file Paper generated, and leaves
the rest alone. If the file does not exist yet a minimal one is written, and Paper fills in the
rest on first start.

Note what this does not do: a world that already exists keeps whatever it was generated as. To
change one, stop the server and delete its directory so it is created again.

    scripts/bukkit-generator.py servers/lobby/bukkit.yml lobby landmc-lobby
"""
import sys
from pathlib import Path

MINIMAL = """# Written by landmc-deploy. Paper owns this file and will fill in the rest on first start.
worlds:
  {world}:
    generator: {plugin}
"""


def patch(path: Path, world: str, plugin: str) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()

    out = []
    in_worlds = False
    in_world = False
    wrote_generator = False
    saw_world = False

    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())

        if indent == 0 and stripped.endswith(":"):
            # Leaving the worlds block without having seen our world: add it here.
            if in_worlds and not saw_world:
                out.append(f"  {world}:")
                out.append(f"    generator: {plugin}")
                saw_world = wrote_generator = True

            in_worlds = stripped == "worlds:"
            in_world = False

        elif in_worlds and indent == 2 and stripped.endswith(":"):
            in_world = stripped == f"{world}:"
            if in_world:
                saw_world = True

        elif in_world and indent == 4 and stripped.startswith("generator:"):
            out.append(f"    generator: {plugin}")
            wrote_generator = True
            continue

        out.append(line)

    if in_worlds and not saw_world:
        out.append(f"  {world}:")
        out.append(f"    generator: {plugin}")
        wrote_generator = True
    elif saw_world and not wrote_generator:
        # The world is listed with other settings but no generator; put one in.
        result = []
        for line in out:
            result.append(line)
            if line.strip() == f"{world}:" and len(line) - len(line.lstrip()) == 2:
                result.append(f"    generator: {plugin}")
        out = result
        wrote_generator = True

    if not wrote_generator:
        out.append("worlds:")
        out.append(f"  {world}:")
        out.append(f"    generator: {plugin}")

    return "\n".join(out) + "\n"


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    world, plugin = sys.argv[2], sys.argv[3]

    if path.exists():
        path.write_text(patch(path, world, plugin), encoding="utf-8")
        print(f"set worlds.{world}.generator to {plugin} in {path}")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(MINIMAL.format(world=world, plugin=plugin), encoding="utf-8")
        print(f"wrote a minimal {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
