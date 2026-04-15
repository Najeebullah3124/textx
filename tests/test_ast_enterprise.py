from pathlib import Path

from bugfinder.analyzer.ast_analyzer import analyze_file_with_ast


def test_ast_flags_requests_without_timeout(tmp_path: Path) -> None:
    file_path = tmp_path / "http_client.py"
    file_path.write_text(
        "import requests\n"
        "def fetch(url):\n"
        "    return requests.get(url)\n",
        encoding="utf-8",
    )
    issues = analyze_file_with_ast(file_path)
    assert any("without timeout" in issue.description.lower() for issue in issues)


def test_ast_flags_dynamic_sql_execution(tmp_path: Path) -> None:
    file_path = tmp_path / "db.py"
    file_path.write_text(
        "def run(cursor, user_id):\n"
        "    cursor.execute(f\"SELECT * FROM users WHERE id = {user_id}\")\n",
        encoding="utf-8",
    )
    issues = analyze_file_with_ast(file_path)
    assert any("dynamic sql query construction" in issue.description.lower() for issue in issues)


def test_ast_flags_weak_hash_usage(tmp_path: Path) -> None:
    file_path = tmp_path / "hashing.py"
    file_path.write_text(
        "import hashlib\n"
        "def digest(x):\n"
        "    return hashlib.md5(x.encode()).hexdigest()\n",
        encoding="utf-8",
    )
    issues = analyze_file_with_ast(file_path)
    assert any("weak hash algorithm" in issue.description.lower() for issue in issues)
