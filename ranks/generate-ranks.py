"""Writes the LandMC rank ladder as SQL LuckPerms can be given directly.

The ladder, the names and the colours are the old server's UserRank enum, in the same order it
listed them. What each rank may do is the same too, expressed as permissions rather than as
"is this index at least that index", because that is what LuckPerms understands and what makes
it changeable without a build.

Generated rather than typed: fourteen groups times prefixes, weights, inheritance and
permissions is a place where one wrong line is a rank that silently cannot do its job.
"""

import pathlib

# Legacy colour codes to their modern names, so the prefixes read as the old ones looked.
COLOURS = {
    "c": "red", "6": "gold", "e": "yellow", "a": "green",
    "b": "aqua", "3": "dark_aqua", "d": "light_purple",
    "9": "blue", "2": "dark_green", "f": "white", "7": "gray",
}

# The same colours as hex, for the one prefix that has to be written a letter at a time.
HEX = {
    "c": "#FF5555", "6": "#FFAA00", "e": "#FFFF55", "a": "#55FF55",
    "b": "#55FFFF", "3": "#00AAAA", "d": "#FF55FF",
}

# LuckPerms stores a node in a varchar(200). A prefix written per letter runs out of room
# quickly, and the whole insert fails on the one row that does - taking the rest with it.
MAXIMUM_NODE = 200


def rainbow(word):
    """The old server's rainbow, one colour per letter, cycling through the same seven.

    Written with hex codes and a single bold wrapping the lot, rather than a named colour and a
    bold tag per letter. The result is the same and it fits in the column; the readable version
    was 250 characters and could not be stored at all.
    """
    cycle = ["c", "6", "e", "a", "b", "3", "d"]
    letters = "".join(
        f"<{HEX[cycle[index % len(cycle)]]}>{letter}"
        for index, letter in enumerate(word))
    return f"<b>{letters}</b>"


def plain(colour, word):
    return f"<{COLOURS[colour]}><bold>{word}</bold> "


# (name, weight, prefix, parent, permissions)
LADDER = [
    ("default", 0, None, None, [
        # Without these, the commands every player is meant to use are refused to everybody.
        "landmc.command.friend",
        "landmc.command.msg",
        "landmc.command.ignore",
        "landmc.command.server",
        "landmc.command.live",
        "landmc.command.helpop",
    ]),
    ("vip", 10, plain("e", "VIP"), "default", [
        # Two seconds between messages instead of five, as it was.
        "landmc.chat.cooldown.short",
        # Flight on the hub, the first thing the old server gave for a rank.
        "landmc.lobby.fly",
    ]),
    ("svip", 20, plain("d", "SVIP"), "vip", [
        # Colours and emoticons in chat started here.
        "landmc.chat.colors",
    ]),
    ("szefuncio", 30, rainbow("SZEFUNCIO") + "<white> ", "svip", []),
    ("sponsor", 40, plain("a", "SPONSOR"), "szefuncio", []),
    ("miniyt", 50, plain("6", "MiniYT"), "sponsor", []),
    ("yt", 60, plain("6", "YT"), "miniyt", []),
    ("buildteam", 70, plain("3", "BUILD TEAM"), "yt", [
        # The team never waited between messages.
        "landmc.chat.cooldown.bypass",
        "landmc.cooldown.bypass",
        "landmc.command.setspawn",
    ]),
    ("helper", 80, plain("9", "POMOCNIK"), "buildteam", [
        # Links were allowed from here up, which is why the filter has an exemption at all.
        "landmc.chat.links",
        "landmc.command.helpop.receive",
        "landmc.command.helpop.nodelay",
        "landmc.punishments.kick",
        "landmc.punishments.warn",
        "landmc.punishments.history",
        "landmc.punishments.notify",
    ]),
    ("mod", 90, plain("2", "MODERATOR"), "helper", [
        "landmc.punishments.ban",
        "landmc.punishments.tempban",
        "landmc.punishments.banip",
        "landmc.punishments.unban",
        "landmc.command.socialspy",
        "landmc.command.adminchat",
        "landmc.adminchat.spy",
        "landmc.economy.balance.others",
    ]),
    ("admin", 100, plain("c", "ADMIN"), "mod", [
        "landmc.command.maintenance",
        "landmc.maintenance.bypass",
        "landmc.command.setrank",
        "landmc.command.broadcast",
        "landmc.command.send",
        "landmc.command.live.admin",
        "landmc.economy.admin",
        "landmc.auth.admin",
        "landmc.antiproxy.admin",
        "landmc.voucher.generate",
    ]),
    ("manager", 110, plain("c", "MANAGER"), "admin", []),
    # The two that run the place get everything, including whatever is added next.
    ("owner", 120, plain("c", "WŁAŚCICIEL"), "manager", ["*"]),
    ("developer", 130, plain("c", "DEVELOPER"), "manager", ["*"]),
]


def rows():
    out = []
    for name, weight, prefix, parent, permissions in LADDER:
        nodes = list(permissions)
        if parent:
            nodes.append(f"group.{parent}")
        if weight:
            nodes.append(f"weight.{weight}")
        if prefix:
            nodes.append(f"prefix.{weight}.{prefix}")
        for node in nodes:
            out.append((name, node))
    return out


def main():
    lines = [
        "-- The LandMC rank ladder.",
        "--",
        "-- Generated from the old server's UserRank enum: the same ranks in the same order,",
        "-- with the colours it used. What each one may do is expressed as permissions rather",
        "-- than as a comparison of indexes, so it can be changed without a build.",
        "--",
        "-- Each rank inherits the one below it, which is what made hasRank() work there: a",
        "-- moderator has everything a VIP has, and nothing has to be listed twice.",
        "--",
        "-- Safe to run again. Groups are inserted only when missing, and every node this file",
        "-- owns is replaced, so editing the list here and re-running is the way to change it.",
        "",
    ]

    names = ", ".join(f"('{name}')" for name, *_ in LADDER)
    lines.append(f"INSERT IGNORE INTO luckperms_groups (name) VALUES {names};")
    lines.append("")

    owned = ", ".join(f"'{name}'" for name, *_ in LADDER)
    lines.append("-- Everything below is rewritten, so a node removed from this file goes away.")
    lines.append(f"DELETE FROM luckperms_group_permissions WHERE name IN ({owned});")
    lines.append("")

    lines.append("INSERT INTO luckperms_group_permissions")
    lines.append("    (name, permission, value, server, world, expiry, contexts)")
    lines.append("VALUES")

    values = [
        f"    ('{name}', '{node.replace(chr(39), chr(39) * 2)}', 1, 'global', 'global', 0, '{{}}')"
        for name, node in rows()
    ]
    lines.append(",\n".join(values) + ";")
    lines.append("")

    longest = max(rows(), key=lambda row: len(row[1]))
    if len(longest[1]) > MAXIMUM_NODE:
        raise SystemExit(
            f"'{longest[0]}' has a node of {len(longest[1])} characters; LuckPerms stores "
            f"at most {MAXIMUM_NODE}, and one row over the limit fails the whole insert")

    target = pathlib.Path(__file__).with_name("ranks.sql")
    target.write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(LADDER)} groups, {len(rows())} nodes, longest {len(longest[1])} chars -> {target}")


if __name__ == "__main__":
    main()
