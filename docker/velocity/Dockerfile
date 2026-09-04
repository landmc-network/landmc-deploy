# Velocity, pinned to an exact build.
#
# Built here rather than pulled from a general-purpose Minecraft image: the network runs
# Velocity 4.1.1 and Paper 26.2 - versions a third-party image would have to catch up to - and
# an image that silently updates the proxy under a running network is not what "repeatable
# deployment" means.
FROM eclipse-temurin:25-jre

# Velocity 4 requires Java 25 bytecode support; the base image is what provides it.
ARG VELOCITY_VERSION=4.1.1
ARG VELOCITY_BUILD=24
ARG VELOCITY_SHA256=846411d2d0560fed0f23496ffb89681be528d2c0650ecdcf21724d2d7bd9c1ee

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends curl ca-certificates; \
    rm -rf /var/lib/apt/lists/*; \
    curl -fsSL -o /opt/velocity.jar \
        "https://fill-data.papermc.io/v1/objects/${VELOCITY_SHA256}/velocity-${VELOCITY_VERSION}-${VELOCITY_BUILD}.jar"; \
    echo "${VELOCITY_SHA256}  /opt/velocity.jar" | sha256sum -c -

# No user is created here on purpose. Everything under /server is a bind mount from the host,
# so the container has to write as whoever owns those directories - compose passes the host's
# own uid:gid. Baking a uid into the image only works until it collides with one the base image
# already uses, which is exactly what uid 1000 does on eclipse-temurin.
WORKDIR /server

EXPOSE 25565

ENV JAVA_MEMORY=1G

# Extra JVM flags, empty by default. Having a hook for them means a diagnostic flag - a GC
# log, a packet-decode trace - is an environment variable on one service rather than an edit to
# this file and a rebuild of the image on a server that is currently running.
ENV JAVA_OPTS=""
ENTRYPOINT ["sh", "-c", "exec java -Xms${JAVA_MEMORY} -Xmx${JAVA_MEMORY} -XX:+UseG1GC ${JAVA_OPTS} -jar /opt/velocity.jar"]
