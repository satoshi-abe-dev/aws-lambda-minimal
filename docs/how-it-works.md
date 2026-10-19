# 仕組みの説明：お店にたとえると

このサンプルで使う AWS のサービスと、手順書（[getting-started.md](getting-started.md)）のコマンドが何をしているかを、お店にたとえて説明する。

## 1. 登場人物

| AWS の名前 | お店でいうと | 役割 |
|---|---|---|
| Lambda | 料理人 | 注文が来たときだけ働く。働いた分だけ料金がかかり、注文がなければ料金はかからない |
| `src/app.py` | レシピ | 料理人が何を作るか。このサンプルでは「名前を受け取って挨拶を返す」 |
| API Gateway | 受付の窓口 | インターネットから来た注文を受け付けて、料理人に渡す。正式な名前は Amazon API Gateway で、AWS のサービスの 1 つ。デプロイで作られる URL は、この窓口の住所 |
| CloudWatch Logs | 業務日誌 | 料理人がいつ何をしたかの記録。`template.yaml` で 7 日たつと消える設定にしている |
| IAM ロール | 社員証 | 料理人が日誌に書き込むための許可証。SAM が自動で作る |

### 「サーバーの管理が要らない」の意味

プログラムを動かすには、それを実行するコンピュータ（サーバー）が要る。Lambda では、サーバーの用意と世話を AWS が受け持つ。利用者が用意するのは、コード（`src/app.py`）と設定（`template.yaml`）だけ。

比べる相手として、AWS の EC2（Elastic Compute Cloud、仮想サーバーを借りるサービス）で同じことをする場合を並べる。

| 作業 | EC2（サーバーを借りる） | Lambda |
|---|---|---|
| 性能と台数 | どの性能のサーバーを何台借りるかを決める | 決めない。メモリの量（`template.yaml` の `MemorySize`）だけを指定する |
| OS | Linux などを入れ、セキュリティ更新を当て続ける | AWS が用意し、更新する |
| Python | 自分で入れ、更新する | `template.yaml` の `Runtime: python3.14` で指定すると、AWS が用意する |
| プログラムの起動 | 起動しておき、止まったら起動し直す仕組みを作る | リクエストが来たときに AWS が実行環境を用意し、`lambda_handler` を呼ぶ |
| アクセスの増減 | 混んだら台数を増やし、空いたら減らす | 同時に来たリクエストの数に合わせて、AWS が実行環境を増やす |
| 故障 | 壊れたサーバーから別のサーバーに移す | AWS が対応する |
| 料金 | 起動している間はずっとかかる（アクセスがなくてもかかる） | 実行した回数と時間の分だけかかる |

お店でいうと、EC2 は店舗を借りて料理人を常駐させる形。客が来なくても家賃と人件費がかかり、店舗の修繕や、混んだときの人手集めも自分で行う。Lambda は、注文が入ったときだけ AWS が厨房と料理人を用意し、レシピどおりに作る形で、作った回数と時間の分だけ払う。

このような仕組みを「サーバーレス（serverless）」と呼ぶ。サーバーがなくなるわけではなく、AWS の側で動いている。利用者がサーバーを扱わない、という意味の呼び名。

サーバーを扱わない代わりに、次の制約がある。

| 制約 | 内容 |
|---|---|
| 実行時間の上限 | 1 回の実行は最大 15 分。このサンプルでは `template.yaml` の `Timeout: 10` で 10 秒にしている |
| 最初の呼び出しの遅れ | しばらく呼ばれていないと、次の呼び出しで実行環境の準備から始まり、その分だけ返事が遅くなる（コールドスタート。3 章の「起動したときと、注文が来たとき」） |
| 状態が残らない | 実行環境は片付けられることがあり、メモリに置いた値は次の呼び出しで残っていないことがある。残したいデータは S3 やデータベースに置く |
| Python のバージョン | 小さな更新は AWS が当てるが、`python3.14` のようなバージョン自体のサポートには期限がある。期限が近づいたら `Runtime` を新しいバージョンに書き換えてデプロイし直す |

## 2. 注文が来たときの流れ（手順書 8 章の `curl`）

```
Mac
   │  curl ".../hello?name=test"
   ▼
API Gateway（受付）── 「/hello への注文」として受け付け、料理人に回す
   │
   ▼
Lambda（料理人）──── app.py を実行して {"message": "Hello, test!"} を作る
   │         └──→ CloudWatch Logs（日誌）に記録する
   ▼
API Gateway（受付）
   │
   ▼
Mac に {"message": "Hello, test!"} が返る
```

