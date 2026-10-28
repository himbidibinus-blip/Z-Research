"""Every test uses a temporary database and data directory; never touches actual user data."""
import pytest

@pytest.fixture(autouse=True)
def isolated_research_store(monkeypatch, tmp_path):
    import app.main as main
    import app.ai_features as ai
    data = tmp_path / 'local_data'
    data.mkdir()
    database = data / 'quantresearch.db'
    monkeypatch.setattr(main, 'DATA', data)
    monkeypatch.setattr(main, 'DB', database)
    monkeypatch.setattr(ai, 'ROOT', tmp_path)
    monkeypatch.setattr(ai, 'DBPATH', database)
    ai.SESSIONS.clear()
    main.init()
    ai.setup_db()
    import app.v09 as v09
    monkeypatch.setattr(v09, 'DATA', data)
    v09.initialize()
    from app.v05 import setup_v05_db
    setup_v05_db()
    yield
    ai.SESSIONS.clear()
