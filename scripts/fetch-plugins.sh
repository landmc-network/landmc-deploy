#!/usr/bin/env bash
# Puts the plugin jars where the containers expect them.
#
# By default it takes the jar each project's CI built for the newest green commit on main, so
# what runs here is a build that passed its tests rather than whatever somebody last compiled
# locally. Pass --local to use a working copy instead, which is what you want while developing.
#
# Usage:
#   scripts/fetch-plugins.sh                      # newest green CI build of every project
#   scripts/fetch-plugins.sh proxy                # just the proxy
#   scripts/fetch-plugins.sh --local ../landmc-proxy/build/libs/landmc-proxy.jar
set -euo pipefail

cd "$(dirname "$0")/.."

readonly ORG=landmc-network

# project -> the server directory its jar belongs in
target_dir() {
    case $1 in
        proxy) echo servers/proxy/plugins ;;
        lobby) echo servers/lobby/plugins ;;
        *) echo "Unknown project: $1" >&2; return 1 ;;
    esac
}

install_jar() {
    local project=$1 jar=$2 directory
    directory=$(target_dir "$project")
    mkdir -p "$directory"

    local destination="$directory/landmc-$project.jar"
    # Kept next to the jar so a bad deploy can be undone without another download.
    if [ -f "$destination" ]; then
        cp "$destination" "$destination.previous"
    fi

    cp "$jar" "$destination"
    echo "$project: $(sha256sum "$destination" | cut -c1-16)  $destination"
}

fetch_from_ci() {
    local project=$1 repository="$ORG/landmc-$project"

    if ! command -v gh > /dev/null; then
        echo "The GitHub CLI is not installed; use --local, or install gh and run: gh auth login" >&2
        return 1
    fi

    local run
    run=$(gh run list --repo "$repository" --workflow Build --branch main \
        --status success --limit 1 --json databaseId --jq '.[0].databaseId')

    if [ -z "$run" ] || [ "$run" = "null" ]; then
        echo "$project: no successful build on main to take a jar from" >&2
        return 1
    fi

    local workspace
    workspace=$(mktemp -d)
    trap 'rm -rf "$workspace"' RETURN

    gh run download "$run" --repo "$repository" --name "landmc-$project" --dir "$workspace"

    local jar
    jar=$(find "$workspace" -name '*.jar' -type f | head -1)
    if [ -z "$jar" ]; then
        echo "$project: build $run has no jar attached" >&2
        return 1
    fi

    echo "$project: from build $run of $repository"
    install_jar "$project" "$jar"
}

main() {
    if [ "${1:-}" = "--local" ]; then
        shift
        if [ $# -eq 0 ]; then
            echo "--local needs at least one jar path" >&2
            exit 1
        fi
        for jar in "$@"; do
            if [ ! -f "$jar" ]; then
                echo "No such jar: $jar" >&2
                exit 1
            fi
            case "$(basename "$jar")" in
                landmc-proxy*) install_jar proxy "$jar" ;;
                landmc-lobby*) install_jar lobby "$jar" ;;
                *) echo "Cannot tell which server $jar belongs to" >&2; exit 1 ;;
            esac
        done
        return
    fi

    local projects=("$@")
    if [ ${#projects[@]} -eq 0 ]; then
        projects=(proxy lobby)
    fi

    local failed=0
    for project in "${projects[@]}"; do
        fetch_from_ci "$project" || failed=1
    done
    return $failed
}

main "$@"
echo "Done. Restart what you changed: docker compose restart proxy lobby"