## 3. ハンドラ：料理人が注文ごとに開くレシピのページ

`src/app.py` の `lambda_handler` は「ハンドラ」と呼ばれる関数。Lambda が呼び出す入口の関数で、注文（リクエスト）が来るたびに 1 回呼ばれる。Lambda が起動したときに 1 回だけ呼ばれるものではない。英語の handle は「処理する、さばく」という意味。

### Lambda がハンドラを見つける仕組み

どの関数を呼ぶかは、`template.yaml` の `Handler` で指定している。

```yaml
Handler: app.lambda_handler
#        ^^^ ^^^^^^^^^^^^^^
#        |   関数の名前（def lambda_handler）
#        ファイルの名前（app.py から .py を除いたもの）
```

関数の名前は自由に決められる。この指定と、`app.py` の関数の名前が合っていれば動く。

### 起動したときと、注文が来たとき

```python
import json          # ① 起動したときに 1 回だけ実行される

def lambda_handler(event, context):     # ② 注文が来るたびに実行される
    params = event.get("queryStringParameters") or {}
    name = params.get("name") or "World"
    return {...}
```

| タイミング | 実行される部分 | お店でいうと |
|---|---|---|
| 起動したとき（コールドスタート） | ファイルの一番外側（`import json` など） | 料理人が出勤して、包丁や鍋を準備する |
| 注文が来るたび | `lambda_handler` の中身 | 注文票を見て、料理を作る |

Lambda は一度起動すると、しばらく待機する。待機中に次の注文が来ると、起動の部分は実行せず、`lambda_handler` だけを実行する。しばらく注文がないと片付けられ、次の注文で起動からやり直す。

### 引数と戻り値

| | 中身 | お店でいうと |
|---|---|---|
| `event` | リクエストの情報（URL の `?name=test` など）が入った辞書 | 注文票 |
| `context` | 残りの実行時間など、Lambda 側の情報。このサンプルでは使っていない | 厨房の状況メモ |
| 戻り値の辞書 | ステータスコード、ヘッダー、本文。API Gateway がこれを HTTP の返事に変える | 出来上がった料理 |

`tests/test_app.py` は、この `event` を自分で作って `lambda_handler` に直接渡している。このため、AWS を使わずに Mac の中でテストできる。

### 戻り値の辞書の形

`lambda_handler` は、次の 3 つのキーを持つ辞書を返す。

| キー | 値の型 | 中身 |
|---|---|---|
| `statusCode` | 整数 | HTTP のステータスコード（200 は成功） |
| `headers` | 辞書 | HTTP のヘッダー |
| `body` | 文字列 | HTTP の本文。`json.dumps` で辞書を JSON の文字列に変えたもの（辞書のままではない） |

キーの名前は、Python や Lambda が決めたものではなく、API Gateway が Lambda の戻り値を読むときの決まり（HTTP API の「ペイロード形式バージョン 2.0」）。

| 決めているもの | 決めている内容 |
|---|---|
| Python | 辞書を返せること。キーの名前は自由 |
| Lambda | `lambda_handler` の戻り値を、呼び出し元にそのまま渡すこと |
| API Gateway | 渡された辞書の `statusCode`、`headers`、`body` を読んで、HTTP の返事を作ること |

curl に表示されるのは、`body` の文字列だけ。`tests/test_app.py` のように API Gateway を通さずに呼ぶ場合、戻り値はただの辞書。

### 返事の文字列ができるまで（`?name=test` → `Hello, test!`）

`curl "$URL?name=test"` の返事 `{"message": "Hello, test!"}` は、`src/app.py` の次の行で作られる。

```python
"body": json.dumps({"message": f"Hello, {name}!"}, ensure_ascii=False),
```

`Hello, ` と `!` はこの行に直接書かれている。`test` はコードの中にはなく、URL の `?name=test` から来る。

| 順番 | 場所 | 起きること |
|---|---|---|
| 1 | curl | `GET /hello?name=test` を送る |
| 2 | API Gateway | URL の `?` より後ろを `event["queryStringParameters"]` に入れ、`lambda_handler` を呼ぶ。中身は `{"name": "test"}` |
| 3 | `params = event.get("queryStringParameters") or {}` | `params` が `{"name": "test"}` になる |
| 4 | `name = params.get("name") or "World"` | `name` が `"test"` になる |
| 5 | `f"Hello, {name}!"` | `{name}` に `name` の値が入り、`"Hello, test!"` になる |

