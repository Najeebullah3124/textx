from pathlib import Path

from bugfinder.scanner import chunk_python_file, chunk_source_file, scan_source_files


def test_chunk_python_file_splits_large_function(tmp_path: Path) -> None:
    source = "def f():\n" + "".join(f"    x{i} = {i}\n" for i in range(300))
    file_path = tmp_path / "sample.py"
    file_path.write_text(source, encoding="utf-8")

    chunks = chunk_python_file(file_path, max_lines=80)
    assert len(chunks) >= 3
    assert all(c.content.strip() for c in chunks)


def test_scan_source_files_includes_react_and_python(tmp_path: Path) -> None:
    py = tmp_path / "a.py"
    tsx = tmp_path / "App.tsx"
    py.write_text("print('x')\n", encoding="utf-8")
    tsx.write_text("export const App = () => <div>Hello</div>;\n", encoding="utf-8")

    files = scan_source_files(str(tmp_path))
    paths = {p.name for p in files}
    assert "a.py" in paths
    assert "App.tsx" in paths


def test_chunk_source_file_sets_language_for_tsx(tmp_path: Path) -> None:
    tsx = tmp_path / "App.tsx"
    tsx.write_text("export const App = () => <div>Hello</div>;\n", encoding="utf-8")
    chunks = chunk_source_file(tsx, max_lines=20)
    assert len(chunks) == 1
    assert chunks[0].language == "typescript"
