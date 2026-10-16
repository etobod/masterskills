"""The plugin speaks English: no Polish letters in what it ships.

The only Polish left on purpose is the list of undecided phrases in
`scripts/check_plan.py`, which also catches a plan written in Polish.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLISH = re.compile(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]")
SHIPPED = ["templates", "scripts", "hooks", "skills", "agents", "rules", "scenarios"]
SUFFIXES = {".md", ".py", ".json", ".ts", ".sh"}
# file -> the only lines that may hold Polish
ALLOWED = {"scripts/migrate.py": re.compile(""),
           "scripts/check_plan.py": re.compile(r"^\s+\"(do |sprawdzić|zobaczymy|jeśli|ewentualnie|być|prawdopodobnie)")}


WORDS = re.compile(r"\b(tymczasowo|wariant|popraw|brak|otwarte|rozmowa|planowanie|pytanie|odlozone|przeglad|"
                   r"utknelo|bramka|kryteria|uwagi|zakres|notatki|decyzje|temat|dziennik|wzorce|sugestia|"
                   r"nierealna|zachowanie|recznie|jednostkowe|integracyjne|wykonane|mutacja|historia|"
                   r"powitanie|powitan|jezyk|drobne|przeniesione)\b", re.IGNORECASE)


def shipped():
    for top in SHIPPED:
        for path in sorted((ROOT / top).rglob("*")):
            if path.suffix in SUFFIXES and "__pycache__" not in path.parts:
                yield path.relative_to(ROOT).as_posix(), path


class LanguageTest(unittest.TestCase):
    def test_no_unaccented_polish_words(self):
        """Polish written without diacritics ("tymczasowo wariant A") slips past the letter check."""
        found = []
        for rel, path in shipped():
            allowed = ALLOWED.get(rel)
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if WORDS.search(line) and not (allowed and allowed.match(line)):
                    found.append(f"{rel}:{number}: {WORDS.search(line).group(0)}")
        self.assertEqual(found, [], "\n" + "\n".join(found))

    def test_no_polish_outside_allowed(self):
        found = []
        for top in SHIPPED:
            for path in sorted((ROOT / top).rglob("*")):
                if path.suffix not in SUFFIXES or "__pycache__" in path.parts:
                    continue
                rel = path.relative_to(ROOT).as_posix()
                allowed = ALLOWED.get(rel)
                for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    if POLISH.search(line) and not (allowed and allowed.match(line)):
                        found.append(f"{rel}:{number}: {line.strip()[:80]}")
        self.assertEqual(found, [], "\n" + "\n".join(found))


if __name__ == "__main__":
    unittest.main()
