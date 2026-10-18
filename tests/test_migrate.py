"""Tests for scripts/migrate.py: a format 1 (Polish) `loc/` becomes format 2 (English)."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = ROOT / "tmp" / "scratch" / "tests"

CLAUDE = """# demo

## Commands
- Tests: `python -m unittest`

## Invariants
- greet never raises

## Project-specific workflow
- none
"""

PRD = """# PRD — demo

Po co jest projekt.

## Cel
Powitanie w wybranym języku.

## Rdzeń idei
- **Prosto.** Jeden plik.

## Scenariusze
1. Użytkownik wita gościa po polsku.

## Kierunki
### Eksport
→ przekazane do loc/inbox/done/002-plan-eksport.md
"""

PATTERNS = """# Wzorce

## ✅ Działa
### Testy z katalogu głównego
**Kiedy stosować:** uruchamianie testów
`python -m unittest`

## ❌ Nie działa

## ⚠️ Pułapki
"""

MEMORY = """# Dziennik

Co zrobiono, najnowsze na górze.

<!-- index:start -->
| Data | Typ | Temat | Linia |
|---|---|---|---|
| 2026-10-16 12:00 | Planowanie | Plan powitań | 12 |
| 2026-10-15 10:00 | Przegląd | Przegląd eksportu | 15 |
<!-- index:end -->

## 2026-10-16 12:00 — [Planowanie] Plan powitań
Zaplanowano powitania. Szczegóły: loc/inbox/006-plan-powitania.md

## 2026-10-15 10:00 — [Przegląd] Przegląd eksportu
Przejrzano eksport. Szczegóły: loc/inbox/done/003-przeglad-eksport.md
"""

TEST_PLAN = """# Plan testów

## (a) Warstwy i komendy
| Warstwa | Komenda | Rodzaj | Kiedy |
|---|---|---|---|
| jednostkowe | `python -m unittest` | bramka | szybkie |

## (b) Co się zmieniło → co rozszerzyć

## (c) Stałe macierze

## (d) Granice

## (e) Jak tu wygląda test
- `unittest`, testy w `test_*.py`.
"""

DONE_PLAN = """# 002 — Eksport

**Typ:** plan
**Status:** wykonane 2026-10-15
**Utworzono:** 2026-10-14 09:00
**Źródło:** loc/inbox/done/003-przeglad-eksport.md

## Cel
Eksport działa.

## Rozstrzygnięcie
Wykonano, commit abc1234.
"""

REVIEW = """# 003 — Przegląd eksportu

**Typ:** przeglad
**Status:** zamknięte
**Utworzono:** 2026-10-14 08:00
**Źródło:** HEAD

## Zakres
app.py

## Uwagi
- **[średni]** `app.py:3` — brak obsługi pustej nazwy

## Rozstrzygnięcie
→ loc/inbox/done/002-plan-eksport.md
"""

BRAINSTORM = """# 001 — Powitania

**Typ:** brainstorm
**Status:** otwarte
**Utworzono:** 2026-10-13 10:00
**Źródło:** rozmowa

## Temat
Powitania w kilku językach.

## Notatki
Użytkownik chce polskiego.

## Decyzje
- B-01 — parametr `lang`, bo prościej

## Otwarte

## Rozstrzygnięcie
<puste do czasu obsłużenia: który plan z tego powstał>
"""

DEFERRED = """# 004 — Normalizacja języka

**Typ:** odlozone
**Status:** otwarte
**Utworzono:** 2026-10-16 11:00
**Źródło:** loc/inbox/006-plan-powitania.md

## Co odłożono
Kod języka nie jest normalizowany.

## Dlaczego nie teraz
Poza celem planu.

## Kiedy wrócić
Przy następnym planie.

## Rozstrzygnięcie
<puste do czasu obsłużenia>
"""

STUCK = """# 005 — powitania — utknięte bramki

**Typ:** utknelo
**Kategoria:** nieblokująca
**Status:** otwarte
**Utworzono:** 2026-10-16 12:30
**Źródło:** loc/inbox/006-plan-powitania.md

## M1 proof

### Rundy
#### Runda 1
błąd
#### Runda 2
błąd
#### Runda 3
błąd

### Co zostało
- `app.py:3` — pusta nazwa

### Co zrobiono dalej
Praca poszła dalej.

## Rozstrzygnięcie
<puste do czasu decyzji użytkownika>
"""

QUESTION = """# 007 — Kropka czy wykrzyknik

**Typ:** pytanie
**Status:** otwarte
**Utworzono:** 2026-10-16 13:00
**Źródło:** loc/inbox/006-plan-powitania.md

