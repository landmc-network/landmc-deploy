# NanoLimbo: the server a player sits on before they have logged in.
#
# It has no world, no chunks and no plugins - which is the entire point. A player who has not
# authenticated cannot be on the lobby, because every listener there would otherwise have to be
# audited for what it does with an unauthenticated connection.
#
# Pinned and checksummed like the other two images. A limbo that silently updated itself would
# be a login screen changing under a running network, and 1.13.0 is the release that added
# support for protocol 776.
FROM eclipse-temurin:25-jre

ARG NANOLIMBO_VERSION=1.13.0
ARG NANOLIMBO_SHA256=884dc3d4941fb0964dfd348cebc66afb692b156a213cc980d6f47f02441432cf

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends curl ca-certificates; \
    rm -rf /var/lib/apt/lists/*; \
    curl -fsSL -o /opt/limbo.jar \
        "https://github.com/Nan1t/NanoLimbo/releases/download/v${NANOLIMBO_VERSION}/NanoLimbo.jar"; \
    echo "${NANOLIMBO_SHA256}  /opt/limbo.jar" | sha256sum -c -

# As in the other two images, no user is created: everything under /server is a bind mount and
# compose passes the host's own uid:gid.
WORKDIR /server

EXPOSE 25566

# 128 MB is generous for a server that holds connections and renders nothing.
ENV JAVA_MEMORY=128M

# Extra JVM flags, empty by default. See the note in docker/velocity.
ENV JAVA_OPTS=""
ENTRYPOINT ["sh", "-c", "exec java -Xms${JAVA_MEMORY} -Xmx${JAVA_MEMORY} ${JAVA_OPTS} -jar /opt/limbo.jar"]
