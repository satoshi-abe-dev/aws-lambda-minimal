# Terraform のメモ

このサンプルは SAM（CloudFormation）でリソースを作っている。求人でよく見かける IaC（Infrastructure as Code。インフラを、画面の操作ではなくファイル（コード）に書いて作る方法）の道具である Terraform について、SAM と比べながらまとめたメモ。README の「次のステップ」にある Terraform 版を作るときの下調べを兼ねている。

内容は 2026 年半ばまでの情報に基づく。このリポジトリでは、Terraform をまだ実際には動かしていない。

## Terraform とは

インフラをファイル（コード）で管理する IaC の道具。作りたいリソースを `.tf` ファイルに書くと、Terraform がその通りにリソースを作る。

| 項目 | 内容 |
|---|---|
| 開発元 | HashiCorp（2014 年に公開。HashiCorp は 2025 年に IBM に買収された） |
| 書き方 | HCL（HashiCorp Configuration Language）という専用の言語 |
| 対応するクラウド | AWS、Azure、Google Cloud など。「プロバイダ」というプラグインで、クラウドごとの操作に対応する |
| 使い方 | `terraform` コマンド |
| ライセンス | 2023 年に、オープンソースのライセンス（MPL 2.0）から、商用の利用に制限のあるライセンス（BSL 1.1）に変わった |
| OpenTofu | ライセンスの変更をきっかけに、変更前の Terraform から分かれたオープンソース版。Linux Foundation が管理していて、使い方はほぼ同じ |

## 求人でよく見かける理由

- AWS 以外のクラウドや、GitHub、Datadog などのサービスも、同じ書き方で管理できる。複数のクラウドを使う会社でも、1 つの道具で済む。
- 利用者が多く、情報やモジュール（再利用できる部品）が多い。
- インフラ全体を管理するチーム（SRE、プラットフォームエンジニアリングなど）で、標準の道具として使われていることが多い。

## 複数のクラウドやサービスを扱う場面

Terraform で複数のプロバイダを使う理由で多いのは、クラウドどうしをつなぐことではなく、1 つのクラウドと、その周りのサービスをまとめて管理すること。

### 1. 1 つのクラウドと、周りのサービス（よくある）

アプリは AWS だけで動かし、AWS の外のサービスも同じ Terraform で設定する。

| サービス | Terraform で設定するもの |
|---|---|
| AWS | Lambda、データベースなど |
| Cloudflare | ドメインの DNS（API の URL を独自のドメインにする） |
| GitHub | リポジトリ、メンバーの権限 |
| Datadog | 監視、アラート |

あるプロバイダで作ったリソースの値を、別のプロバイダの設定に渡せる。たとえば、AWS で作った API の URL を、Cloudflare の DNS のレコードに入れられる。この場合も、処理が流れるのは AWS の中だけ。

### 2. 複数のクラウドを、それぞれ別の用途で使う（ある）

つながってはいるものの、役割が分かれている例。

- アプリは AWS で動かし、データの分析は Google Cloud の BigQuery で行う
- アプリは AWS で動かし、AI のモデルは Azure の Azure OpenAI を呼ぶ
- 会社の合併で、部署ごとに使っているクラウドが違う

### 3. 同じ処理を複数のクラウドで動かす（少ない）

1 つのクラウドが止まっても動き続けるように、同じアプリを AWS と Google Cloud の両方に置く形。費用も手間もかかるため、行っている会社は多くない。

### まとめ

複数のクラウドを 1 つの道具で扱えることの利点は、クラウドどうしをつなぐことよりも、扱う対象が増えても道具と書き方が 1 つで済むことにある。

## SAM（CloudFormation）との違い

| | SAM（CloudFormation） | Terraform |
|---|---|---|
| リソースを作るもの | AWS の CloudFormation（AWS の中で動く） | 手元の `terraform` コマンドが、AWS の API を直接呼ぶ。CloudFormation は使わない |
| 対応するクラウド | AWS だけ | 複数のクラウドとサービス |
| 書き方 | YAML（SAM の短い書き方） | HCL |
| 作ったものの記録 | スタック（AWS の中に保存される） | 状態ファイル `terraform.tfstate`（標準では手元に保存される） |
| 変更前の確認 | 変更セット（`Deploy this changeset? [y/N]`） | `terraform plan` |
| 作る・更新する | `sam deploy` | `terraform apply` |
| まとめて消す | `sam delete` | `terraform destroy` |
| 名前などの設定 | `samconfig.toml` | 変数（`variables.tf`、`terraform.tfvars`） |
| Lambda 向けの省略 | ある（`AWS::Serverless::Function` から IAM ロールや API が自動で作られる） | ない。必要なリソースをすべて書く |
| AWS のコンソール | CloudFormation の画面にスタックが表示される | CloudFormation の画面には何も表示されない。リソースはそれぞれのサービスの画面に表示される |

