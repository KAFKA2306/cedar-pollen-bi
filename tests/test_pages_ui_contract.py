from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


def test_first_viewport_metrics_name_the_comparison_basis():
    assert 'aria-label="過去平均比の主要指標"' in HTML
    assert "過去平均比 最大" in HTML
    assert "過去平均比 最小" in HTML
    assert "過去平均比 200%以上" in HTML
    assert "過去平均比 50%以下" in HTML


def test_primary_filter_names_the_user_task_and_same_basis():
    assert '<label for="search">都道府県を検索</label>' in HTML
    assert 'placeholder="例: 大阪府、関東"' in HTML
    assert '<label for="band">過去平均比</label>' in HTML
