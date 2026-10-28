"""v0.9.4: guard the beginner-friendly UX while preserving data provenance."""
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

STATIC = Path(__file__).resolve().parents[1] / 'app' / 'static'


def test_ui_released_as_v094_and_local_backend_reports_version():
    assert TestClient(app).get('/api/health').json()['version'] == '0.9.4'
    text = (STATIC / 'index.html').read_text()
    assert 'lang="id"' in text
    assert 'v0.9.4' in text


def test_dashboard_guides_users_through_five_steps():
    js = (STATIC / 'studio09.js').read_text()
    assert "function guideStage()" in js
    assert "function guideBar(activeIndex)" in js
    for token in ['Data', 'Model', 'Analisis', 'Referensi', 'Menulis']:
        assert token in js


def test_upload_and_project_creation_are_one_explicit_opt_in_action():
    js = (STATIC / 'studio09.js').read_text()
    assert 'id="autoCreateProject" checked' in js
    assert "$('#autoCreateProject')?.checked" in js
    assert "case 'uploadForm'" in js
    assert "'POST',{name,dataset_id:a.id}" in js


def test_construct_selection_uses_plain_checkboxes_not_hidden_keyboard_shortcuts():
    js = (STATIC / 'studio09.js').read_text()
    assert 'data-multi-for="independent"' in js
    assert 'data-multi-for="mediators"' in js
    assert 'data-multi-for="moderators"' in js
    assert "[data-multi-for=\"'+id+'\"]:checked" in js


def test_dataset_modal_lists_every_column_and_does_not_overclaim_type():
    js = (STATIC / 'studio09.js').read_text()
    assert 'const variables=d.columns.map' in js
    assert 'hanya berdasarkan beberapa baris contoh' in js
    assert 'html(col)' in js


def test_existing_model_dataset_swap_requires_confirmation():
    js = (STATIC / 'studio09.js').read_text()
    assert "case 'confirm-link-dataset'" in js
    assert 'model lama akan dikosongkan' in js.lower()
    assert 'case \'cancel-modal\'' in js


def test_side_menu_and_mobile_use_accessible_nav_semantics():
    text = (STATIC / 'index.html').read_text()
    css = (STATIC / 'studio09.css').read_text()
    assert 'id="mobileMenu"' in text
    assert 'Pengaturan &amp; fitur lanjutan' in text
    assert 'aria-label="Langkah penelitian"' in (STATIC / 'studio09.js').read_text()
    assert '@media(max-width:480px)' in css