`curl "$URL"` のように `?name=...` を付けない場合は、4 で `name` が `"World"` になり、`Hello, World!` が返る。

## 4. お店を建てる仕組み（手順書 7 章の `sam deploy`）

受付、料理人、日誌、社員証を 1 つずつ手で作る代わりに、設計図を渡してまとめて建ててもらう。

デプロイとは、プログラムと、それが動くための仕組み一式を AWS 上に用意し、インターネットから呼び出せる状態にすること。お店でいうと、レシピを渡してお店を建ててもらい、開店することに当たる。`sam deploy` では、次の 2 つが起きる。

1. ビルドしたもの（`app.py` を zip にしたもの）を、SAM 用の S3 バケットに置く（箱を資材置き場に運ぶ）
2. CloudFormation が `template.yaml` どおりに、Lambda、API Gateway、ロググループ、IAM ロールを作る、または更新する（建設会社が設計図どおりにお店を建てる）

開店したお店の窓口（API の URL）はインターネットに公開される。手順書 8 章では Mac の `curl` から呼び出しているが、URL を知っていれば、どの端末からでも呼び出せる。

| AWS の名前 | お店でいうと | 役割 |
|---|---|---|
| `template.yaml` | 設計図 | 「受付 1 つ、料理人 1 人、日誌 1 冊」のように、作るものが書いてある |
| CloudFormation | 建設会社 | 設計図どおりに、全部まとめて建てる。撤去も全部まとめて行う |
| スタック | 建ったお店一式 | このサンプルでは `aws-lambda-minimal` という名前 |
| SAM（Serverless Application Model） | 建設会社への発注を代行する業者 | CloudFormation を Lambda 向けに使いやすくするための道具。サーバーレスのアプリを書くための決まった書き方、という意味の名前。テンプレートの書式（`template.yaml` の `Transform: AWS::Serverless-2016-10-31` がその印）と、`sam` コマンド（SAM CLI。CLI は Command Line Interface の略）の両方を指す。CloudFormation の設計図を短く書け、`sam` コマンドで建設会社に依頼する |
| SAM 用の S3 バケット | 資材置き場 | レシピ（コード）を建設会社に渡すために置いておく場所。`aws-sam-cli-managed-default` スタックとして作られる |

### CloudFormation とは

CloudFormation は AWS のサービスの 1 つで、Lambda や API Gateway と同じく AWS が提供している。作ってほしいリソースを書いたファイル（テンプレート）を受け取り、そこに書いてあるリソースを AWS 上に作る。

| | 内容 | このサンプルでは |
|---|---|---|
| 渡すもの | 作ってほしいリソースを書いたファイル（テンプレート） | `template.yaml` |
| 行うこと | テンプレートを読み、書いてあるリソースを順番に作る | Lambda、API Gateway など 6 つのリソースを作る |
| できるもの | 作ったリソースのまとまり（スタック） | `aws-lambda-minimal` |
| 見る場所 | コンソールの「CloudFormation」の画面 | スタックの一覧に `aws-lambda-minimal` が表示される |

### スタックとリソース

- **リソース**：AWS の上で実際に動いたり、データを持ったりする個々のもの。Lambda の関数、HTTP API、ロググループ、S3 バケットなど。
- **スタック**：CloudFormation が 1 つのテンプレートからリソースを作り、集合としてまとめたもの。スタック自体は動かず、データも持たない。中のリソースを、まとめて作る・変える・消すための管理の単位。

`sam deploy` のとき、CloudFormation は次の順に動く。

1. テンプレートを受け取り、スタックを作る。この時点では、スタックは空の名簿。
2. テンプレートに書いてあるリソースを、1 つずつ作る。
3. 作ったリソースを、そのつどスタックの名簿に書き込む。

「まとめる」は、同じ名簿に載せることを指す。リソースどうしをつないだり、1 か所に集めたりするわけではない。Lambda と API Gateway がつながっているのは、テンプレートにそう書いたからで、スタックとは関係がない。名簿があるので、CloudFormation は更新のときに名簿とテンプレートを比べて変更点（`+ Add`、`* Modify` など）を判断し、削除のときに名簿のリソースをまとめて消せる。

