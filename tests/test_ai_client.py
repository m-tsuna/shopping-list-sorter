"""OpenAI への通信の単体テスト。requests.post を差し替え、本物にはつながない。"""

from unittest.mock import Mock, patch

import pytest
import requests

import ai_client
from config import API_KEY_NAME, AppError

SETTINGS = {"model": "gpt-4o-mini", "temperature": 0, "max_tokens": 20}


@pytest.fixture(autouse=True)
def fake_key(monkeypatch):
    """本物の鍵の代わりに、偽物の鍵を使う。"""
    monkeypatch.setattr(ai_client, "load_dotenv", lambda path: None)
    monkeypatch.setenv(API_KEY_NAME, "sk-fake")


def fake_response(status, data):
    """OpenAI の返事の代わりを作る。"""
    return Mock(status_code=status, json=Mock(return_value=data))


def test_返事の文章を取り出す():
    data = {"choices": [{"message": {"content": " スーパー\n"}}]}
    with patch("ai_client.requests.post", return_value=fake_response(200, data)):
        assert ai_client.ask_ai("質問", SETTINGS) == "スーパー"


def test_鍵が無いときはエラーにする(monkeypatch):
    monkeypatch.delenv(API_KEY_NAME)
    with pytest.raises(AppError, match="鍵が見つかりません"):
        ai_client.ask_ai("質問", SETTINGS)


def test_鍵が間違っているときはエラーにする():
    with patch("ai_client.requests.post", return_value=fake_response(401, {})):
        with pytest.raises(AppError, match="鍵が正しくありません"):
            ai_client.ask_ai("質問", SETTINGS)


def test_残高不足はエラーにする():
    data = {"error": {"code": "insufficient_quota"}}
    with patch("ai_client.requests.post", return_value=fake_response(429, data)):
        with pytest.raises(AppError, match="残高"):
            ai_client.ask_ai("質問", SETTINGS)


def test_通信エラーの表示に鍵が含まれない():
    error = requests.ConnectionError("sk-fake")
    with patch("ai_client.requests.post", side_effect=error):
        with pytest.raises(AppError) as caught:
            ai_client.ask_ai("質問", SETTINGS)
    assert "sk-fake" not in str(caught.value)


def test_想定と違う返事はエラーにする():
    with patch("ai_client.requests.post", return_value=fake_response(200, {"choices": []})):
        with pytest.raises(AppError, match="返事の形"):
            ai_client.ask_ai("質問", SETTINGS)
