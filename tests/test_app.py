"""ハンドラの単体テスト。AWS には接続しない。"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from app import lambda_handler  # noqa: E402


def make_event(query=None):
    """HTTP API（ペイロード形式 2.0）のイベントのうち、ハンドラが使う部分だけを作る。"""
    event = {
        "version": "2.0",
        "routeKey": "GET /hello",
        "rawPath": "/hello",
        "requestContext": {"http": {"method": "GET", "path": "/hello"}},
    }
    # クエリ文字列がないとき、HTTP API はこのキー自体を含めない
    if query is not None:
        event["queryStringParameters"] = query
    return event


def test_with_name():
    response = lambda_handler(make_event({"name": "Taro"}), None)

    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "application/json"
    assert json.loads(response["body"]) == {"message": "Hello, Taro!"}


def test_without_name():
    response = lambda_handler(make_event(), None)

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {"message": "Hello, World!"}


def test_with_empty_name():
    response = lambda_handler(make_event({"name": ""}), None)

    assert json.loads(response["body"]) == {"message": "Hello, World!"}


def test_with_japanese_name():
    response = lambda_handler(make_event({"name": "太郎"}), None)

    assert json.loads(response["body"]) == {"message": "Hello, 太郎!"}
