"""買い物リスト自動仕分けの入口。実行するコマンドを受け取って振り分ける。"""

import shutil
import sys
from pathlib import Path

import create_rules
import evaluate
import tidy_rules
import rules
from config import ICLOUD_DIR, ICLOUD_SETTINGS_FILE, RULES_FILE, SETTINGS_FILE, AppError

USAGE = """使い方：
  python main.py create         いまの買い物メモから rules.json を作る
  python main.py tidy [ファイル]  書き方の違う品物のお店を揃える
  python main.py test           AI の仕分けの正解率を測る
  python main.py deploy         settings.json を iCloud にコピーする
  python main.py always 品物...  その品物を毎回お店を選ぶようにする"""


def deploy():
    """settings.json を、ショートカットが読む iCloud の場所へコピーする。"""
    if not SETTINGS_FILE.exists():
        raise AppError(f"設定のファイルが見つかりません：{SETTINGS_FILE}")
    ICLOUD_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SETTINGS_FILE, ICLOUD_SETTINGS_FILE)
    print(f"コピーしました：{ICLOUD_SETTINGS_FILE}")


def run_command(args):
    """コマンドの名前に合う処理を実行する。"""
    command = args[0] if args else ""
    if command == "create" and len(args) == 1:
        create_rules.run()
    elif command == "tidy" and len(args) <= 2:
        tidy_rules.run(Path(args[1]) if len(args) == 2 else RULES_FILE)
    elif command == "test" and len(args) == 1:
        evaluate.run()
    elif command == "deploy" and len(args) == 1:
        deploy()
    elif command == "always" and len(args) >= 2:
        rules.mark_ask_every_time(args[1:])
        print(f"毎回選ぶようにしました：{'、'.join(args[1:])}")
    else:
        print(USAGE)
        return 1
    return 0


def main():
    """エラーをまとめて受け取り、日本語で表示して終了する。"""
    try:
        return run_command(sys.argv[1:])
    except AppError as error:
        print(f"エラー：{error}")
    except KeyboardInterrupt:
        print("\n途中でやめました。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
