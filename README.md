# LandMC Deploy

Cała sieć LandMC jako jeden stack Dockera: proxy, lobby, Redis i MariaDB.

To repozytorium nie zawiera logiki pluginów — te są w `landmc-proxy` i `landmc-lobby`. Tutaj
jest to, co decyduje, *jak* i *gdzie* one działają.

## Co się uruchamia

| Usługa | Obraz | Widoczna z zewnątrz |
|---|---|---|
| `proxy` | Velocity 4.1.1 (build 24), przypięty | tak, port `PROXY_PORT` |
| `lobby` | Paper 26.2 (build 121), przypięty | nie |
| `redis` | `redis:8-alpine` | nie |
| `mariadb` | `mariadb:11.4` | nie |

Tylko proxy ma opublikowany port. Backend osiągalny z internetu to backend, który omija proxy —
a przy włączonym `MODERN` forwardingu wystarczy to, żeby wejść jako dowolny gracz.

Obrazy Velocity i Paper budujemy sami, z przypiętym buildem i sprawdzaną sumą SHA-256. Gotowy
obraz, który sam się aktualizuje, potrafi podmienić serwer pod działającą siecią — a to nie
jest „powtarzalny deployment".

## Pierwsze uruchomienie

```bash
cp .env.example .env
```

Uzupełnij `.env` — hasła, `FORWARDING_SECRET` (np. `openssl rand -hex 24`), oraz `HOST_UID`
i `HOST_GID` (`id -u`, `id -g`). Potem:

```bash
./scripts/setup.sh
```

```bash
./scripts/fetch-plugins.sh
```

```bash
docker compose up -d
```

`setup.sh` renderuje wszystko, co potrzebuje sekretu: `forwarding.secret` dla Velocity,
`paper-global.yml` dla Paper i konfiguracje pluginów z `configs/`. Jest idempotentny i zostawia
kopię `.previous` każdej konfiguracji, którą nadpisał.

`fetch-plugins.sh` bierze jary z **ostatniego zielonego builda CI** na `main`, więc na serwerze
ląduje build, który przeszedł testy, a nie to, co ktoś ostatnio skompilował u siebie. Podczas
pracy nad pluginem:

```bash
./scripts/fetch-plugins.sh --local ../landmc-proxy/build/libs/landmc-proxy.jar
```

## Konfiguracja

- `servers/proxy/velocity.toml`, `servers/lobby/server.properties` — wersjonowane, bez sekretów.
- `configs/` — te fragmenty konfiguracji pluginów, o których decyduje deployment: hosty Redisa
  i bazy, hasła, identyfikator serwera. Resztę plugin dopisuje sobie sam przy starcie.
- `.env` — sekrety. Nie trafia do repozytorium.

`velocity.toml` jest napisany pod schemat, który generuje **Velocity 4.1.1**, i to nie jest
formalność. Brakująca sekcja nie jest zgłaszana jako błąd — zostaje wypełniona wartościami,
które niekoniecznie są udokumentowanymi domyślnymi. Pominięcie `[packet-limiter]` wystarczyło,
żeby każdy gracz przechodził logowanie, a potem był po cichu rozłączany przed wejściem na
backend, bez jednej linijki w logu. Przy aktualizacji Velocity porównaj ten plik ze świeżo
wygenerowanym, zamiast zakładać, że stare klucze nadal wystarczą.

## Diagnostyka

Proxy ma wbudowany ślad logowania. W `servers/proxy/plugins/landmc-proxy/config.yml`:

```yaml
join-debug:
  enabled: true
```

Po restarcie każde wejście gracza zapisuje fazy od `PRE_LOGIN_START` do `DISCONNECT` z jednym
identyfikatorem na próbę. To jest właściwe narzędzie na „gracz nie może wejść" — dokładnie tak
znaleziono problem z `[packet-limiter]` opisany wyżej. Wyłącz, gdy skończysz: przy ruchu to
kilkanaście linii na każde wejście.

## Weryfikacja

Stack został uruchomiony w całości na czystym hoście z Dockerem 29.7 i sprawdzony realnym
połączeniem klienta protokołu Minecraft 26.2 (776):

- proxy wstaje na MariaDB (`Friends ready on MARIADB`), lobby też (`Database ready (MARIADB)`),
- gracz przechodzi przez proxy na lobby, a backend potwierdza przekazany profil
  (`UUID of player Crispi is ff20d2eb-…`) — czyli `MODERN` forwarding i wspólny sekret działają,
- Redis i MariaDB mają healthchecki, a proxy i lobby czekają na nie przed startem.

## Czego tu jeszcze nie ma

- Skyblock i kolejne backendy — dojdą jako następne usługi w `compose.yml`.
- Kopie zapasowe bazy i światów.
- Osobne środowisko stagingowe.