| | リソース | スタック |
|---|---|---|
| 実体 | ある（呼び出せる、データを持つ） | ない（リソースの一覧と管理情報だけ） |
| 例 | `HelloFunction`（Lambda の関数） | `aws-lambda-minimal` |
| 作る方法 | スタック経由でも、コンソールで手で作っても作れる | CloudFormation（`sam deploy`）だけ |
| 関係 | 1 つのスタックに属するか、どのスタックにも属さない | 複数のリソースを持つ |

このサンプルでは、テンプレート 1 つ（`template.yaml`）から、スタック 1 つ（`aws-lambda-minimal`）と、リソース 6 つが作られる。`template.yaml` に書いているのは `HelloFunction` と `HelloFunctionLogGroup` の 2 つで、残りの 4 つは SAM が追加する（手順書 7 章の変更点の一覧の表）。

CloudFormation が受け取るのは、`template.yaml` そのものではない。`sam build` が作った `.aws-sam/build/template.yaml`（コードの場所などを書き換えたもの）を、`sam deploy` が S3 にアップロードして渡す。CloudFormation は `Transform` に従って SAM の書き方を広げてから、リソースを作る。中身のもとは `template.yaml` 。

#### このアカウントのスタック

CloudFormation のコンソールの「スタック」には、次の 2 つが表示される。

| | `aws-lambda-minimal` | `aws-sam-cli-managed-default` |
|---|---|---|
| 何か | このサンプルの本体 | SAM 用のファイル置き場 |
| テンプレート | `template.yaml` | SAM CLI の中に用意されているもの |
| 中のリソース | Lambda の関数、HTTP API、ロググループ、IAM ロールなど 6 つ | S3 バケット（`SamCliSourceBucket`）と、そのアクセス設定（`SamCliSourceBucketBucketPolicy`）の 2 つ |
| 作られたとき | 初回の `sam deploy`（`sam delete` の後は、次の `sam deploy`） | そのリージョンで初めて `sam deploy` を実行したとき |
| 説明の列 | `template.yaml` の `Description` | `Managed Stack for AWS SAM CLI` |
| `sam delete` で | 消える | 消えない（同じリージョンの別の SAM アプリと共用するため） |

`sam deploy` では、SAM がビルドしたコード（zip）とテンプレートを `aws-sam-cli-managed-default` の S3 バケットに置き、CloudFormation がそれを使って `aws-lambda-minimal` のリソースを作る。

ステータスの列の `CREATE_COMPLETE` は「作成に成功し、その後は変更していない」、`UPDATE_COMPLETE` は「作った後に更新され、更新に成功した」という意味。

#### スタック名を決めている場所

スタック名は、テンプレートの中身ではなく、デプロイするときに CloudFormation に渡す値。`template.yaml` には書かれていない。SAM では、次のどれかで渡す。上にあるものほど優先される。

| 渡し方 | 例 |
|---|---|
| コマンドのオプション | `sam deploy --stack-name test-stack` |
| `samconfig.toml` の `stack_name` | `stack_name = "aws-lambda-minimal"` |
| `sam deploy --guided` の質問への答え | `Stack Name [sam-app]: aws-lambda-minimal` |

このサンプルでは、`--guided` の答えが `samconfig.toml` に保存されているので、`samconfig.toml` で指定している形になっている。同じ `template.yaml` から、`--stack-name` で別の名前を渡すと、別のスタックが作られる。`aws-sam-cli-managed-default` は、SAM CLI が決めている固定の名前。`samconfig.toml` の `resolve_s3 = true` が、このスタックの S3 バケットを使う（なければ作る）設定。

### SAM を使うと、必ず CloudFormation が使われる

SAM は、CloudFormation を使ってリソースを作る道具。`sam deploy` を実行すると、必ず CloudFormation が使われる。CloudFormation を使うかどうかを選ぶ設定はなく、どのファイルにも「CloudFormation を使う」という設定は書いていない。

`sam deploy` は `template.yaml` を CloudFormation に渡して、リソースの作成を依頼する。CloudFormation を直接操作することはない。`sam deploy` の実行中に表示される `CREATE_IN_PROGRESS`、`CREATE_COMPLETE` などは、CloudFormation がリソースを作っている途中経過。

設定ではないが、ファイルの中には CloudFormation 用であることを示す記述がある。

