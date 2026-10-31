"""最初のルール作りの単体テスト。"""

import pytest

from config import AppError
from create_rules import count_by_store, parse_memo

STORES = ["スーパー", "コストコ"]


def test_見出しと品物を読み取る():
    assert parse_memo("⚫︎スーパー\n竹輪\n\n⚫︎コストコ\n柔軟剤\n", STORES) == {
        "竹輪": "スーパー",
        "柔軟剤": "コストコ",
    }


def test_全角の空白と空の行を取り除く():
    assert parse_memo("⚫︎スーパー\n　\n竹輪　\n", STORES) == {"竹輪": "スーパー"}


def test_別の記号の見出しも読める():
    assert parse_memo("●スーパー\n竹輪\n", STORES) == {"竹輪": "スーパー"}


def test_サイズのメモが付いた品物は1行のまま残す():
    line = "かご　幅58   奥行き24"
    assert parse_memo(f"⚫︎スーパー\n{line}\n", STORES) == {line: "スーパー"}


def test_設定に無いお店はエラーにする():
    with pytest.raises(AppError, match="八百屋"):
        parse_memo("⚫︎八百屋\nねぎ\n", STORES)


def test_見出しより前の品物はエラーにする():
    with pytest.raises(AppError, match="竹輪"):
        parse_memo("竹輪\n⚫︎スーパー\n", STORES)


def test_お店ごとの数を数える():
    rules = {"竹輪": "スーパー", "たまご": "スーパー"}
    assert count_by_store(rules, STORES) == {"スーパー": 2, "コストコ": 0}
