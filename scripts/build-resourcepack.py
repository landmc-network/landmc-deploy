#!/usr/bin/env python3
"""Packs resourcepack/pack/ into a zip and writes the manifest the proxy reads.

The zip is named after its own SHA-1, which is what makes this work without any cache-busting:
a changed pack is a different URL, so a client holding the old one never serves it from disk by
mistake, and a client holding the new one never downloads it twice. The proxy sends the same
hash to the client, and Minecraft refuses a download that does not match it - so the file name
and the check agree by construction.

The zip is built deterministically: sorted entries, no timestamps, fixed permissions. Without
that, rebuilding an unchanged pack would produce a different hash and every player would
download the same pack again.

The pack id, on the other hand, stays the same across rebuilds. Minecraft treats it as "which
pack is this", separately from "which version of it": a new id every build makes clients drop
and re-apply rather than replace.

Usage:
    scripts/build-resourcepack.py
    scripts/build-resourcepack.py --host mc.example.com

Without --host the URL keeps {host}, which the proxy fills in with the address each player
actually connected to. That is usually what you want - it works for every domain pointed at
this server, and survives one of them changing.
"""
import argparse
import hashlib
import json
import os
import pathlib
import sys
import uuid
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PACK_DIR = ROOT / "resourcepack" / "pack"
WWW_DIR = ROOT / "resourcepack" / "www"
ID_FILE = ROOT / "resourcepack" / "pack-id"

# Zip entries carry a modification time. Fixing it is what makes an unchanged pack hash the
# same twice; the value is the epoch zip files can represent, and nothing reads it.
FIXED_TIME = (1980, 1, 1, 0, 0, 0)

MANIFEST = {
    "version": 1,
    "required": True,
    "prompt": "<green>LandMC <dark_gray>» <gray>Paczka zasobów jest wymagana, aby grać.",
    "maxAttempts": 3,
    "retryDelayMillis": 2000,
    "retryMessage": "<gray>Pobieranie paczki nie powiodło się, próbuję ponownie...",
    "declinedKickMessage":
        "<red>Paczka zasobów jest wymagana. Zaakceptuj ją, aby wejść na serwer.",
    "downloadFailedKickMessage":
        "<red>Nie udało się pobrać paczki zasobów. Spróbuj połączyć się ponownie.",
    "sendDelayMillis": 0,
    "resendAfterRebuild": True,
}


def pack_id():
    """The id from disk, or a new one written there. Never regenerated once it exists."""
    if ID_FILE.exists():
        return ID_FILE.read_text(encoding="utf-8").strip()

    generated = str(uuid.uuid4())
    ID_FILE.write_text(generated + "\n", encoding="utf-8")
    print(f"Wrote a new pack id to {ID_FILE.relative_to(ROOT)} - keep it in the repository.")
    return generated


def build(target):
    """Writes the pack to `target` and returns its SHA-1."""
    files = sorted(
        (path for path in PACK_DIR.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(PACK_DIR).as_posix())

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            info = zipfile.ZipInfo(path.relative_to(PACK_DIR).as_posix(), FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            # 0644, so the archive does not carry whatever the checkout happens to have.
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())

    return hashlib.sha1(target.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", help="address written into the download URL")
    parser.add_argument(
        "--port",
        default=os.environ.get("RESOURCEPACK_PORT", "8082"),
        help="port the pack is served on (default 8082, or RESOURCEPACK_PORT)")
    arguments = parser.parse_args()

    if not (PACK_DIR / "pack.mcmeta").is_file():
        sys.exit(
            f"No {PACK_DIR.relative_to(ROOT)}/pack.mcmeta -"
            " that file is what makes a directory a resource pack.")

    WWW_DIR.mkdir(parents=True, exist_ok=True)

    staging = WWW_DIR / ".building.zip"
    sha1 = build(staging)
    target = WWW_DIR / f"landmc-{sha1}.zip"

    if target.exists():
        staging.unlink()
        print(f"Pack unchanged ({sha1}).")
    else:
        # Renamed into place, and the old zip removed only afterwards: a client part-way
        # through downloading the previous pack keeps its file until the new one has landed.
        staging.replace(target)
        for stale in WWW_DIR.glob("landmc-*.zip"):
            if stale != target:
                stale.unlink()
        print(f"Built {target.relative_to(ROOT)}")

    manifest = dict(MANIFEST)
    manifest["packId"] = pack_id()
    manifest["sha1"] = sha1
    manifest["urlTemplate"] = (
        f"http://{arguments.host or '{host}'}:{arguments.port}/landmc-{{hash}}.zip")

    # Written in the order the proxy's record declares, so a diff between two builds shows the
    # hash changing rather than the whole file.
    ordered = {key: manifest[key] for key in (
        "version", "packId", "sha1", "urlTemplate", "required", "prompt", "maxAttempts",
        "retryDelayMillis", "retryMessage", "declinedKickMessage", "downloadFailedKickMessage",
        "sendDelayMillis", "resendAfterRebuild")}

    (WWW_DIR / "manifest.json").write_text(
        json.dumps(ordered, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Wrote {(WWW_DIR / 'manifest.json').relative_to(ROOT)}"
          f" (sha1 {sha1}, id {manifest['packId']})")


if __name__ == "__main__":
    main()
