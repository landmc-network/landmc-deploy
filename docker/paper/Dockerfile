# Paper, pinned to an exact build, for the same reasons as the Velocity image.
FROM eclipse-temurin:25-jre

ARG PAPER_VERSION=26.2
ARG PAPER_BUILD=121
ARG PAPER_SHA256=0de30efb024bc8b83c9c7d507d11802897ad8056b6110ec09fe1a91d126ccb54

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends curl ca-certificates; \
    rm -rf /var/lib/apt/lists/*; \
    curl -fsSL -o /opt/paper.jar \
        "https://fill-data.papermc.io/v1/objects/${PAPER_SHA256}/paper-${PAPER_VERSION}-${PAPER_BUILD}.jar"; \
    echo "${PAPER_SHA256}  /opt/paper.jar" | sha256sum -c -

# No user is created here on purpose. Everything under /server is a bind mount from the host,
# so the container has to write as whoever owns those directories - compose passes the host's
# own uid:gid. Baking a uid into the image only works until it collides with one the base image
# already uses, which is exactly what uid 1000 does on eclipse-temurin.
WORKDIR /server

EXPOSE 25565

# Extra JVM flags, empty by default. See the note in docker/velocity.
ENV JAVA_OPTS=""

# Aikar's flags, minus the ones that only make sense above 12 GB. The lobby is a small heap and
# a long pause there is as visible as one on a game server.
ENV JAVA_MEMORY=2G
ENTRYPOINT ["sh", "-c", "exec java -Xms${JAVA_MEMORY} -Xmx${JAVA_MEMORY} \
    -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 \
    -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch \
    -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:G1MixedGCLiveThresholdPercent=90 \
    -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem \
    -XX:MaxTenuringThreshold=1 -Dusing.aikars.flags=https://mcflags.emc.gs ${JAVA_OPTS} \
    -jar /opt/paper.jar --nogui"]
