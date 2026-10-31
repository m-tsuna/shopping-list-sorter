"""ファイル名・フォルダ名・URL などの設定をまとめたファイル。"""

from pathlib import Path

# このプログラムが置かれているフォルダ
BASE_DIR = Path(__file__).resolve().parent

# リポジトリの中のファイル
SETTINGS_FILE = BASE_DIR / "settings.json"
MEMO_FILE = BASE_DIR / "memo.txt"
TEST_ITEMS_FILE = BASE_DIR / "test_items.csv"
ENV_FILE = BASE_DIR / ".env"

# iPhone と Mac で共有する iCloud Drive のフォルダ（ショートカット用の場所）
ICLOUD_DIR = (
    Path.home()
    / "Library/Mobile Documents/iCloud~is~workflow~my~workflows/Documents/買い物仕分け"
)
RULES_FILE = ICLOUD_DIR / "rules.json"
ICLOUD_SETTINGS_FILE = ICLOUD_DIR / "settings.json"

# OpenAI API
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
API_KEY_NAME = "OPENAI_API_KEY"
TIMEOUT_SECONDS = 30

# メモでお店の見出しと判断する先頭の記号
HEADING_MARKS = "⚫●•◆■"
# ⚫ の直後に付くことがある、見た目を決める見えない文字
VARIATION_SELECTORS = "︎️"

# ルールでこの値になっている品物は、毎回お店を選んでもらう
ASK_EVERY_TIME = "毎回選ぶ"

# 正解率の合格ライン（要件定義書 T10）
PASS_RATE = 0.85


class AppError(Exception):
    """利用者に日本語で知らせて終了するエラー。"""