## Pytanie
Czy powitanie kończy się kropką?

## Kontekst
Dziś `Cześć, Ann`.

## Warianty
- **A (rekomendowany)** — kropka, bez kosztu
- **B** — wykrzyknik, bez kosztu

## Tymczasowo
A.

## Gdzie wystąpiło
- 2026-10-16 — plan 006 M1

## Rozstrzygnięcie
<puste do czasu odpowiedzi>
"""

PLAN = """# 006 — Powitania

**Typ:** plan
**Status:** otwarte
**Utworzono:** 2026-10-16 11:30
**Źródło:** loc/inbox/done/001-brainstorm-powitania.md

## Cel
Funkcja `greet` wita po polsku i po angielsku.

## Czego nie robimy
- Innych języków.

## Nie bronimy przed
- brak

## Kontekst z kodu
- `app.py:1` — funkcja `greet`

## Kamienie milowe

### M1 — zestaw testów
Zestaw testów z jednym testem dymnym i plikiem loc/TEST-PLAN.md.
**Bez testów:** pierwszy kamień tworzy zestaw
**Wykonawca:** auto
**Dowód:** `python -m unittest` → `OK`

### M2 — język powitania
Parametr `lang`.
**Kryteria:**
- K1: `greet("Ann", "pl")` zwraca `"Cześć, Ann"` → `test_app.py::test_polish`
- K2 (zachowanie): nieznany język daje powitanie po angielsku → `test_app.py::test_unknown`
**Wykonawca:** auto
**Dowód:** `python -m unittest test_app` → `OK`

### M3 — wygląd
Kolor tekstu.
**Kryteria:**
- K3: `contrast(text, background)` daje co najmniej 4.5 → `test_app.py::test_contrast`
- K4: tekst jest czytelny na telefonie → ręcznie
**Wykonawca:** użytkownik (blokujący)
**Sprawdzenie ręczne:** tekst czytelny na telefonie
**Dowód:** `python -m unittest test_app` → `OK`

## Ryzyka i decyzje
- Decyzja B-01 i pytanie loc/inbox/007-pytanie-kropka.md.

## Bramka planu
- runda 1: skan czysty

## Uwagi z przeglądów
- dość (planowanie): 003 #1 `app.py:3` — pusta nazwa daje niepełne powitanie. Powód: nikt nie podaje pustej nazwy w tym projekcie [Cel 1]
- nierealna (M1 code-review): `app.py:5` — kod języka z dużej litery. Kto to wytwarza: nikt, wołający podaje stałe

## Fragment PRD
Przeniesione z loc/PRD.md 2026-10-16.
### Powitania
Witamy po polsku.

