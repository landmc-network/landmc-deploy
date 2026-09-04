#!/usr/bin/env bash
# Puts the plugin jars where the containers expect them.
#
# By default it takes the jar each project's CI built for the newest green commit on main, so
# what runs here is a build that passed its tests rather than whatever somebody last compiled
# locally. Pass --local to use a working copy instead, which is what you want while developing.
#
# Usage:
#   scripts/fetch-plugins.sh                       # newest green CI build of everything
#   scripts/fetch-plugins.sh landmc-vanish         # only that repository's jars
#   scripts/fetch-plugins.sh --local ../landmc-proxy/build/libs/landmc-proxy.jar
set -euo pipefail

cd "$(dirname "$0")/.."

readonly ORG=landmc-network

# Each entry is "repository|artifact|destination". A repository can produce more than one
# artifact: vanish ships a jar for each side of the network, and both have to come from the same
# build, or the two halves can disagree about the shape of a message.
readonly ARTIFACTS=(
    "landmc-proxy|landmc-proxy|servers/proxy/plugins/landmc-proxy.jar"
    "landmc-lobby|landmc-lobby|servers/lobby/plugins/landmc-lobby.jar"
    "landmc-antiproxy|landmc-antiproxy|servers/proxy/plugins/landmc-antiproxy.jar"
    "landmc-punishments|landmc-punishments|servers/proxy/plugins/landmc-punishments.jar"
    "landmc-vanish|landmc-vanish-proxy|servers/proxy/plugins/landmc-vanish-proxy.jar"
    "landmc-vanish|landmc-vanish-paper|servers/lobby/plugins/landmc-vanish-paper.jar"
)

install_jar() {
    local jar=$1 destination=$2
    mkdir -p "$(dirname "$destination")"

    # Kept next to the jar so a bad deploy can be undone without another download.
    if [ -f "$destination" ]; then
        cp "$destination" "$destination.previous"
    fi

    cp "$jar" "$destination"
    echo "  $(sha256sum "$destination" | cut -c1-16)  $destination"
}

fetch_from_ci() {
    local repository_name=$1 artifact=$2 destination=$3
    local repository="$ORG/$repository_name"

    local run
    run=$(gh run list --repo "$repository" --workflow Build --branch main \
        --status success --limit 1 --json databaseId --jq '.[0].databaseId')

    if [ -z "$run" ] || [ "$run" = "null" ]; then
        echo "$artifact: no successful build on main to take a jar from" >&2
        return 1
    fi

    local workspace
    workspace=$(mktemp -d)
    trap 'rm -rf "$workspace"' RETURN

    gh run download "$run" --repo "$repository" --name "$artifact" --dir "$workspace"

    local jar
    jar=$(find "$workspace" -name '*.jar' -type f | head -1)
    if [ -z "$jar" ]; then
        echo "$artifact: build $run has no jar attached" >&2
        return 1
    fi

    echo "$artifact: from build $run of $repository"
    install_jar "$jar" "$destination"
}

contains() {
    local needle=$1
    shift
    local candidate
    for candidate in "$@"; do
        if [ "$candidate" = "$needle" ]; then
            return 0
        fi
    done
    return 1
}

install_local() {
    local jar entry name destination

    for jar in "$@"; do
        if [ ! -f "$jar" ]; then
            echo "No such jar: $jar" >&2
            exit 1
        fi

        name=$(basename "$jar")
        destination=""
        for entry in "${ARTIFACTS[@]}"; do
            if [ "$name" = "$(basename "${entry##*|}")" ]; then
                destination=${entry##*|}
                break
            fi
        done

        if [ -z "$destination" ]; then
            echo "Cannot tell where $name belongs. Known jars:" >&2
            for entry in "${ARTIFACTS[@]}"; do
                echo "  $(basename "${entry##*|}")" >&2
            done
            exit 1
        fi

        install_jar "$jar" "$destination"
    done
}

main() {
    if [ "${1:-}" = "--local" ]; then
        shift
        if [ $# -eq 0 ]; then
            echo "--local needs at least one jar path" >&2
            exit 1
        fi
        install_local "$@"
        return
    fi

    if ! command -v gh > /dev/null; then
        echo "The GitHub CLI is not installed; use --local, or install gh and run: gh auth login" >&2
        exit 1
    fi

    local wanted=("$@")
    local failed=0
    local entry repository_name rest artifact destination

    for entry in "${ARTIFACTS[@]}"; do
        repository_name=${entry%%|*}
        rest=${entry#*|}
        artifact=${rest%%|*}
        destination=${rest#*|}

        if [ ${#wanted[@]} -gt 0 ] \
                && ! contains "$artifact" "${wanted[@]}" \
                && ! contains "$repository_name" "${wanted[@]}"; then
            continue
        fi

        fetch_from_ci "$repository_name" "$artifact" "$destination" || failed=1
    done

    return $failed
}

main "$@"
echo "Done. Restart what you changed: docker compose restart proxy lobby"