| 場所 | 記述 | 意味 |
|---|---|---|
| `template.yaml` | `AWSTemplateFormatVersion: "2010-09-09"` | CloudFormation のテンプレートであることを示す |
| `template.yaml` | `Transform: AWS::Serverless-2016-10-31` | SAM の短い書き方で書いていることを示す。CloudFormation がこれを本来の書き方に展開する |
| `samconfig.toml` | `capabilities = "CAPABILITY_IAM"` | CloudFormation に、IAM ロールを作ることを許可する設定 |

`template.yaml` は、SAM の書き方を使って書いた CloudFormation のテンプレート。

### SAM とは

SAM（Serverless Application Model）は、CloudFormation を Lambda 向けに使いやすくする道具。Amazon のクラウド事業の部門である AWS が開発していて、オープンソースとしてソースコードが GitHub に公開されている（`aws/serverless-application-model`、`aws/aws-sam-cli`）。リソースを実際に作るのは CloudFormation で、SAM はその手前の作業を引き受ける。

| 部分 | 中身 | このサンプルでの例 |
|---|---|---|
| テンプレートの書き方（SAM の書式） | Lambda や API を短く書ける書き方。CloudFormation が `Transform` で本来の書き方に広げる | `template.yaml` の `AWS::Serverless::Function` と `Events: HttpApi` |
| コマンド（SAM CLI） | ビルド、アップロード、デプロイ、削除、ログ表示をまとめて行うコマンド | `sam build`、`sam deploy`、`sam delete`、`sam logs` |

SAM を使わずに CloudFormation だけを使う場合と比べると、次の違いがある。

| 作業 | SAM を使う場合 | CloudFormation だけの場合 |
|---|---|---|
| テンプレート | 2 つのリソースを書く | 6 つのリソースをすべて自分で書く（IAM ロールの権限、API の設定、呼び出し許可など） |
| コードの準備 | `sam build` がまとめる | 自分で zip にする |
| アップロード | `sam deploy` が S3 に置く | S3 バケットを自分で作り、zip を自分で置く |
| デプロイ | `sam deploy` | `aws cloudformation deploy --stack-name ...` |
| 設定の保存 | `samconfig.toml` | 毎回コマンドに書く |

お店でいうと、CloudFormation が建設会社で、SAM は建設会社への発注を代行する業者。設計図を短く書けるようにし、材料（コード）の運び込みも引き受ける。最後に建てるのは、どちらの場合も CloudFormation 。

#### 対応する範囲

SAM は AWS だけに対応している。リソースを実際に作る CloudFormation が、AWS のリソースを作るための AWS のサービスのため。SAM で Azure や Google Cloud のリソースは作れない。

AWS の中でも、SAM の短い書き方が使えるのは、Lambda、API Gateway などのサーバーレスのリソースだけ。ほかの AWS のリソース（データベースやネットワークなど）も、CloudFormation の書き方で同じテンプレートに書けば作れる。

| 道具 | 対応する範囲 |
|---|---|
| SAM | AWS のみ（サーバーレス向けの短い書き方がある） |
| CloudFormation | AWS のみ |
| Terraform | AWS、Azure、Google Cloud、GitHub など（[terraform.md](terraform.md)） |

CloudFormation 以外の道具で AWS のリソースを作る方法もある（Terraform など）。その場合は SAM を使わず、その道具を使う。README の「次のステップ」にある Terraform 版が、それに当たる。Terraform と SAM の違いは [terraform.md](terraform.md) にある。

### 手でリソースを作る場合との違い

CloudFormation（SAM）を使わずにリソースを作る方法として、コンソールで 6 つのリソース（Lambda、IAM ロール、ロググループ、HTTP API、ステージ、呼び出し許可）を 1 つずつ手で作る方法がある。その場合と比べると、次の違いがある。

| | 手で作る場合 | CloudFormation を使う場合 |
|---|---|---|
| 作る | 画面を何度も操作する。作る順番（IAM ロール → Lambda → ロググループなど）も自分で考える | `template.yaml` に書いた内容で、順番も含めてまとめて作られる（`sam deploy` の出力に、作られた順番が表示される） |
| 消す | 1 つずつ探して消す。消し忘れると、料金がかかり続ける場合がある | スタックを削除すると、中身もまとめて消える（`sam delete`） |
| もう一度作る | 手順を覚えていないと、同じものを再現できない | 同じテンプレートから、何度でも同じものが作られる（手順書 10 章で消した後に、同じものを作り直せる） |
| 変更する | どこを変えたかを自分で管理する | 変更前に、増える・変わる・消えるリソースの一覧（変更セット）が表示される |