## Rozstrzygnięcie
<puste do czasu obsłużenia: wynik wykonania, data, commit>
"""

STATE = {
    "plan": "loc/inbox/006-plan-powitania.md",
    "mode": "inline",
    "milestone": 2,
    "phase": "proof",
    "milestones": [{"id": "M1", "status": "done", "start": "abc1234", "end": "def5678"},
                   {"id": "M2", "status": "in_progress", "start": "def5678", "end": None}],
    "gates": {"M1/proof": {"rounds": 3, "passed": False, "stuck": "loc/inbox/005-utknelo-powitania.md"},
              "M1/code-review": {"rounds": 1, "passed": True, "stuck": None}},
    "deviations": [],
    "deferred": "loc/inbox/004-odlozone-normalizacja.md",
    "next_action": "Run the M2 proof",
    "updated": "2026-10-16 12:40",
}

FILES = {
    "CLAUDE.md": CLAUDE,
    "loc/PRD.md": PRD,
    "loc/PATTERNS.md": PATTERNS,
    "loc/MEMORY.md": MEMORY,
    "loc/TEST-PLAN.md": TEST_PLAN,
    "loc/inbox/done/001-brainstorm-powitania.md": BRAINSTORM,
    "loc/inbox/done/002-plan-eksport.md": DONE_PLAN,
    "loc/inbox/done/003-przeglad-eksport.md": REVIEW,
    "loc/inbox/004-odlozone-normalizacja.md": DEFERRED,
    "loc/inbox/005-utknelo-powitania.md": STUCK,
    "loc/inbox/006-plan-powitania.md": PLAN,
    "loc/inbox/007-pytanie-kropka.md": QUESTION,
    "loc/state/006.json": json.dumps(STATE, indent=2),
    "loc/state/qa-historia.log": "2026-10-15 002 model 3/3\n",
}


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args],
                          capture_output=True, text=True, encoding="utf-8")


class MigrateTest(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.project = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, self.project, True)
        (self.project / ".git").mkdir()
        for rel, text in FILES.items():
            path = self.project / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    def migrate(self) -> dict:
        result = run("migrate.py", "--project", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def read(self, rel: str) -> str:
        return (self.project / rel).read_text(encoding="utf-8")

    def snapshot(self) -> dict:
        return {p.relative_to(self.project).as_posix(): p.read_bytes()
                for p in sorted(self.project.rglob("*")) if p.is_file()}

    def test_format_1_to_2(self):
        out = self.migrate()
        self.assertEqual((out["from"], out["to"]), (1, 4))
        self.assertEqual(self.read("loc/VERSION").strip(), "4")

        inbox = sorted(p.name for p in (self.project / "loc" / "inbox").glob("*.md"))
        self.assertEqual(inbox, ["004-deferred-normalizacja.md", "005-stuck-powitania.md",
                                 "006-plan-powitania.md", "007-question-kropka.md"])
        self.assertTrue((self.project / "loc/inbox/done/003-review-eksport.md").is_file())
        self.assertTrue((self.project / "loc/state/qa-history.log").is_file())

        done_plan = self.read("loc/inbox/done/002-plan-eksport.md")
        self.assertIn("**Source:** loc/inbox/done/003-review-eksport.md", done_plan)
        self.assertIn("**Status:** done 2026-10-15", done_plan)
        self.assertIn("Eksport działa.", done_plan)  # prose stays

        plan = self.read("loc/inbox/006-plan-powitania.md")
        for marker in ("**Type:** plan", "**Status:** open", "## Goal", "## Not defended against\n- none",
                       "## Milestones", "### M1 — test suite", "**No tests:**", "- K2 (behaviour):",
                       "→ manual", "**Performer:** user (blocking)", "## Plan gate", "## Review notes",
                       "- enough (planning): 003 #1", "Reason: nikt", "- unrealistic (M1 code-review):",
                       "Who produces it: nikt", "## PRD fragment\nMoved from loc/PRD.md 2026-10-16.", "loc/inbox/007-question-kropka.md", "<empty until handled>"):
            self.assertIn(marker, plan)

        stuck = self.read("loc/inbox/005-stuck-powitania.md")
        for marker in ("**Category:** non-blocking", "### Rounds", "#### Round 3", "### What remains",
                       "### What happened next", "## Resolution"):
            self.assertIn(marker, stuck)
        deferred = self.read("loc/inbox/004-deferred-normalizacja.md")
        for marker in ("## What was deferred", "## Why not now", "## When to return"):
            self.assertIn(marker, deferred)
        question = self.read("loc/inbox/007-question-kropka.md")
        for marker in ("**Type:** question", "## Question\nCzy powitanie kończy się kropką?", "## Context",
                       "## Options", "- **A (recommended)** — kropka", "## Interim", "## Where it came up"):
            self.assertIn(marker, question)
        brainstorm = self.read("loc/inbox/done/001-brainstorm-powitania.md")
        for marker in ("**Source:** conversation", "## Topic", "## Notes", "## Decisions", "## Open"):
            self.assertIn(marker, brainstorm)
        self.assertIn("## Scope", self.read("loc/inbox/done/003-review-eksport.md"))
        self.assertIn("## Findings", self.read("loc/inbox/done/003-review-eksport.md"))

        prd = self.read("loc/PRD.md")
        for marker in ("## Goal", "## Core idea", "## Scenarios", "## Directions",
                       "→ moved to loc/inbox/done/002-plan-eksport.md"):
            self.assertIn(marker, prd)
        patterns = self.read("loc/PATTERNS.md")
        for marker in ("# Patterns", "## ✅ Works", "## ❌ Does not work", "## ⚠️ Pitfalls", "**When to use:**"):
            self.assertIn(marker, patterns)
        memory = self.read("loc/MEMORY.md")
        for marker in ("# Journal", "| Date | Type | Topic | Line |", "| Planning |", "[Planning] Plan powitań",
                       "[Review] Przegląd eksportu", "loc/inbox/done/003-review-eksport.md"):
            self.assertIn(marker, memory)
        test_plan = self.read("loc/TEST-PLAN.md")
        for marker in ("# Test plan", "## (a) Layers and commands", "## (b) What changed → what to extend",
                       "## (c) Fixed matrices", "## (d) Limits", "## (e) What a test looks like here"):
            self.assertIn(marker, test_plan)

        state = json.loads(self.read("loc/state/006.json"))
        self.assertEqual(state["gates"]["M1/proof"]["stuck"], "loc/inbox/005-stuck-powitania.md")
        self.assertEqual(state["deferred"], "loc/inbox/004-deferred-normalizacja.md")

        self.assertIn("## User language\nPolish\n", self.read("CLAUDE.md"))
        self.assertLess(self.read("CLAUDE.md").index("## User language"),
                        self.read("CLAUDE.md").index("## Project-specific workflow"))

        self.assertEqual(sorted(out["translate"]), [
            "loc/MEMORY.md", "loc/PATTERNS.md", "loc/PRD.md", "loc/TEST-PLAN.md",
            "loc/inbox/004-deferred-normalizacja.md", "loc/inbox/005-stuck-powitania.md",
            "loc/inbox/006-plan-powitania.md"])

        # A plan written before the difficulty rule keeps its name; only that is reported.
        checked = run("check_plan.py", str(self.project / "loc/inbox/006-plan-powitania.md"))
        issues = [i["problem"] for i in json.loads(checked.stdout)["issues"]]
        self.assertEqual([i for i in issues if not i.startswith("file name")], [], checked.stdout)
        checked = run("check_state.py", str(self.project / "loc/state/006.json"))
        self.assertEqual(checked.returncode, 0, checked.stdout)
        checked = run("init_project.py", "--project", str(self.project), "--check")
        self.assertEqual(json.loads(checked.stdout)["empty"]["loc/PRD.md"], [])

    def test_idempotent(self):
        self.migrate()
        before = self.snapshot()
        out = self.migrate()
        self.assertEqual((out["from"], out["to"]), (4, 4))
        self.assertEqual(out["translate"], [])
        self.assertEqual(self.snapshot(), before)

    def test_without_loc_does_nothing(self):
        shutil.rmtree(self.project / "loc")
        out = self.migrate()
        self.assertIsNone(out["from"])
        self.assertFalse((self.project / "loc").exists())


PRD_2 = """# PRD — demo

