# LandMC Deploy

Konfiguracje, skrypty i szablony infrastruktury dla sieci LandMC.

To repozytorium nie zawiera logiki pluginów. Służy do utrzymania środowisk, instancji i procesu wdrażania.

## Odpowiedzialność

- konfiguracje proxy,
- konfiguracje Paper,
- Docker Compose,
- zmienne środowiskowe,
- szablony nowych instancji,
- skrypty startowe,
- dokumentacja deploymentu,
- lokalne środowisko developerskie.

## Proponowany układ

```text
landmc-deploy/
  docker/
  servers/
    proxy/
    lobby/
    skyblock-1/
  configs/
  scripts/
  docs/
```

## Zasady

- Sekrety nie powinny trafiać do repozytorium.
- Konfiguracje publiczne i szablony powinny być wersjonowane.
- Dane środowiskowe powinny być trzymane w `.env` lub systemie secretów.
- Deployment powinien być powtarzalny lokalnie i na serwerze.

## Technologie

- Docker
- Docker Compose
- Paper
- Velocity
- PostgreSQL albo MariaDB
- Redis

## Status

Projekt w przygotowaniu.