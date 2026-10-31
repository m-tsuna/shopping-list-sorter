"""OpenAI に質問して、返事の文章を受け取るファイル。"""

import os

import requests
from dotenv import load_dotenv

from config import API_KEY_NAME, ENV_FILE, OPENAI_URL, TIMEOUT_SECONDS, AppError


def get_api_key():
    """.env から OpenAI の鍵を読む。無ければエラーにする。"""
    load_dotenv(ENV_FILE)
    key = os.environ.get(API_KEY_NAME, "").strip()
    if not key:
        raise AppError(
            f"OpenAI の鍵が見つかりません。.env に {API_KEY_NAME}=鍵 を書いてください。"
        )
    return key


def explain_error(response):
    """OpenAI の失敗の返事を、原因が分かる日本語にする。"""
    if response.status_code == 401:
        return "OpenAI の鍵が正しくありません。.env の鍵を確かめてください。"
    if response.status_code == 429:
        try:
            code = response.json()["error"]["code"]
        except (ValueError, KeyError, TypeError):
            code = ""
        if code == "insufficient_quota":
            return "OpenAI の残高が足りません。管理画面で残高を確かめてください。"
        return "OpenAI への問い合わせが多すぎます。少し待ってからやり直してください。"
    return f"OpenAI からエラーが返りました（状態コード {response.status_code}）。"


def ask_ai(prompt, settings, max_tokens=None):
    """AI に prompt を送り、返事の文章を返す。

    max_tokens を省くと settings.json の値を使う。
    """
    key = get_api_key()
    body = {
        "model": settings["model"],
        "temperature": settings["temperature"],
        "max_tokens": max_tokens or settings["max_tokens"],
        "messages": [{"role": "user", "content": prompt}],
    }
    # 鍵が画面に出ないよう、通信エラーの中身は表示しない
    try:
        response = requests.post(
            OPENAI_URL,
            headers={"Authorization": f"Bearer {key}"},
            json=body,
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException:
        raise AppError(
            "OpenAI につながりませんでした。インターネットの接続を確かめてください。"
        ) from None

    if response.status_code != 200:
        raise AppError(explain_error(response))

    # 返事は choices → 1つ目 → message → content の入れ子になっている
    try:
        return response.json()["choices"][0]["message"]["content"].strip()
    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
        raise AppError("OpenAI の返事の形が想定と違いました。") from None