インフラ（サーバーや API などの仕組み）を、このようにファイル（コード）で管理する方法を IaC（Infrastructure as Code）と呼ぶ。CloudFormation と SAM は、AWS の IaC の道具。`sam deploy` は、SAM の書式で短く書いたテンプレートを CloudFormation の書式に展開して、CloudFormation に渡す。リソースを実際に作るのは CloudFormation 。

### 設計図の中の呼び名（HelloFunction など）

`sam deploy` の出力やコンソールに出る `HelloFunction`、`HelloFunctionRole` などは、AWS が決めた用語ではなく、設計図（`template.yaml`）の中でのリソースの呼び名。CloudFormation では LogicalResourceId と呼ぶ。

#### 自分で付けた呼び名

`template.yaml` に書いている名前。英単語をつなげて付けていて、別の名前に変えても動く。

```yaml
Resources:
  HelloFunction:            # 「Hello を返す関数（Function）」の意味で付けた名前
    Type: AWS::Serverless::Function
    ...
      Events:
        HelloApi:           # 「Hello の API」の意味で付けたイベントの名前
          Type: HttpApi

  HelloFunctionLogGroup:    # 「HelloFunction のロググループ」の意味で付けた名前
    Type: AWS::Logs::LogGroup
```

#### SAM が自動で付ける呼び名

SAM が自動で追加するリソースには、上の名前に役割を表す単語をつなげた名前が付く。後ろの単語を見ると、何のためのリソースかが分かる。

| 呼び名 | 分解すると | 意味 |
|---|---|---|
| `HelloFunctionRole` | `HelloFunction` + `Role` | HelloFunction の IAM ロール（社員証） |
| `HelloFunctionHelloApiPermission` | `HelloFunction` + `HelloApi` + `Permission` | HelloApi が HelloFunction を呼び出してよいという許可 |
| `ServerlessHttpApi` | SAM が使う決まった名前 | SAM が作る HTTP API（受付の窓口） |
| `ServerlessHttpApiApiGatewayDefaultStage` | `ServerlessHttpApi` + `ApiGateway` + `DefaultStage` | その HTTP API の標準のステージ（営業設定） |

#### AWS 上の実際の名前

呼び名は設計図の中だけで使う名前。AWS 上のリソースには、スタック名と呼び名を元に、別の名前が付く。

```
設計図の中の呼び名   HelloFunction
AWS 上の名前         aws-lambda-minimal-HelloFunction-XXXXXXXXXXXX
                     ^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^ ^^^^^^^^^^^^
                     スタック名          呼び名         ランダムな文字列
```

コンソールの Lambda の画面には、AWS 上の名前で表示される。ランダムな文字列の部分は、`sam delete` の後にデプロイしてスタックを作り直すと変わる。スタックがある状態での再デプロイ（更新）では変わらない。

### 設計図の中の `${...}`（`!Sub`）

`template.yaml` では、`!Sub` を付けた文字列の中の `${...}` が、デプロイのときに実際の値に置き換わる。

`!Sub`、`!Ref`（CloudFormation の組み込み関数）や `${AWS::Region}`（擬似パラメータ）は、YAML の機能ではなく、CloudFormation の機能。`template.yaml` は CloudFormation のテンプレートなので、デプロイのときに CloudFormation が読んで置き換える。CloudFormation が読まない YAML ファイル（GitHub Actions の設定ファイルなど）に同じように書いても、置き換わらない。

```yaml
Value: !Sub https://${ServerlessHttpApi}.execute-api.${AWS::Region}.amazonaws.com/hello
```

`${...}` に入る名前は、次の 3 種類。

| 書き方 | 何を指すか | 定義している場所 | このサンプルでの値の例 |
|---|---|---|---|
| `${HelloFunction}` | `template.yaml` の `Resources:` に書いた呼び名 | `template.yaml` | Lambda の実際の名前（`aws-lambda-minimal-HelloFunction-...`） |
| `${ServerlessHttpApi}` | SAM が自動で作るリソースの呼び名 | SAM（`Events` の `HttpApi` から作られる） | API の ID（`xxxxxxxxxx` のような 10 文字の英数字） |
| `${AWS::Region}` | 擬似パラメータ | CloudFormation が最初から用意している（どこにも書かない） | デプロイ先のリージョン（`ap-southeast-2`） |

