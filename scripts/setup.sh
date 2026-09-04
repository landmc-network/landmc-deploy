#!/usr/bin/env bash
# Prepares the working tree for a start: renders everything that needs a secret, and puts the
# forwarding secret where each side expects it.
#
# Idempotent, and safe to run against a live checkout - it only writes generated files, and
# keeps a .previous copy of any plugin config it replaces.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    echo "No .env. Copy .env.example to .env and fill it in first." >&2
    exit 1
fi

set -a
# shellcheck disable=SC1091
. ./.env
set +a

require() {
    local name=$1
    if [ -z "${!name:-}" ]; then
        echo "$name is empty in .env" >&2
        exit 1
    fi
}

require FORWARDING_SECRET
require REDIS_PASSWORD
require MARIADB_PASSWORD

# envsubst is told exactly which names to replace, so a $ anywhere else in a config - a
# MiniMessage tag, a password, a regex - survives untouched.
render_to() {
    local template=$1 output=$2
    FORWARDING_SECRET="$FORWARDING_SECRET" \
    REDIS_PASSWORD="$REDIS_PASSWORD" \
    MARIADB_USER="${MARIADB_USER:-landmc}" \
    MARIADB_PASSWORD="$MARIADB_PASSWORD" \
    MARIADB_DATABASE="${MARIADB_DATABASE:-landmc}" \
        envsubst '$FORWARDING_SECRET $REDIS_PASSWORD $MARIADB_USER $MARIADB_PASSWORD $MARIADB_DATABASE' \
        < "$template" > "$output"
    chmod 600 "$output"
    echo "rendered $output"
}

# Velocity reads the secret from a file, which keeps it out of velocity.toml.
# Both the proxy and the limbo verify the same secret: the limbo is a real server on the
# network, and one that accepted unauthenticated connections would be a way around the proxy.
for target in servers/proxy servers/limbo; do
    mkdir -p "$target"
    printf '%s' "$FORWARDING_SECRET" > "$target/forwarding.secret"
    chmod 600 "$target/forwarding.secret"
    echo "wrote $target/forwarding.secret"
done

# Paper wants the same secret inside its own config. That file belongs to Paper - it carries a
# schema version and Paper migrates it between releases - so the two keys the deployment owns
# are edited in place rather than the whole file being shipped from here.
python3 scripts/paper-proxy-config.py servers/lobby/config/paper-global.yml

# The lobby is a build that is pasted in, not terrain, so its world is generated empty.
python3 scripts/bukkit-generator.py servers/lobby/bukkit.yml lobby landmc-lobby

while IFS= read -r template; do
    render_to "$template" "${template%.template}"
done < <(find servers -name '*.template' -type f)

# Plugin configuration is versioned in configs/ and copied into place, so a fresh checkout
# produces a network that talks to the right Redis and database without anyone editing YAML by
# hand. The plugin fills in every other field on first start and owns the file from then on,
# which is why the previous copy is kept rather than merged.
#
# Copied verbatim, not rendered: the ${LANDMC_*} names in these files are resolved by the
# plugin itself from the container's environment. Expanding them here would write the database
# password into every plugin's config.yml, which is what the placeholders exist to avoid.
install_plugin_configs() {
    local source server template destination
    for source in configs/*/; do
        server=$(basename "$source")
        while IFS= read -r template; do
            destination="servers/$server/plugins/${template#configs/"$server"/}"
            destination=${destination%.template}
            mkdir -p "$(dirname "$destination")"
            if [ -f "$destination" ]; then
                cp "$destination" "$destination.previous"
            fi
            cp "$template" "$destination"
            chmod 600 "$destination"
            echo "installed $destination"
        done < <(find "$source" -name '*.template' -type f)
    done
}

install_plugin_configs

# The EULA is the operator's to accept; this only records a decision already made in .env.
if [ "${ACCEPT_EULA:-false}" = "true" ]; then
    echo "eula=true" > servers/lobby/eula.txt
    echo "wrote servers/lobby/eula.txt"
else
    echo "ACCEPT_EULA is not true in .env - Paper will refuse to start until it is." >&2
fi

echo
echo "Ready. Fetch the plugin jars with scripts/fetch-plugins.sh, then: docker compose up -d"