## Goal
Greet people.

## Core idea
- **Kind.** Every greeting is polite.

## Scenarios
1. The user types a name and sees a greeting.

## Directions
### Export
Export greetings.
"""


class DecisionsMigrationTest(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.project = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, self.project, True)
        (self.project / "loc" / "inbox" / "done").mkdir(parents=True)
        (self.project / "loc" / "VERSION").write_text("2\n", encoding="utf-8")
        (self.project / "loc" / "PRD.md").write_bytes(PRD_2.replace("\n", "\r\n").encode("utf-8"))

    def migrate(self) -> dict:
        result = run("migrate.py", "--project", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_adds_decisions_before_directions(self):
        (self.project / "loc/inbox/done/004-plan-1-easy-export.md").write_text("# plan\n", encoding="utf-8")
        out = self.migrate()
        self.assertEqual((out["from"], out["to"]), (2, 4))
        self.assertTrue(out["harvest"])
        self.assertIn("loc/PRD.md", out["changed"])
        self.assertEqual(out["translate"], [])
        prd = (self.project / "loc/PRD.md").read_bytes().decode("utf-8")
        self.assertNotIn("\n", prd.replace("\r\n", ""))  # the file's line endings are kept
        self.assertLess(prd.index("## Scenarios"), prd.index("## Decisions"))
        self.assertLess(prd.index("## Decisions"), prd.index("## Directions"))
        self.assertIn("D-01", prd)
        self.assertEqual((self.project / "loc/VERSION").read_text(encoding="utf-8").strip(), "4")
        before = (self.project / "loc/PRD.md").read_bytes()
        again = self.migrate()
        self.assertEqual((again["from"], again["to"]), (4, 4))
        self.assertEqual((self.project / "loc/PRD.md").read_bytes(), before)

    def test_no_harvest_without_done_plans_or_with_decisions(self):
        out = self.migrate()
        self.assertFalse(out["harvest"])
        (self.project / "loc/VERSION").write_text("2\n", encoding="utf-8")
        prd = PRD_2.replace("## Directions",
                            "## Decisions\n- D-01: Greetings end with a dot. Reason: style.\n\n## Directions")
        (self.project / "loc/PRD.md").write_bytes(prd.encode("utf-8"))
        (self.project / "loc/inbox/done/004-plan-1-easy-export.md").write_text("# plan\n", encoding="utf-8")
        out = self.migrate()
        self.assertFalse(out["harvest"])
        self.assertEqual((self.project / "loc/PRD.md").read_text(encoding="utf-8").count("## Decisions"), 1)

    def test_template_has_decisions(self):
        prd = (ROOT / "templates" / "loc" / "PRD.md").read_text(encoding="utf-8")
        self.assertLess(prd.index("\n## Scenarios"), prd.index("\n## Decisions"))
        self.assertLess(prd.index("\n## Decisions"), prd.index("\n## Directions"))
        self.assertIn("replaces D-", prd)


READY_PLAN = """# 070 — Ready

