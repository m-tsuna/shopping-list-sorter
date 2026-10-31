"""F7 ルールの整理：書き方の違う品物を見つけ、お店を揃えるファイル。"""

import json
from collections import Counter

from ai_client import ask_ai
from config import RULES_FILE, AppError
from rules import backup_rules, load_rules, load_settings, save_rules

# 品物の数だけ返事が長くなるので、仕分けより多めに取る
TIDY_MAX_TOKENS = 1000


def parse_groups(reply, rules):
    """AI の返事から、書き方の違う品物のまとまりを取り出す。

    返事は [["おむつ", "オムツ"]] の形。ルールに無い名前は取り除く。
    """
    # AI が ```json で囲んで返すことがあるので、[ から ] までを取り出す
    start, end = reply.find("["), reply.rfind("]")
    try:
        groups = json.loads(reply[start : end + 1])
    except json.JSONDecodeError:
        raise AppError("AI の返事を読み取れませんでした。もう一度試してください。") from None

    result = []
    for group in groups:
        names = [name for name in group if name in rules]
        if len(names) >= 2:
            result.append(names)
    return result


def choose_store(names, rules):
    """まとまりの中で一番多いお店を選ぶ。同数なら先に出てきた方にする。"""
    return Counter(rules[name] for name in names).most_common(1)[0][0]


def make_changes(groups, rules):
    """お店が揃っていないまとまりから、{品物: 新しいお店} を作る。"""
    changes = {}
    for names in groups:
        store = choose_store(names, rules)
        for name in names:
            if rules[name] != store:
                changes[name] = store
    return changes


def run(rules_path=RULES_FILE):
    """AI にまとまりを探させ、y と答えたときだけ書き換える。"""
    settings = load_settings()
    rules = load_rules(rules_path)
    prompt = settings["tidy_prompt"].replace(
        "{items}", json.dumps(list(rules), ensure_ascii=False)
    )
    groups = parse_groups(ask_ai(prompt, settings, TIDY_MAX_TOKENS), rules)

    if not groups:
        print("書き方の違う品物は見つかりませんでした。")
        return

    print("書き方の違う品物：")
    for names in groups:
        detail = "、".join(f"{name}（{rules[name]}）" for name in names)
        print(f"  ・{detail}")

    changes = make_changes(groups, rules)
    if not changes:
        print("どれもお店は揃っています。変更はありません。")
        return

    print("次のように変えます（書き方はどちらも残します）：")
    for name, store in changes.items():
        print(f"  ・{name}：{rules[name]} → {store}")

    if input("書き換えますか？（y / n）：").strip().lower() != "y":
        print("やめました。ファイルは変えていません。")
        return

    print(f"バックアップ：{backup_rules(rules_path).name}")
    save_rules({**rules, **changes}, rules_path)
    print("保存しました。")