擬似パラメータ（Pseudo Parameter）は、CloudFormation がスタックを作るときに自動で値を入れる変数。宣言しなくても、どのテンプレートでも使える。名前は `AWS::` で始まる。主なものは次のとおり。

| 擬似パラメータ | 入る値 |
|---|---|
| `AWS::Region` | スタックを作るリージョン。このサンプルでは `samconfig.toml` の `region` で指定したもの |
| `AWS::AccountId` | AWS アカウントの ID |
| `AWS::StackName` | スタック名 |

URL にリージョンを直接書かずに `${AWS::Region}` を使っているのは、別のリージョンにデプロイしたときにも正しい URL になるようにするため。

参考: [Pseudo parameters reference（AWS 公式）](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/pseudo-parameter-reference.html)

## 5. コマンドが何をしているか

手順書で使う順に並べている。`sam deploy --guided` と `sam deploy` は、手順書 7 章の A と B に当たり、どちらか 1 つを使う（違いは表の後にある）。

| コマンド | 章 | お店でいうと |
|---|---|---|
| `pytest` | 6 | 開店前に、レシピどおり作れるかを台所で試作する（AWS は使わない） |
| `sam build` | 7 | レシピと設計図を、建設会社に渡せる形に箱詰めする（Mac の中だけで行う） |
| `sam deploy --guided` | 7（A） | 箱を資材置き場に運び、建設会社に「この設計図で建てて」と依頼する。`--guided`（案内付き）を付けたので、店名や場所などを窓口で 1 つずつ聞かれる。答えは `samconfig.toml` に控えとして残る。初めてデプロイするときは、こちらを使う |
| `sam deploy` | 7（B）、9 | 控え（`samconfig.toml`）の店名や場所を使って、建設会社に依頼する。控えがあるので、もう一度聞かれることはない。お店があれば改装になり、スタックの状態は `UPDATE_COMPLETE` になる。お店がなければ（`sam delete` の後など）新しく建てて、`CREATE_COMPLETE` になる。2 回目以降は、こちらを使う |
| `curl` | 8 | 客として窓口に注文してみる |
| `sam delete` | 10 | 建設会社に、お店を丸ごと撤去するよう依頼する。資材置き場は残る（手順書 10 章の手順で、手で片付けることもできる） |

### `--guided` を付ける場合と付けない場合

`--guided` は「案内付き」という意味のオプション。お店でいうと、建設会社に初めて依頼するときの「申込書の記入」に当たる。

| | `sam deploy --guided` | `sam deploy` |
|---|---|---|
| お店でいうと | 窓口で担当者に聞かれながら、申込書（店名、場所、社員証を作ってよいか など）を書く | 前回の申込書の控えを見せて、「前と同じで」と依頼する |
| 質問 | 出る | 出ない |
| 使う設定 | その場で答えた内容。答えは控え（`samconfig.toml`）に保存される | 控え（`samconfig.toml`）の内容 |
| 使う場面 | 初めてデプロイするとき、設定を変えたいとき、控えがないとき | 2 回目以降（スタックを `sam delete` で消した後も含む） |

控えがない状態で `--guided` を付けずに `sam deploy` を実行すると、店名などが決まっていないため、デプロイできずにエラーになる。

## 6. 準備の章（手順書 1〜5 章）

| 手順書の章 | お店でいうと |
|---|---|
| 2 章：AWS アカウント（プロジェクト）の作成 | お店を建てる土地を借りる契約 |
| 3 章：MFA の設定 | 土地の鍵を二重にする |
| 4 章：費用の確認 | 契約の残高（クレジット）と期限を確かめる |
| 5 章：`aws login` | Mac から建設会社に依頼できるように、本人確認を済ませる |

## 7. プロジェクト、AWS アカウント、リージョン、スタック、リソースの関係

新しい登録方式では、入れ物が次の順に入れ子になっている。

```text
AWS Builder ID > プロジェクト > AWS アカウント > リージョン > （スタック） > リソース
```

