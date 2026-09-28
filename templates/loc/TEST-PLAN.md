# Plan testów

Umowa o testach projektu, około jednej strony. Zmienia się tylko przez kamień
planu (`loc-planning`), nigdy przy okazji. `loc-qa` zgłasza luki, ale go nie
edytuje. Bez historii rund i bez pokrycia wymagań.

## (a) Warstwy i komendy

<!-- Jedna linia na warstwę: nazwa, komenda, bramka albo raport, szybka czy pełna.
Warstwa „bramka” musi przejść, żeby plan był zatwierdzony; „raport” tylko informuje.
Warstwy wyłącznie w CI oznacz „tylko CI” — nie wchodzą do werdyktu.
Przykład:
| Warstwa | Komenda | Rodzaj | Kiedy |
|---|---|---|---|
| jednostkowe | `python -m pytest tests/unit -q` | bramka | szybkie, po każdym kamieniu |
| integracyjne | `python -m pytest tests/integration -q` | bramka | pełne, w `loc-qa` |
| zachowanie modelu | `python evals/run.py` | raport | na żądanie |
-->

## (b) Co się zmieniło → co rozszerzyć

<!-- Tylko testy. Dokumenty należą do `## Project-specific workflow` w `CLAUDE.md`.
Przykład:
| Zmiana w produkcie | Co rozszerzyć |
|---|---|
| nowy endpoint API | test kontraktu w `tests/api/` + wpis w `qa-api` |
| nowa opcja konfiguracji | test domyślnej i niepoprawnej wartości |
-->

## (c) Stałe macierze

<!-- Kombinacje, które każda zmiana w danym obszarze musi przejść, np. systemy × wersje. -->

## (d) Granice

<!-- Czego świadomie nie sprawdzimy automatycznie i dlaczego. -->

## (e) Jak tu wygląda test

<!-- 3–6 linii konwencji:
- framework i styl asercji;
- gdzie kłaść testy (katalog, nazwy plików);
- fikstury: w gicie tylko pisane ręcznie; dane nagrane tylko w katalogu ignorowanym;
- znacznik znanego defektu (np. `@pytest.mark.xfail(strict=True, reason="loc/inbox/NNN-…")`);
- katalog danych nagranych.
-->
