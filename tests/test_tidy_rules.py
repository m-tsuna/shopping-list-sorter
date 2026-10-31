"""ルールの整理の単体テスト。"""

import pytest

from config import AppError
from tidy_rules import choose_store, make_changes, parse_groups

RULES = {"おむつ": "コストコ", "オムツ": "アカチャンホンポ", "紙おむつ": "コストコ"}


def test_JSONのまとまりを読み取る():
    assert parse_groups('[["おむつ", "オムツ"]]', RULES) == [["おむつ", "オムツ"]]


def test_コードの囲みが付いた返事も読める():
    assert parse_groups('```json\n[["おむつ", "オムツ"]]\n```', RULES) == [["おむつ", "オムツ"]]


def test_ルールに無い名前は取り除く():
    assert parse_groups('[["おむつ", "存在しない"]]', RULES) == []


def test_読み取れない返事はエラーにする():
    with pytest.raises(AppError):
        parse_groups("見つかりません", RULES)


def test_一番多いお店を選ぶ():
    assert choose_store(["オムツ", "おむつ", "紙おむつ"], RULES) == "コストコ"


def test_違うお店の品物だけを変更する():
    assert make_changes([["おむつ", "オムツ", "紙おむつ"]], RULES) == {"オムツ": "コストコ"}


def test_お店が揃っていれば変更しない():
    assert make_changes([["おむつ", "紙おむつ"]], RULES) == {}
