# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要
思いついた買い物の品物を、iPhone から声か短い入力で登録すると、リマインダーのお店別リストへ自動で入れるツールです。利用者は本人1人で、毎日の買い物メモの手間を減らすために使います。

- 毎日使う部分は iPhone の「ショートカット」で動き、Python は動かない
- Python は Mac で手で動かす補助で、ルール作り・整理・正解率の測定を行う
- 両者は iCloud Drive の同じファイルでつながる

## 使う技術
- Python 3（Anaconda。`/opt/anaconda3/bin/python`）／requests／python-dotenv／pytest
- OpenAI API（gpt-4o-mini）。Python は Chat Completions、ショートカットは Responses API
- iPhone のショートカット・リマインダー、iCloud Drive

## 動かし方（コマンド）
- `python main.py create`：`memo.txt` から `rules.json` を作る
- `python main.py tidy [ファイル]`：書き方の違う品物を AI が見つけ、お店を揃える（省略時は本物の `rules.json`）
- `python main.py test`：`test_items.csv` で AI の正解率を測る（少し料金がかかる）
- `python main.py deploy`：`settings.json` を iCloud へコピーする
- `python main.py always 品物...`：買うお店が変わる品物を「毎回選ぶ」にする
- `python build_shortcut.py`：ショートカットのファイルを作って署名する
- `pytest`：単体テストを全部実行する（AI にはつながない）
- `pytest tests/test_create_rules.py::関数名`：テストを1つだけ実行する

## 全体の仕組み
- 本物の `rules.json` は iCloud の `Shortcuts/買い物仕分け/` にあり、ショートカットが品物を入れるたびに書き足す。リポジトリには置かない
- `settings.json` の本物はリポジトリにあり、`deploy` で iCloud へコピーする。変えたら `deploy` が要る
- AI への聞き方は `settings.json` の `prompt` が唯一の定義。`{stores}`・`{examples}`・`{item}` をショートカットと `rules.py` の `build_prompt` が同じように置き換える
- `{examples}` には `rules.json` の JSON をそのまま入れる。ショートカットが同じ文字列を作れるよう、加工しない

## コードの書き方
- 利用者に見せるエラーは `config.py` の `AppError` を投げ、`main.py` でまとめて表示する
- OpenAI への通信は `ai_client.py` だけが行う。単体テストでは `requests.post` を差し替える
- `rules.json` を書き換える前に `rules.py` の `backup_rules` を呼ぶ

## このプロジェクトのルール
- お店を増やす・名前を変えるときは、`settings.json` とショートカットの分岐（README の手順12）の両方を直す
- ショートカットは GitHub に載らないので、手順を変えたら README の作り方も直す
- 進捗と記事の材料は `作業記録.md` に書く
