-- The LandMC rank ladder.
--
-- Generated from the old server's UserRank enum: the same ranks in the same order,
-- with the colours it used. What each one may do is expressed as permissions rather
-- than as a comparison of indexes, so it can be changed without a build.
--
-- Each rank inherits the one below it, which is what made hasRank() work there: a
-- moderator has everything a VIP has, and nothing has to be listed twice.
--
-- Safe to run again. Groups are inserted only when missing, and every node this file
-- owns is replaced, so editing the list here and re-running is the way to change it.

INSERT IGNORE INTO luckperms_groups (name) VALUES ('default'), ('vip'), ('svip'), ('szefuncio'), ('sponsor'), ('miniyt'), ('yt'), ('buildteam'), ('helper'), ('mod'), ('admin'), ('manager'), ('owner'), ('developer');

-- Everything below is rewritten, so a node removed from this file goes away.
DELETE FROM luckperms_group_permissions WHERE name IN ('default', 'vip', 'svip', 'szefuncio', 'sponsor', 'miniyt', 'yt', 'buildteam', 'helper', 'mod', 'admin', 'manager', 'owner', 'developer');

INSERT INTO luckperms_group_permissions
    (name, permission, value, server, world, expiry, contexts)
VALUES
    ('default', 'landmc.command.friend', 1, 'global', 'global', 0, '{}'),
    ('default', 'landmc.command.msg', 1, 'global', 'global', 0, '{}'),
    ('default', 'landmc.command.ignore', 1, 'global', 'global', 0, '{}'),
    ('default', 'landmc.command.server', 1, 'global', 'global', 0, '{}'),
    ('default', 'landmc.command.live', 1, 'global', 'global', 0, '{}'),
    ('default', 'landmc.command.helpop', 1, 'global', 'global', 0, '{}'),
    ('vip', 'landmc.chat.cooldown.short', 1, 'global', 'global', 0, '{}'),
    ('vip', 'group.default', 1, 'global', 'global', 0, '{}'),
    ('vip', 'weight.10', 1, 'global', 'global', 0, '{}'),
    ('vip', 'prefix.10.<yellow><bold>VIP</bold> ', 1, 'global', 'global', 0, '{}'),
    ('svip', 'landmc.chat.colors', 1, 'global', 'global', 0, '{}'),
    ('svip', 'group.vip', 1, 'global', 'global', 0, '{}'),
    ('svip', 'weight.20', 1, 'global', 'global', 0, '{}'),
    ('svip', 'prefix.20.<light_purple><bold>SVIP</bold> ', 1, 'global', 'global', 0, '{}'),
    ('szefuncio', 'group.svip', 1, 'global', 'global', 0, '{}'),
    ('szefuncio', 'weight.30', 1, 'global', 'global', 0, '{}'),
    ('szefuncio', 'prefix.30.<b><#FF5555>S<#FFAA00>Z<#FFFF55>E<#55FF55>F<#55FFFF>U<#00AAAA>N<#FF55FF>C<#FF5555>I<#FFAA00>O</b><white> ', 1, 'global', 'global', 0, '{}'),
    ('sponsor', 'group.szefuncio', 1, 'global', 'global', 0, '{}'),
    ('sponsor', 'weight.40', 1, 'global', 'global', 0, '{}'),
    ('sponsor', 'prefix.40.<green><bold>SPONSOR</bold> ', 1, 'global', 'global', 0, '{}'),
    ('miniyt', 'group.sponsor', 1, 'global', 'global', 0, '{}'),
    ('miniyt', 'weight.50', 1, 'global', 'global', 0, '{}'),
    ('miniyt', 'prefix.50.<gold><bold>MiniYT</bold> ', 1, 'global', 'global', 0, '{}'),
    ('yt', 'group.miniyt', 1, 'global', 'global', 0, '{}'),
    ('yt', 'weight.60', 1, 'global', 'global', 0, '{}'),
    ('yt', 'prefix.60.<gold><bold>YT</bold> ', 1, 'global', 'global', 0, '{}'),
    ('buildteam', 'landmc.chat.cooldown.bypass', 1, 'global', 'global', 0, '{}'),
    ('buildteam', 'landmc.cooldown.bypass', 1, 'global', 'global', 0, '{}'),
    ('buildteam', 'landmc.command.setspawn', 1, 'global', 'global', 0, '{}'),
    ('buildteam', 'group.yt', 1, 'global', 'global', 0, '{}'),
    ('buildteam', 'weight.70', 1, 'global', 'global', 0, '{}'),
    ('buildteam', 'prefix.70.<dark_aqua><bold>BUILD TEAM</bold> ', 1, 'global', 'global', 0, '{}'),
    ('helper', 'landmc.chat.links', 1, 'global', 'global', 0, '{}'),
    ('helper', 'landmc.command.helpop.receive', 1, 'global', 'global', 0, '{}'),
    ('helper', 'landmc.command.helpop.nodelay', 1, 'global', 'global', 0, '{}'),
    ('helper', 'landmc.punishments.kick', 1, 'global', 'global', 0, '{}'),
    ('helper', 'landmc.punishments.warn', 1, 'global', 'global', 0, '{}'),
    ('helper', 'landmc.punishments.history', 1, 'global', 'global', 0, '{}'),
    ('helper', 'landmc.punishments.notify', 1, 'global', 'global', 0, '{}'),
    ('helper', 'group.buildteam', 1, 'global', 'global', 0, '{}'),
    ('helper', 'weight.80', 1, 'global', 'global', 0, '{}'),
    ('helper', 'prefix.80.<blue><bold>POMOCNIK</bold> ', 1, 'global', 'global', 0, '{}'),
    ('mod', 'landmc.punishments.ban', 1, 'global', 'global', 0, '{}'),
    ('mod', 'landmc.punishments.tempban', 1, 'global', 'global', 0, '{}'),
    ('mod', 'landmc.punishments.banip', 1, 'global', 'global', 0, '{}'),
    ('mod', 'landmc.punishments.unban', 1, 'global', 'global', 0, '{}'),
    ('mod', 'landmc.command.socialspy', 1, 'global', 'global', 0, '{}'),
    ('mod', 'landmc.command.adminchat', 1, 'global', 'global', 0, '{}'),
    ('mod', 'landmc.adminchat.spy', 1, 'global', 'global', 0, '{}'),
    ('mod', 'landmc.economy.balance.others', 1, 'global', 'global', 0, '{}'),
    ('mod', 'group.helper', 1, 'global', 'global', 0, '{}'),
    ('mod', 'weight.90', 1, 'global', 'global', 0, '{}'),
    ('mod', 'prefix.90.<dark_green><bold>MODERATOR</bold> ', 1, 'global', 'global', 0, '{}'),
    ('admin', 'landmc.command.maintenance', 1, 'global', 'global', 0, '{}'),
    ('admin', 'landmc.maintenance.bypass', 1, 'global', 'global', 0, '{}'),
    ('admin', 'landmc.command.setrank', 1, 'global', 'global', 0, '{}'),
    ('admin', 'landmc.command.broadcast', 1, 'global', 'global', 0, '{}'),
    ('admin', 'landmc.command.send', 1, 'global', 'global', 0, '{}'),
    ('admin', 'landmc.command.live.admin', 1, 'global', 'global', 0, '{}'),
    ('admin', 'landmc.economy.admin', 1, 'global', 'global', 0, '{}'),
    ('admin', 'landmc.auth.admin', 1, 'global', 'global', 0, '{}'),
    ('admin', 'landmc.antiproxy.admin', 1, 'global', 'global', 0, '{}'),
    ('admin', 'landmc.voucher.generate', 1, 'global', 'global', 0, '{}'),
    ('admin', 'group.mod', 1, 'global', 'global', 0, '{}'),
    ('admin', 'weight.100', 1, 'global', 'global', 0, '{}'),
    ('admin', 'prefix.100.<red><bold>ADMIN</bold> ', 1, 'global', 'global', 0, '{}'),
    ('manager', 'group.admin', 1, 'global', 'global', 0, '{}'),
    ('manager', 'weight.110', 1, 'global', 'global', 0, '{}'),
    ('manager', 'prefix.110.<red><bold>MANAGER</bold> ', 1, 'global', 'global', 0, '{}'),
    ('owner', '*', 1, 'global', 'global', 0, '{}'),
    ('owner', 'group.manager', 1, 'global', 'global', 0, '{}'),
    ('owner', 'weight.120', 1, 'global', 'global', 0, '{}'),
    ('owner', 'prefix.120.<red><bold>WŁAŚCICIEL</bold> ', 1, 'global', 'global', 0, '{}'),
    ('developer', '*', 1, 'global', 'global', 0, '{}'),
    ('developer', 'group.manager', 1, 'global', 'global', 0, '{}'),
    ('developer', 'weight.130', 1, 'global', 'global', 0, '{}'),
    ('developer', 'prefix.130.<red><bold>DEVELOPER</bold> ', 1, 'global', 'global', 0, '{}');
