"""Guard rails for the layering: the database details stay inside db/."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRODUCTION_DIRS = ["callbacks", "behaviours", "jobs", "utils", "domain", "conf"]
PRODUCTION_FILES = ["handlers.py", "main.py"]
SQL_KEYWORDS = ["SELECT ", "INSERT INTO", "UPDATE ", "DELETE FROM"]


def _sources() -> list[Path]:
    paths = [p for d in PRODUCTION_DIRS for p in (ROOT / d).rglob("*.py")]
    paths += [ROOT / f for f in PRODUCTION_FILES]
    return sorted(paths)


def _imported_modules(path: Path) -> set[str]:
    modules = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.add(node.module)
    return modules


def _importers(paths: list[Path], forbidden: set[str]) -> list[str]:
    return [
        f"{p.relative_to(ROOT)} imports {m}"
        for p in paths
        for m in sorted(_imported_modules(p))
        if m.split(".")[0] in forbidden
    ]


def _containing(paths: list[Path], needles: list[str]) -> list[str]:
    return [
        f"{p.relative_to(ROOT)} contains {n!r}"
        for p in paths
        for n in needles
        if n in p.read_text()
    ]


def test_only_db_imports_psycopg():
    found = _importers(_sources(), {"psycopg", "psycopg_pool"})
    assert not found, f"psycopg must only be used inside db/: {found}"


def test_the_legacy_table_is_known_only_to_the_migrations():
    # every application module and the whole test suite, except the tests of the copy migration
    paths = sorted(
        p
        for p in ROOT.rglob("*.py")
        if not {".venv", "migrations"} & set(p.relative_to(ROOT).parts)
        and p.name not in {"test_schema_redesign.py", "test_architecture.py"}
    )
    found = _containing(paths, ["all_players"])
    assert not found, f"all_players belongs to migrations/ only: {found}"


def test_domain_is_pure():
    found = _importers(
        sorted((ROOT / "domain").rglob("*.py")),
        {"telegram", "db", "psycopg", "psycopg_pool", "json"},
    )
    assert not found, f"domain/ must not depend on infrastructure: {found}"


def test_no_sql_outside_db():
    found = _containing(_sources(), SQL_KEYWORDS)
    assert not found, f"queries belong in db/: {found}"
