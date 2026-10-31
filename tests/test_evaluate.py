"""仕分けのテストの単体テスト。"""

import pytest

from config import AppError
from evaluate import load_test_items, remove_answers, score


def test_テストの品物を読む(tmp_path):
    path = tmp_path / "items.csv"
    path.write_text("品物,お店\n牛乳,スーパー\n", encoding="utf-8")
    assert load_test_items(path) == [("牛乳", "スーパー")]


def test_ファイルが無いときはエラーにする(tmp_path):
    with pytest.raises(AppError):
        load_test_items(tmp_path / "items.csv")


def test_テストの品物をルールの例から除く():
    rules = {"牛乳": "スーパー", "竹輪": "スーパー"}
    assert remove_answers(rules, [("牛乳", "スーパー")]) == {"竹輪": "スーパー"}


def test_正解数と外れた品物を返す():
    results = [("牛乳", "スーパー", "スーパー"), ("綿棒", "100均", "コストコ")]
    assert score(results) == (1, [("綿棒", "100均", "コストコ")])
