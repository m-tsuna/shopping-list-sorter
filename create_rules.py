"""F6 最初のルール作り：いまの買い物メモから rules.json を作るファイル。"""

from config import (
    HEADING_MARKS,
    MEMO_FILE,
    RULES_FILE,
    VARIATION_SELECTORS,
    AppError,
)
from rules import backup_rules, load_settings, save_rules


def parse_memo(text, stores):
    """メモの文章を読み、{品物: お店} の辞書を返す。"""
    rules = {}
    current_store = None
    for line in text.splitlines():
        # strip は全角の空白も取り除く
        line = line.strip()
        if not line:
            continue
        if line[0] in HEADING_MARKS:
            current_store = line.lstrip(HEADING_MARKS + VARIATION_SELECTORS).strip()
            if current_store not in stores:
                raise AppError(f"メモのお店「{current_store}」は設定にありません。")
        elif current_store is None:
            raise AppError(f"お店の見出しより前に品物があります：{line}")
        else:
            rules[line] = current_store
    return rules


def count_by_store(rules, stores):
    """お店ごとの品物の数を数える。"""
    values = list(rules.values())
    return {store: values.count(store) for store in stores}


def run(memo_path=MEMO_FILE, rules_path=RULES_FILE):
    """メモを読み、確認してから rules.json を保存する。"""
    settings = load_settings()
    try:
        text = memo_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise AppError(f"メモのファイルが見つかりません：{memo_path}") from None

    rules = parse_memo(text, settings["stores"])
    if not rules:
        raise AppError("メモに品物がありませんでした。")

    print(f"{len(rules)}品を読み取りました")
    for store, count in count_by_store(rules, settings["stores"]).items():
        print(f"  {store}：{count}品")

    if rules_path.exists():
        answer = input("rules.json はすでにあります。作り直しますか？（y / n）：")
        if answer.strip().lower() != "y":
            print("やめました。ファイルは変えていません。")
            return
        print(f"バックアップ：{backup_rules(rules_path).name}")

    save_rules(rules, rules_path)
    print(f"保存しました：{rules_path}")
