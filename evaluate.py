"""F8 仕分けのテスト：答えの分かる品物で AI の正解率を出すファイル。"""

import csv

from ai_client import ask_ai
from config import PASS_RATE, TEST_ITEMS_FILE, AppError
from rules import build_prompt, load_rules, load_settings


def load_test_items(path=TEST_ITEMS_FILE):
    """test_items.csv から (品物, 正解のお店) の一覧を読む。"""
    try:
        with open(path, encoding="utf-8", newline="") as file:
            return [(row["品物"].strip(), row["お店"].strip()) for row in csv.DictReader(file)]
    except FileNotFoundError:
        raise AppError(f"テストの品物のファイルが見つかりません：{path}") from None
    except (KeyError, AttributeError):
        raise AppError(f"テストの品物のファイルの形が違います：{path}") from None


def remove_answers(rules, items):
    """AI に答えを見せないよう、テストの品物をルールの例から除く。"""
    test_names = {name for name, _ in items}
    return {name: store for name, store in rules.items() if name not in test_names}


def score(results):
    """(品物, 正解, AI の答え) の一覧から、正解数と外れた品物を返す。"""
    misses = [result for result in results if result[1] != result[2]]
    return len(results) - len(misses), misses


def run():
    """品物を1つずつ AI に聞き、正解率と外れた品物を表示する。"""
    settings = load_settings()
    items = load_test_items()
    if not items:
        raise AppError("テストの品物が1つもありません。")
    examples = remove_answers(load_rules(), items)

    print(f"{len(items)}個の品物を AI に仕分けさせます")
    results = []
    for name, answer in items:
        reply = ask_ai(build_prompt(settings, name, examples), settings)
        results.append((name, answer, reply))

    correct, misses = score(results)
    rate = correct / len(items)
    print(f"正解：{correct} / {len(items)}（{rate:.0%}）")
    print("合格" if rate >= PASS_RATE else f"不合格（合格ラインは {PASS_RATE:.0%}）")

    if misses:
        print("\n外れた品物：")
        for name, answer, reply in misses:
            print(f"  ・{name}　正解：{answer}　AI：{reply}")
