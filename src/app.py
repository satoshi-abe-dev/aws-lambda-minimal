"""GET /hello に応答する Lambda ハンドラ。

API Gateway（HTTP API, ペイロード形式 2.0）から呼ばれる。
API Gateway の正式な名前は Amazon API Gateway（AWS のサービス）。
クエリ文字列の name を使って挨拶を JSON で返す。標準ライブラリのみを使う。

template.yaml の `Handler: app.lambda_handler` で、このファイルの lambda_handler が指定されている。
仕組みの説明は docs/how-it-works.md にある。
"""

# ファイルの一番外側の行は、Lambda が起動したとき（コールドスタート）に 1 回だけ実行される。
import json


# ハンドラ。リクエストが来るたびに Lambda から呼び出される。
#   event:   リクエストの情報が入った辞書。GET /hello?name=test の場合、
#            event["queryStringParameters"] は {"name": "test"} になる。
#   context: 残りの実行時間など、Lambda 側の情報。この関数ではログに出すだけで、処理には使わない。
# 戻り値の辞書は、API Gateway が HTTP のレスポンスに変換してクライアントに返す。
def lambda_handler(event, context):
    # クエリ文字列（URL の ? より後ろ）を取り出す。
    # クエリ文字列がないとき、HTTP API は queryStringParameters のキー自体を含めない。
    # そのため get() で取り出し、None の場合は空の辞書にする。
    params = event.get("queryStringParameters") or {}
    # name がない場合と、空文字（?name=）の場合は "World" を使う。
    name = params.get("name") or "World"
    print(f"event:{{ {event} }}  @lambda_handler in app.py")
    print(f"context:{{ {context} }}  @lambda_handler in app.py")
    print(f"name:{{ {name} }}  @lambda_handler in app.py")

    # 辞書形式
    return {
        # HTTP のステータスコード。200 は成功。
        "statusCode": 200,
        # レスポンスの本文が JSON であることを示す。
        "headers": {"Content-Type": "application/json"},
        # 本文は文字列で返す。json.dumps で辞書を JSON の文字列に変換する。
        # ensure_ascii=False で、日本語の名前を \uXXXX に変換せず、そのまま返す。
        "body": json.dumps({"message": f"Hello, {name}!"}, ensure_ascii=False),
    }
