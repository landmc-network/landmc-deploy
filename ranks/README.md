# Rangi

Drabina rang sieci LandMC — te same rangi, w tej samej kolejności i w tych samych kolorach co
na poprzedniej wersji serwera.

| Ranga | Prefiks | Co dochodzi |
|---|---|---|
| `default` | — | komendy gracza: `/msg`, `/znajomi`, `/serwery`, `/live`, `/helpop` |
| `vip` | żółty **VIP** | odstęp na czacie 2 s zamiast 5 s |
| `svip` | fioletowy **SVIP** | kolory i emotki w wiadomościach |
| `szefuncio` | tęczowy **SZEFUNCIO** | — |
| `sponsor` | zielony **SPONSOR** | — |
| `miniyt` / `yt` | złoty **MiniYT** / **YT** | — |
| `buildteam` | ciemnoturkusowy **BUILD TEAM** | brak odstępu na czacie, `/setspawn` |
| `helper` | niebieski **POMOCNIK** | odnośniki na czacie, `/helpop`, kick, warn, historia kar |
| `mod` | ciemnozielony **MODERATOR** | bany, `/socialspy`, czat administracji |
| `admin` | czerwony **ADMIN** | maintenance, `/setrank`, ekonomia, auth, antyproxy, vouchery |
| `manager` | czerwony **MANAGER** | to co admin |
| `owner` / `developer` | czerwony **WŁAŚCICIEL** / **DEVELOPER** | `*` |

**Każda ranga dziedziczy po niższej.** Tak działało `hasRank()` na starym serwerze — porównywało
indeksy, więc moderator miał wszystko, co VIP. Dzięki temu nic nie jest wypisane dwa razy.

Uprawnienia zamiast porównywania indeksów to jedyna zmiana względem oryginału: to, co dana ranga
może, da się teraz zmienić bez przebudowywania wtyczki.

## Jak to wgrać

`ranks.sql` pisze wprost do tabel LuckPermsa, bo ani proxy, ani backendy nie mają konsoli
osiągalnej z zewnątrz. To dokładnie te wiersze, które zapisałyby `/lp creategroup`,
`/lp group <nazwa> meta setprefix` i `/lp group <nazwa> permission set`.

```bash
docker exec -i <kontener-mariadb> sh -c 'mariadb -ulandmc -p"$MARIADB_PASSWORD" landmc' < ranks.sql
```

Potem restart proxy i backendów, żeby LuckPerms wczytał zmiany (albo `/lp sync` z konsoli).

Plik można puszczać wielokrotnie: grupy dodają się tylko gdy ich nie ma, a węzły są nadpisywane
w całości. Żeby coś zmienić, edytuje się `generate-ranks.py`, uruchamia go i wgrywa wynik —
nie edytuje się `ranks.sql` ręcznie.

Uprawnienia **graczy** nie są tu ruszane. Plik dotyczy wyłącznie grup.