## 状態ファイル（state）

Terraform で最も注意が必要な点。

- Terraform は、作ったリソースを `terraform.tfstate` というファイルに記録する。CloudFormation のスタックの名簿に当たる。
- 次の `terraform plan` や `apply` では、このファイルと `.tf` ファイルと実際の AWS を比べて、変更点を決める。
- 標準では手元に保存される。このファイルを失うと、Terraform は作ったリソースを管理できなくなる。
- 中にパスワードなどの値が入ることがあるため、Git には入れない（`.gitignore` に `*.tfstate` を書く）。
- チームで使う場合は、S3 などの共有の場所に置く（「リモートバックエンド」と呼ぶ）。同時に 2 人が変更しないように、ロック（排他制御）も使う。

SAM（CloudFormation）では、この記録を AWS がスタックとして持つので、手元で管理する必要がない。

## 基本のコマンド

| コマンド | 内容 |
|---|---|
| `terraform init` | 最初に 1 回実行する。プロバイダ（AWS 用のプラグインなど）をダウンロードする |
| `terraform fmt` | `.tf` ファイルの書式を整える |
| `terraform validate` | 書き方に誤りがないかを確かめる |
| `terraform plan` | 何が作られる・変わる・消えるかを表示する。AWS は変更しない |
| `terraform apply` | 変更点を表示し、`yes` と答えると AWS に反映する |
| `terraform destroy` | 作ったリソースをすべて消す |

## このサンプルを Terraform で書く場合

SAM では `template.yaml` に 2 つのリソースを書けば、残りを SAM が追加する。Terraform では、次のリソースをすべて自分で書く。

| Terraform のリソース | 中身 | SAM での対応 |
|---|---|---|
| `aws_iam_role` | Lambda の IAM ロール | `HelloFunctionRole`（SAM が追加） |
| `aws_iam_role_policy_attachment` | ロールに、ログを書く権限（`AWSLambdaBasicExecutionRole`）を付ける | 同上 |
| `aws_lambda_function` | Lambda の関数 | `HelloFunction` |
| `aws_cloudwatch_log_group` | ロググループ（7 日で削除） | `HelloFunctionLogGroup` |
| `aws_apigatewayv2_api` | HTTP API | `ServerlessHttpApi`（SAM が追加） |
| `aws_apigatewayv2_integration` | API と Lambda をつなぐ設定 | `Events: HttpApi` から SAM が作る |
| `aws_apigatewayv2_route` | `GET /hello` の経路 | 同上 |
| `aws_apigatewayv2_stage` | API を公開するステージ | `ServerlessHttpApiApiGatewayDefaultStage`（SAM が追加） |
| `aws_lambda_permission` | API Gateway が Lambda を呼んでよいという許可 | `HelloFunctionHelloApiPermission`（SAM が追加） |

コードの zip も、`sam build` の代わりに自分で作る。Terraform の `archive_file`（`hashicorp/archive` プロバイダ）を使うと、`terraform apply` のときに `src/` を zip にできる。

Lambda の関数の部分は、たとえば次のような書き方になる（動かして確かめたものではない）。

```hcl
resource "aws_lambda_function" "hello" {
  function_name = "aws-lambda-minimal-hello"
  role          = aws_iam_role.lambda.arn
  handler       = "app.lambda_handler"
  runtime       = "python3.14"
  architectures = ["arm64"]
  memory_size   = 128
  timeout       = 10

  filename         = data.archive_file.src.output_path
  source_code_hash = data.archive_file.src.output_base64sha256
}
```

`aws_iam_role.lambda.arn` のように、ほかのリソースを「種類.名前.属性」で参照する。CloudFormation の `!Ref` や `!GetAtt` に当たる。

## このアカウントで使う場合の確かめること

Terraform 版を作るときに、次の点を確かめる必要がある。どれもまだ確かめていない。

- **認証**：`aws login` の認証情報を、Terraform の AWS プロバイダがそのまま読めるか。読めない場合は、`aws configure export-credentials --format env` で一時的な認証情報を環境変数にする方法がある。
- **ランタイム**：AWS プロバイダのバージョンが、`python3.14` のランタイムに対応しているか。
- **リージョン**：プロバイダの `region` を `ap-southeast-2` にする。ほかのリージョンは SCP で拒否される。
- **状態ファイルの置き場所**：1 人で学習する範囲なら手元でよい。S3 に置く場合は、そのバケットを先に作る必要がある。

## 参考

- [Terraform のドキュメント（HashiCorp）](https://developer.hashicorp.com/terraform/docs)
- [AWS プロバイダのドキュメント（Terraform Registry）](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [OpenTofu](https://opentofu.org/)