- **AWS Builder ID**：AWS にログインするための個人のアカウント。1 つの Builder ID で、プロジェクトを複数作れる（AWS 設定の「プロジェクト」の画面の「プロジェクトを作成」）。
- **プロジェクト**：新しい登録方式で、開発のための作業場をまとめる単位。AWS アカウントを 1 つ持っている。このサンプルでは「Just Ship It」が 1 つある。
- **AWS アカウント**：リソースを入れる入れ物。持ち主、権限、費用の単位になる。番号（アカウント ID）は 12 桁の数字。
- **リージョン**：AWS のデータセンターがある地域。リソースは、どこか 1 つのリージョンに作られる。新しい登録方式のアカウントは、決まった 1 つのリージョン（このサンプルではシドニー `ap-southeast-2`）だけを使える。
- **スタック**：CloudFormation が 1 つのテンプレートからリソースを作り、集合としてまとめたもの（4 章の「スタックとリソース」）。
- **リソース**：AWS の上に作った個々のもの。Lambda の関数、ロググループ、HTTP API、IAM ロール、S3 バケットなど。

```text
AWS Builder ID
└─ プロジェクト「Just Ship It」
   └─ AWS アカウント
      └─ リージョン ap-southeast-2
         ├─ スタック aws-lambda-minimal
         │    ├─ HelloFunction（Lambda の関数）
         │    ├─ HelloFunctionLogGroup（ロググループ）
         │    └─ ……ほか 4 つ
         ├─ スタック aws-sam-cli-managed-default
         │    ├─ S3 バケット
         │    └─ バケットのアクセス設定
         └─ （スタックに属さないリソース：AWS が最初から作った AccountFullAccessRole など）
```

### スタックが括弧付きの理由

SAM や CloudFormation で作ったリソースは、すべてどれかのスタックに属する。このサンプルで作ったリソースに限れば、「リージョン > スタック > リソース」で考えられる。ただし、スタックは必須の段ではない。

| | 「リージョン > スタック > リソース」で合うか |
|---|---|
| SAM や CloudFormation で作ったリソース | 合う |
| コンソールで手で作ったリソース | 合わない。スタックを通らず、リージョンの直下にある |
| AWS が最初から作ったもの（`AccountFullAccessRole` など） | 合わない。どのスタックにも属さない |

スタック自体も、リージョンに属するリソースの 1 つ（CloudFormation のリソース）。IAM ロールは例外で、リージョンに属さず、アカウント全体で 1 つのリソース。

### AWS アカウントは何の単位か

| 単位 | 意味 |
|---|---|
| 持ち主 | リソースはすべて、作ったアカウントのもの。別のアカウントからは、許可しない限り見えない |
| 権限 | 誰が何を操作できるかは、アカウントの中の IAM で決める。`aws login` で使う `AccountFullAccessRole` は、このアカウントの中のリソースをすべて操作できる |
| 費用 | 費用はアカウントごとにまとめられる。クレジットも、このアカウントの使用分から引かれる |
| 名前 | 同じ種類のリソースの名前は、同じアカウントの同じリージョンの中で重ならない |

リソースがどのアカウントとリージョンのものかは、リソースの ID（ARN、Amazon Resource Name）に入っている。ロググループの ARN の例。

```text
arn:aws:logs:ap-southeast-2:<アカウント ID>:log-group:/aws/lambda/aws-lambda-minimal-HelloFunction-...
             ^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^
             リージョン       アカウント ID
```

ARN にはアカウント ID が入るが、プロジェクトの名前は入らない。

### プロジェクトと AWS アカウントが分かれている理由

プロジェクトと AWS アカウントは 1 対 1 で、使う側から見るとほぼ同じもの。2 つに分かれている理由は、次のように考えられる（AWS の公式の説明ではなく、仕組みからの解釈）。

- AWS アカウントは AWS が始まったときからある仕組みで、権限（IAM）、費用、ARN、制限（SCP）など、すべてのサービスがアカウント ID を前提に作られている。
- プロジェクトは、新しい登録方式（2026 年 9 月から）で、既存のアカウントを包む外側の枠として加わった。
- プロジェクトには、アカウントにない情報が付く。チームメンバーとの共有、Free プランとクレジット、リージョンの制限など。
- 「高度な機能をアクティブ化する」と、中のアカウントは従来のアカウントと同じ扱いになる。そのときも同じアカウントが使われ続けるので、作ったリソースはそのまま残る。

AWS の各サービスから見える単位は AWS アカウントで、プロジェクトは人が管理するための枠。
