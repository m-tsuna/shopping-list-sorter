"""ルールの読み書きと、AI への聞き方の単体テスト。"""

import json

import pytest

from config import AppError
from rules import backup_rules, build_prompt, load_rules, mark_ask_every_time, save_rules


def test_保存して読み直すと同じ中身になる(tmp_path):
    path = tmp_path / "rules.json"
    save_rules({"おむつ": "コストコ"}, path)
    assert load_rules(path) == {"おむつ": "コストコ"}
    assert "おむつ" in path.read_text(encoding="utf-8")


def test_ファイルが無いときはエラーにする(tmp_path):
    with pytest.raises(AppError, match="見つかりません"):
        load_rules(tmp_path / "rules.json")


def test_ファイルが壊れているときはエラーにする(tmp_path):
    path = tmp_path / "rules.json"
    path.write_text("{壊れている", encoding="utf-8")
    with pytest.raises(AppError, match="壊れています"):
        load_rules(path)


def test_バックアップは元と同じ中身になる(tmp_path):
    path = tmp_path / "rules.json"
    save_rules({"おむつ": "コストコ"}, path)
    backup = backup_rules(path)
    assert backup != path
    assert load_rules(backup) == {"おむつ": "コストコ"}


def test_指定の品物を毎回選ぶにする(tmp_path):
    path = tmp_path / "rules.json"
    save_rules({"牛乳": "スーパー", "シャンプー": "コストコ"}, path)
    mark_ask_every_time(["シャンプー", "歯磨き粉"], path)
    assert load_rules(path) == {
        "牛乳": "スーパー",
        "シャンプー": "毎回選ぶ",
        "歯磨き粉": "毎回選ぶ",
    }


def test_聞き方の3か所を置き換える():
    settings = {"prompt": "{stores}|{examples}|{item}", "stores": ["スーパー", "100均"]}
    rules = {"竹輪": "スーパー"}
    assert build_prompt(settings, "牛乳", rules) == (
        f"スーパー、100均|{json.dumps(rules, ensure_ascii=False)}|牛乳"
    )
