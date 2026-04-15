from bugfinder.cache.cache_manager import CacheManager


def test_cache_set_get(tmp_path) -> None:
    db_path = tmp_path / "cache.sqlite3"
    cache = CacheManager(str(db_path))
    key = "k1"
    payload = {"issues": [{"type": "bug"}]}
    cache.set(key, payload)

    loaded = cache.get(key)
    assert loaded == payload