**Type:** plan
**Status:** open
**Created:** 2026-10-10
**Source:** conversation

## Goal
The greeting works.

## Out of scope
- export

## Not defended against
- none

## Code context
- `app.py:1`

## Milestones

### M1 — docs
**No tests:** documents only
**Performer:** auto
**Proof:** `python -c "print(1)"` → `1`

## Risks and decisions
- none

## Plan gate
- round 1: scan clean, critic has no blocking notes

## Resolution
"""

BROKEN_PLAN = """# 008 — Stage 1

**Type:** plan
**Status:** open
**Created:** 2026-09-01
**Source:** conversation

## Goal
Data foundation.

## Milestones

### M1 — store
**Dowód:** run it by hand
"""


class PriorityMigrationTest(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.project = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, self.project, True)
        files = {
            "loc/VERSION": "3\n",
            "loc/PRD.md": PRD_2.replace("## Directions", "## Decisions\n- D-01: Dots. Reason: style.\n\n## Directions"),
            "loc/inbox/008-plan-etap-1.md": BROKEN_PLAN,
            "loc/inbox/070-plan-easy-ready.md": READY_PLAN,
            "loc/inbox/060-plan-running.md": BROKEN_PLAN,
            "loc/inbox/069-plan-1-medium-grouped.md": BROKEN_PLAN,
            "loc/state/060.json": json.dumps({"plan": "loc/inbox/060-plan-running.md", "phase": "build"}),
            "loc/MEMORY.md": "Details: loc/inbox/008-plan-etap-1.md\n",
        }
        for rel, text in files.items():
            path = self.project / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text.encode("utf-8"))

    def migrate(self) -> dict:
        result = run("migrate.py", "--project", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_ready_plan_passes_the_gate(self):
        path = self.project / "loc/inbox/070-plan-easy-ready.md"
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_plan.py"), "--ready", str(path)],
                                capture_output=True, text=True, encoding="utf-8",
                                env={**os.environ, "CLAUDE_PROJECT_DIR": str(self.project)})
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_priorities_and_old_plans(self):
        out = self.migrate()
        self.assertEqual((out["from"], out["to"]), (3, 4))
        prd = (self.project / "loc/PRD.md").read_text(encoding="utf-8")
        self.assertLess(prd.index("## Decisions"), prd.index("## Priorities"))
        self.assertLess(prd.index("## Priorities"), prd.index("## Directions"))

        inbox = sorted(p.name for p in (self.project / "loc/inbox").glob("*.md"))
        self.assertEqual(inbox, ["008-deferred-etap-1.md", "060-plan-running.md",
                                 "069-plan-1-medium-grouped.md", "070-plan-easy-ready.md"])
        self.assertEqual(out["deferred"], [["008-plan-etap-1.md", "008-deferred-etap-1.md"]])
        self.assertTrue(out["regroup"])
        deferred = (self.project / "loc/inbox/008-deferred-etap-1.md").read_text(encoding="utf-8")
        self.assertIn("**Type:** deferred\n**Deferred:** ", deferred)
        self.assertIn("needs re-planning", deferred)
        kept = [line for line in deferred.splitlines() if not line.startswith(("**Type:**", "**Deferred:**"))]
        self.assertEqual(kept, [line for line in BROKEN_PLAN.splitlines() if not line.startswith("**Type:**")])
        self.assertIn("loc/inbox/008-deferred-etap-1.md", (self.project / "loc/MEMORY.md").read_text(encoding="utf-8"))
        self.assertEqual((self.project / "loc/inbox/060-plan-running.md").read_text(encoding="utf-8"), BROKEN_PLAN)

        before = {p: p.read_bytes() for p in self.project.rglob("*") if p.is_file()}
        again = self.migrate()
        self.assertEqual((again["from"], again["to"]), (4, 4))
        self.assertEqual({p: p.read_bytes() for p in self.project.rglob("*") if p.is_file()}, before)

    def test_template_has_priorities(self):
        prd = (ROOT / "templates" / "loc" / "PRD.md").read_text(encoding="utf-8")
        self.assertLess(prd.index("\n## Decisions"), prd.index("\n## Priorities"))
        self.assertLess(prd.index("\n## Priorities"), prd.index("\n## Directions"))


if __name__ == "__main__":
    unittest.main()
