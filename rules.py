"""settings.json と rules.json の読み書き、AI への聞き方の組み立てを行うファイル。"""

import json
import shutil
from datetime import datetime

from config import ASK_EVERY_TIME, RULES_FILE, SETTINGS_FILE, AppError


def read_json(path, label):
    """JSON ファイルを読む。無い・壊れているときは分かるエラーにする。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise AppError(f"{label}が見つかりません：{path}") from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise AppError(f"{label}の中身が壊れています：{path}") from None
    if not isinstance(data, dict):
        raise AppError(f"{label}の形が想定と違います：{path}")
    return data


def load_settings(path=SETTINGS_FILE):
    """お店の一覧と AI への聞き方を読む。"""
    return read_json(path, "設定のファイル")


def load_rules(path=RULES_FILE):
    """「品物 → お店」のルールを読む。"""
    return read_json(path, "ルールのファイル")


def save_rules(rules, path=RULES_FILE):
    """ルールを保存する。日本語が読めるよう、文字をそのまま書く。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(rules, ensure_ascii=False, indent=2)
    path.write_text(text + "\n", encoding="utf-8")


def backup_rules(path=RULES_FILE):
    """ルールのファイルを、日時を付けた名前でコピーする。コピー先を返す。"""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_name(f"{path.stem}.backup-{stamp}{path.suffix}")
    shutil.copy2(path, backup_path)
    return backup_path


def mark_ask_every_time(items, path=RULES_FILE):
    """指定の品物を「毎回選ぶ」にする。無ければ足す。"""
    rules = load_rules(path)
    backup_rules(path)
    save_rules({**rules, **dict.fromkeys(items, ASK_EVERY_TIME)}, path)


def build_prompt(settings, item, rules):
    """AI への聞き方を組み立てる。ショートカットと同じ置き換えをする。"""
    return (
        settings["prompt"]
        .replace("{stores}", "、".join(settings["stores"]))
        .replace("{examples}", json.dumps(rules, ensure_ascii=False))
        .replace("{item}", item)
    )
