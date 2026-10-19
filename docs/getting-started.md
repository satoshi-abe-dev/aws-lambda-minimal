# 手順書：AWS アカウントの作成からデプロイ、後片付けまで

AWS を初めて使う人が、このリポジトリのサンプルを AWS にデプロイし、動作を確かめ、最後に削除するまでの手順。
作業する PC は macOS（Homebrew 導入済み）を想定している。

料金や無料枠、画面の情報は、2026 年 10 月時点の AWS 公式ドキュメントと実際の画面で確かめた内容。AWS の料金や画面は変わることがある。

## この手順書が前提にしている登録方式

AWS への登録方法は 2 種類ある。この手順書は、2026 年 9 月に始まった **新しい登録方式（Sign up for AWS (new)、プロジェクト方式）** を前提にしている。

| | 新しい登録方式（この手順書） | 従来の登録方式（advanced） |
|---|---|---|
| ログイン | Google、GitHub、Apple、Amazon のアカウント、またはメールアドレス（AWS Builder ID） | ルートユーザー（メールアドレスとパスワード） |
| リージョン | 連絡先の国によって自動で決まり、変えられない | 自由に選べる |
| 作業用ユーザー | 不要（AWS が管理者の権限を用意する） | IAM ユーザーや IAM Identity Center で作る |
| 画面 | コンソールのホームに「プロジェクト管理」ボタンがあり、右上にリージョンの切り替えがない | 右上にリージョンの切り替えがある |

従来の登録方式のアカウントでも、5 章以降（CLI、ローカルでのテスト、デプロイ、動作確認、後片付け）は同じ手順で進められる。その場合、2〜4 章の代わりに AWS 公式の [Sign up for AWS (advanced)](https://docs.aws.amazon.com/accounts/latest/reference/getting-started.html) の手順で、MFA と作業用ユーザーを用意する。

## 全体の流れ

この手順書では、小さなプログラムを AWS（Amazon のクラウド）に載せ、インターネットから呼び出せることを確かめ、最後に AWS から消すまでを一通り行う。

載せるプログラムは、URL に名前を付けて呼び出すと挨拶を返すだけのもの。

```
https://<デプロイで作られる URL>/hello?name=test  →  {"message": "Hello, test!"}
```

| 章 | やること | 何のためか |
|---|---|---|
| 1 | 用語を知る | 以降の説明に出てくる言葉を先に押さえる |
| 2 | AWS アカウントを作る | AWS を使うための契約。Free プランで始める |
| 3 | MFA を設定する | パスワードが漏れても、他人がログインできないようにする |
| 4 | 費用の確認方法を知る | 残りのクレジットと期限を、いつでも確かめられるようにする |
| 5 | CLI を入れて、ログインする | Mac のターミナルから AWS を操作できるようにする |
| 6 | 手元でテストする | AWS に載せる前に、プログラムが正しく動くかを確かめる |
| 7 | デプロイする | プログラムを AWS に載せ、インターネットから呼び出せる状態にする |
| 8 | 呼び出して確かめる | AWS 上で本当に動いているかを、curl とコンソールで確かめる |
| 9 | 直して載せ直す | 「コードを変える → もう一度デプロイする」流れを体験する |
| 10 | 後片付けをする | 作ったものを AWS から消し、誰でも呼び出せる API を残さない |
| 11 | エラーの対処を調べる | うまくいかないときに参照する |

使う AWS のサービスとコマンドが何をしているかは、お店にたとえた説明が [how-it-works.md](how-it-works.md) にある。

1〜5 章は最初の 1 回だけの準備。6〜9 章は、コードを変えるたびに繰り返す流れ。10 章は、使い終わったときに行う。

終わったときの状態は次のとおり。

- **手元**: このリポジトリのファイルと、AWS へのログイン設定（`~/.aws/`）が残る
- **AWS**: 10 章でサンプルのスタックは消える。SAM 用のファイル置き場（`aws-sam-cli-managed-default`）は `sam delete` では消えずに残る。10 章の「バケットを消す手順」で消すと、何も残らない
- **費用**: Free プランのため請求は発生しない。動作確認の範囲では、クレジットもほとんど減らない

## 目次

1. [AWS の基本用語](#1-aws-の基本用語)
2. [AWS アカウントの作成](#2-aws-アカウントの作成)
3. [MFA（Multi-Factor Authentication、多要素認証）の設定](#3-mfamulti-factor-authentication多要素認証の設定)
4. [費用の確認](#4-費用の確認)
5. [CLI のインストールとログイン](#5-cli-のインストールとログイン)
6. [ローカルでのテスト](#6-ローカルでのテスト)
7. [デプロイ](#7-デプロイ)
8. [動作確認](#8-動作確認)
9. [コードを変更して再デプロイする](#9-コードを変更して再デプロイする)
10. [後片付け](#10-後片付け)
11. [よくあるエラーと対処](#11-よくあるエラーと対処)

---

## 1. AWS の基本用語

| 用語 | 説明 |
|---|---|
| AWS（Amazon Web Services） | Amazon のクラウドサービスの総称。Lambda、API Gateway などのサービスの集まり |
| プロジェクト | 新しい登録方式で、作ったリソースをまとめておく単位。1 つのプロジェクトに 1 つの AWS アカウントが入っている。登録すると最初のプロジェクトが自動で作られる。1 つの AWS Builder ID で、プロジェクトを複数作れる。従来の登録方式にはプロジェクトという単位はなく、登録すると AWS アカウントが 1 つ作られ、リソースはそこに直接置く |
| AWS Settings | プロジェクトの管理、MFA、支払い方法などを設定する画面（<https://settings.aws.com>）。コンソールのホームの「プロジェクト管理」からも開ける |
| AWS Builder ID | ID は Identifier（識別子）の略。新しい登録方式で AWS にログインするための個人のアカウント。登録時に作られる |
| リージョン | AWS のデータセンターがある地域。新しい登録方式では、プロジェクトのリージョンが連絡先の国によって自動で決まる（米国東部（オハイオ）`us-east-2`、欧州（ストックホルム）`eu-north-1`、アジアパシフィック（シドニー）`ap-southeast-2` のどれか）。この手順書では例として `ap-southeast-2` を使う |
| IAM（Identity and Access Management） | AWS の利用者と権限を管理するサービス。「誰が」「何をしてよいか」を決める。このサンプルでは、Lambda が動くための権限（IAM ロール）を SAM が自動で作る |
| Lambda | 関数（プログラム）を置いておくと、呼ばれたときだけ実行するサービス。サーバーの管理が要らない（意味は [how-it-works.md](how-it-works.md) の 1 章にある）。実行した回数と時間に応じて課金される |
| API Gateway（正式な名前は Amazon API Gateway） | AWS のサービスには「Amazon」か「AWS」で始まる正式な名前があり、普段は頭を省いて呼ぶ（AWS Lambda、AWS CloudFormation、Amazon CloudWatch など）。API Gateway も同じで、AWS のサービスの 1 つ。API は Application Programming Interface の略で、プログラムどうしがやり取りするための窓口。HTTP は Hypertext Transfer Protocol の略で、Web でデータをやり取りするときの決まり。インターネットからの HTTP リクエストを受け付けて、Lambda などに渡すサービス。このサンプルでは「HTTP API」という種類を使う |
| CloudWatch Logs | プログラムのログ（`print` の出力やエラー）を保存するサービス |
| S3（正式な名前は Amazon S3。Simple Storage Service の略） | ファイルを保存するサービス。ファイルを入れる入れ物を「バケット（bucket）」と呼ぶ。このサンプルでは、`sam deploy` がコードの zip とテンプレートを置く場所として使う。「3」はバージョンや番号ではなく、**S**imple **S**torage **S**ervice の S が 3 つ並ぶことを表す（S1、S2 というサービスはない）。仮想サーバーの EC2（**E**lastic **C**ompute **C**loud、C が 2 つ）も同じ付け方 |
| CloudFormation | 作りたいリソース（Lambda、API Gateway など）を設定ファイルに書くと、その通りにまとめて作るサービス。まとめて作ったものを「スタック」と呼び、スタックを削除すると中身もまとめて消える。このようにインフラをファイル（コード）で管理する方法を IaC（Infrastructure as Code）と呼ぶ。手で作る場合との違いは [how-it-works.md](how-it-works.md) にある |
| スタック | CloudFormation が 1 つのテンプレートからリソースを作り、集合としてまとめたもの。このサンプルでは `template.yaml` から `aws-lambda-minimal` というスタックが作られる。リソースとの違いは [how-it-works.md](how-it-works.md) の 4 章にある |
| リソース | AWS の上に作った個々のもの（Lambda の関数、ロググループ、HTTP API など） |
| デプロイ | プログラムと、それが動くための仕組み一式（Lambda、API Gateway など）を AWS 上に用意し、インターネットから呼び出せる状態にすること。このサンプルでは `sam deploy` で行う。ビルドしたものを S3 に置き、CloudFormation が `template.yaml` どおりにリソースを作る（または更新する）。できた API の URL は公開され、URL を知っていれば誰でも、どの端末からでも呼び出せる |
| SAM（Serverless Application Model） | CloudFormation を Lambda 向けに使いやすくするための道具。AWS が開発しているオープンソース。CloudFormation の書き方を短くした書式（このリポジトリの `template.yaml`）と、ビルドからデプロイ、削除までをまとめて行うコマンド（`sam`）の 2 つからなる。リソースを実際に作るのは CloudFormation |

プロジェクト、AWS アカウント、リージョン、スタック、リソースの入れ子の関係は、[how-it-works.md](how-it-works.md) の 7 章にある。

## 2. AWS アカウントの作成

1. <https://signin.aws.amazon.com/signup?request_type=builderId> を開く。
2. メールアドレスを入力するか、Google、GitHub、Apple、Amazon のいずれかのアカウントを選ぶ。
3. 名前、メールアドレスの確認コード、パスワード、連絡先を入力する。
4. 支払い情報を求められた場合は登録する。確認のため 1 USD（または相当額）が 3〜5 日間仮押さえされる。Free プランでは請求は発生しない。
5. 最初のプロジェクトが自動で作られ、コンソールのホームが開く。

参考: [Sign up for AWS (new)（AWS 公式）](https://docs.aws.amazon.com/accounts/latest/reference/sign-in-new.html)

### 初回に表示される案内

初めてコンソールを開くと、「AWS へようこそ。まずエージェントを接続しましょう。」という案内（ステップ 1/3）が表示される。Claude Code や Kiro などの AI エージェントを AWS につなぐための案内。この手順書では使わないため、右上の × で閉じても進められる。

### プロジェクトの名前

最初のプロジェクトには、AWS が自動で名前を付ける。この手順書を作ったときのアカウントでは「Just Ship It」だった（英語で「とにかく出荷しよう」という意味の決まり文句）。付けられる名前は、アカウントによって異なる場合がある。

コンソールの右上（例:「Just Ship It ▼」）や、ホームの見出し（例:「コンソールのホーム | Just Ship It」）に表示されているのは、このプロジェクトの名前。

名前は、コンソールのホームの「プロジェクト管理」（AWS Settings）からいつでも変えられる。名前を変えても、プロジェクトの中身や動作は変わらない。

### AWS Builder ID を確かめる

登録すると、AWS Builder ID（AWS 用の個人のアカウント）が自動で作られる。コンソール、AWS Settings、5 章の `aws login` は、すべてこの Builder ID でログインする。

Builder ID の内容は、次のどちらかで開くプロフィールページで確かめられる。

- <https://profile.aws.amazon.com> を開く
- AWS Settings（<https://settings.aws.com>、コンソールのホームの「プロジェクト管理」からも開ける）の左のメニューで「Manage security and sign-in」を選ぶ

プロフィールページの「詳細」には、次の項目がある。

| 項目 | 内容 |
|---|---|
| 名前 | 登録した名前。プロジェクトを他の人と共有したとき、相手に表示される |
| ニックネーム | 画面の右上に出る表示名 |
| メールアドレス | Builder ID を区別するもの |

画面には「Builder ID」という名前の項目や ID 番号はない。Builder ID は 1 つのメールアドレスにつき 1 つで、メールアドレスで区別される。Google、GitHub、Apple、Amazon のアカウントで登録した場合は、そのアカウントのメールアドレスが入っている。

左のメニューの「セキュリティ」では、Builder ID の MFA（3 章）を確かめられる。

### プロジェクトのリージョンを確かめる

コンソールのアドレスバーの URL に、プロジェクトのリージョンが入っている。

```
https://<アカウントID>-xxxxxxxx.ap-southeast-2.console.aws.amazon.com
                               ^^^^^^^^^^^^^^ ここがリージョン
```

新しい登録方式で使えるリージョンは、米国東部（オハイオ）`us-east-2`、欧州（ストックホルム）`eu-north-1`、アジアパシフィック（シドニー）`ap-southeast-2` の 3 つで、連絡先の国によってどれかに決まる。東京 `ap-northeast-1` はこの 3 つに含まれない。この手順書を作ったときのアカウントは、日本の住所で登録し、**シドニー（`ap-southeast-2`）** になった。登録の途中でリージョンを選ぶ画面はない。

シドニーは東京より日本から遠いため、応答が少し遅くなる。動作確認の用途では影響はほとんどない。料金は Free プランのため、リージョンによらず請求は発生しない。

このリージョンは変えられない。別のリージョン（例えば東京 `ap-northeast-1`）の画面を開くと、「リージョン アジアパシフィック (東京) は利用できません」と表示される。その場合は「Return to（プロジェクトのリージョン）」を選ぶと元に戻る。

同じ画面にある「高度な機能をアクティブ化する」を選ぶと、ほかのリージョンも使えるようになる。ただし、次の点があるため、この手順書では使わない。

- Paid プラン（クレジットを超えた分が請求されるプラン）への切り替えが前提になる
- 一度有効にすると元に戻せない
- 追加のクレジットを獲得できなくなる

参考: [AWS Regions for your projects](https://docs.aws.amazon.com/accounts/latest/reference/project-regions.html)、[Activate advanced AWS features](https://docs.aws.amazon.com/accounts/latest/reference/activate-advanced-features.html)

### Free プランについて

| 項目 | 内容 |
|---|---|
| クレジット（AWS の利用料に充てられるお金） | 登録時に 100 USD。所定の課題を行うと最大 100 USD 追加 |
| 請求 | 発生しない |
| 使えるサービス | 一部のサービスに限られる（Lambda、API Gateway、CloudFormation、S3、CloudWatch Logs は使える） |
| 期限 | 6 か月、またはクレジットを使い切るまで |

Free プランが終わると、プロジェクトは停止し、作ったリソースにアクセスできなくなる。90 日以内に Paid プランに切り替えると、引き続き使える。

参考: [Supported AWS services for Sign up for AWS (new)](https://docs.aws.amazon.com/accounts/latest/reference/supported-services-sign-up-new.html)

## 3. MFA（Multi-Factor Authentication、多要素認証）の設定

パスワードが漏れても他人がログインできないように、MFA を設定する。新しい登録方式にはルートユーザーがなく、MFA は AWS Builder ID に設定する。

### Google、GitHub、Apple、Amazon のアカウントで登録した場合

AWS へのログインは、そのアカウントを通して行われる。そのアカウント側の 2 段階認証が有効になっていれば、AWS へのログインも守られる。

- Google: [2 段階認証プロセスを有効にする](https://support.google.com/accounts/answer/185839)
- GitHub: [2 要素認証の設定](https://docs.github.com/ja/authentication/securing-your-account-with-two-factor-authentication-2fa/configuring-two-factor-authentication)
- Apple: 多くの場合、すでに有効になっている

### メールアドレスで登録した場合

1. <https://settings.aws.com> を開く（コンソールのホームの「プロジェクト管理」からも開ける）。
2. 左のメニューの「Manage security and sign-in」を選ぶ。AWS Builder ID のプロフィールに移る。
3. 「Security」ページの「Register device」を選ぶ。
4. 種類を選ぶ。
   - **Security key**: Mac の Touch ID、パスキー、USB のセキュリティキーなど
   - **Authenticator app**: Google Authenticator、1Password などのアプリ。表示される QR コードを読み取り、アプリに出る 6 桁のコードを入力して「Assign MFA」を選ぶ
5. 必要に応じて「Rename」で分かりやすい名前を付ける。

登録したすべての MFA デバイスを失うと、アカウントを復旧できない。AWS は 2 つ以上の登録を勧めている（例: Touch ID と認証アプリ）。

参考: [Manage multi-factor authentication (MFA) in AWS Settings](https://docs.aws.amazon.com/accounts/latest/reference/register-mfa-devices.html)

## 4. 費用の確認

Free プランでは請求が発生しない。使った分はクレジットから差し引かれる。

コンソールのホームの「コストと使用状況」に、次の情報が表示される。

- **残りのクレジット**（例: $100.00 USD）
- **残り日数**（Free プランの期限）
- 当月の費用と、月末の予測

AWS 設定（<https://settings.aws.com>）の「プロジェクト」の画面の「概要」にも、「無料プランの残り日数」と「残りのクレジット」が表示される。

残りのクレジットは、使った分だけ減り、下の課題を完了すると増える。たとえば、最初の 100 USD に課題 1 つ分の 20 USD が加わると、120 USD と表示される。費用が画面に反映されるまで、1 日ほどかかることがある。

このサンプルを動作確認の範囲で使う程度であれば、費用は無料枠の範囲に収まる（README の「費用の目安」を参照）。

### （任意）AWS Budgets でクレジットを増やす

コンソールのホームの「AWS を詳しく知る」に、完了するとクレジットがもらえる課題が並んでいる。そのうち「AWS Budgets を使用してコスト予算をセットアップする」は、予算を作る課題で、完了すると 20 USD のクレジットがもらえる。

1. 「AWS Budgets を使用してコスト予算をセットアップする」のリンクを開く。
2. 画面の案内に沿って、月次のコスト予算を作る（予算額は 1 USD、通知先は自分のメールアドレスなど）。

予算の作成とメール通知は無料。

## 5. CLI のインストールとログイン

### インストール

ターミナルで次を実行する。

```bash
brew install awscli
brew install aws-sam-cli
```

インストールされたことを確かめる。

```bash
aws --version   # aws-cli/2.32.0 以上であること
sam --version
```

`aws login` は AWS CLI 2.32.0 以上で使える。古い版が入っている場合は `brew upgrade awscli` で更新する。

SAM CLI について、AWS 公式の macOS 向けインストール方法は `.pkg` インストーラー（[Install the AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)）。Homebrew 版はコミュニティが管理していて、AWS 公式のドキュメントにも Homebrew を使う方法として記載がある。この手順書は Homebrew 版を使う。

### ログイン

```bash
aws login
```

1. 初回はリージョンを聞かれる。2 章で確かめたプロジェクトのリージョン（この手順書の例では `ap-southeast-2`）を入力する。東京 `ap-northeast-1` を入力すると、プロジェクトのリージョンと合わないため、以降の操作が拒否される。

   ```
   AWS Region [us-east-1]: ap-southeast-2
   ```

2. ブラウザが開き、「Choose AWS sessions」の画面が表示される。自分のプロジェクトを選ぶ（コンソールにログインしていない場合は、先にログインを求められる）。
3. ターミナルに戻ると、ログインが完了している。成功すると、次の行が表示される。

   ```
   Updated profile default to use arn:aws:sts::123456789012:assumed-role/AccountFullAccessRole/... credentials.
   ```

4. 続けて、AI コーディングエージェント向けの設定を入れるかを聞かれる。

   ```
   Configure AWS skills and the AWS MCP server for your AI coding agent(s)? [y/n/never]:
   ```

   これは、Claude Code などの AI エージェントの設定ファイルに、AWS を操作するための機能（AWS MCP サーバーとスキル）を追加するかの確認。

   | 回答 | 結果 |
   |---|---|
   | `y` | AI エージェントの設定ファイルに、AWS 用の機能が追加される |
   | `n` | 追加しない。次に `aws login` したときに、また聞かれる |
   | `never` | 追加しない。今後は聞かれない |

   この手順書は AI エージェントを使わずに進めるため、`n` または `never` と答える。後から追加する場合は、コンソールのホームにある「エージェントプロンプトをコピー」から設定できる。

この操作で `~/.aws/config` の `[default]` に、ログインの情報とリージョンが書き込まれる。一時的な認証情報は `~/.aws/login/cache/` に保存され、自動で更新される。

- 1 回のログインで使えるのは 12 時間。切れたら `aws login` をもう一度実行する
- ブラウザでの許可は最長 90 日有効。90 日を過ぎると、ブラウザでの許可が再び求められる
- 作業を終えるときに `aws logout` を実行すると、保存された認証情報が消える

### 確認

```bash
aws sts get-caller-identity
```

次のように、アカウント ID とログイン中の権限（ロール）が表示されればログインできている。

```json
{
    "UserId": "AROA...:...",
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/AccountFullAccessRole/..."
}
```

`AccountFullAccessRole` は、新しい登録方式で AWS が用意する、プロジェクトの管理者の権限。

参考: [Connect an AI coding tool（`aws login` の説明を含む）](https://docs.aws.amazon.com/accounts/latest/reference/connect-ai-coding-tool.html)、[Login for AWS local development using console credentials](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html)

## 6. ローカルでのテスト

AWS に接続せずに、Lambda のハンドラ（`src/app.py`）が正しく動くかを pytest で確かめる。

```bash
cd aws-lambda-minimal
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

`python3.14` とバージョンまで書いているのは、Lambda のランタイム（`template.yaml` の `python3.14`）と同じバージョンでテストするため。バージョンを付けない `python3` は、PC によって別のバージョンを指す。たとえば、Homebrew の標準の Python が 3.15 に変わった後の Mac では、Apple が入れた Python 3.9（`/usr/bin/python3`）を指す。

次のように表示されれば成功。

```
....                                                                     [100%]
4 passed in 0.01s
```

テストは `tests/test_app.py` にある。API Gateway から Lambda に渡されるイベント（辞書）を自分で作り、ハンドラに渡して、返ってきたステータスコードと本文を確かめている。

## 7. デプロイ

### ビルド

```bash
sam build
```

`template.yaml` を読み、`src/` のコードを `.aws-sam/build/` にまとめる。`Build Succeeded` と表示されれば成功。

`sam deploy` がデプロイするのは、`.aws-sam/build/` の中身。コードや `template.yaml` を変えた後は、デプロイの前に毎回 `sam build` を実行する。実行しないと、前回ビルドした内容がデプロイされる。

`sam build` は、`template.yaml` のランタイム（`python3.14`）と同じバージョンの Python が PC にあることを確かめる。`python3.14 --version` で `Python 3.14.x` と表示されない場合は、`brew install python@3.14` で入れる。

### デプロイ：A と B のどちらか 1 つを行う

デプロイの方法は、このフォルダに `samconfig.toml` があるかどうかで決まる。次の **A と B のどちらか 1 つ** を行う。

| `samconfig.toml` | 行う手順 | コマンド |
|---|---|---|
| ない（初めてデプロイする） | [A. 初回のデプロイ](#a-初回のデプロイsamconfigtoml-がない場合) | `sam deploy --guided` |
| ある（前に A を行った） | [B. 2 回目以降のデプロイ](#b-2-回目以降のデプロイsamconfigtoml-がある場合) | `sam deploy` |

`samconfig.toml` があるかどうかは、次のコマンドで確かめられる。ファイル名が表示されればファイルがあり、`No such file or directory` と表示されればファイルはない。

```bash
ls samconfig.toml
```

### A. 初回のデプロイ（`samconfig.toml` がない場合）

```bash
sam deploy --guided
```

`--guided` は「案内付き」という意味のオプション。付けると、SAM がデプロイの設定を質問の形で 1 つずつ聞く。次の質問が出るのは、`--guided` を付けたため（詳しくは、この節の最後の「`--guided` と `samconfig.toml`」にある）。

| 質問 | 意味 | 回答 |
|---|---|---|
| `Stack Name [sam-app]` | CloudFormation のスタック名。作ったリソースはこの名前でまとめて管理される | `aws-lambda-minimal` |
| `AWS Region [ap-southeast-2]` | デプロイ先のリージョン | プロジェクトのリージョン（`aws login` で設定したものが表示されるので、そのまま Enter） |
| `Confirm changes before deploy [Y/n]` | 作る・変えるリソースの一覧を表示し、確認してからデプロイするか。`Y` にすると、デプロイの直前に `Deploy this changeset? [y/N]` と聞かれる（下の「デプロイの流れ」の手順 3） | `Y` |
| `Allow SAM CLI IAM role creation [Y/n]` | Lambda が動くための IAM ロール（Lambda 用の権限）を SAM が作ってよいか | `Y` |
| `Disable rollback [y/N]` | 失敗したとき、途中まで作ったものを残すか。`N` なら失敗前の状態に戻す | `N` |
| `HelloFunction has no authentication. Is this okay? [y/N]` | 下で説明 | `y` |
| `Save arguments to configuration file [Y/n]` | ここまでの回答を `samconfig.toml` に保存するか | `Y` |
| `SAM configuration file [samconfig.toml]` | 保存先のファイル名 | そのまま Enter |
| `SAM configuration environment [default]` | 設定のまとまりの名前 | そのまま Enter |

SAM CLI の版によって、質問の文言が少し異なることがある。

#### `--guided` と `samconfig.toml`

`Save arguments to configuration file` に `Y` と答えると、回答がこのフォルダの `samconfig.toml` に保存される。中身は次のようになる（`#` 以降は説明として付けたもので、実際のファイルにはない）。

```toml
[default.deploy.parameters]
stack_name = "aws-lambda-minimal"     # スタック名
region = "ap-southeast-2"             # リージョン
confirm_changeset = true              # デプロイ前に変更点の一覧を表示して確認する
capabilities = "CAPABILITY_IAM"       # IAM ロールを作ってよい
resolve_s3 = true                     # SAM 用の S3 バケットを自動で使う
s3_prefix = "aws-lambda-minimal"      # バケットの中でファイルを置くフォルダの名前
```

`sam deploy` は、`samconfig.toml` があると中身を読み込んで使う。このため、2 回目以降は `--guided` を付けずに `sam deploy` だけで、同じ設定でデプロイできる。スタックを `sam delete` で削除した後にもう一度デプロイする場合も同じ。

`--guided` をもう一度付けるのは、次の場合。

- スタック名やリージョンなど、設定を変えたいとき
- `samconfig.toml` がないとき（削除した場合や、別の PC でリポジトリを取得した場合など）

`--guided` を付けて実行した場合は、保存済みの回答が `[ ]` の中に表示される。Enter を押していくと、同じ設定のままになる。

#### 「認証がない」という確認について

`HelloFunction has no authentication. Is this okay?`（または `may not have authorization defined`）は、「この API は、URL を知っている人なら誰でも呼び出せるが、よいか」という確認。

このサンプルの API は挨拶の文字列を返すだけで、秘密の情報や書き込みの処理を持たないため、`y` と答える。`N` と答えるとデプロイは中止される。

認証のない API は、URL が知られると誰でも何度でも呼び出せる。呼び出された回数だけクレジットが減る可能性があるため、動作を確かめたら 10 章の手順で削除しておくと安心。

#### デプロイの流れ

質問に答えると、次の順に進む。

1. SAM 用の S3 バケット（ファイル置き場）がなければ作る。`aws-sam-cli-managed-default` という名前のスタックとして作られる。
2. `src/` を zip にまとめて S3 にアップロードする。
3. 作るリソースの一覧（変更セット）を表示し、`Deploy this changeset? [y/N]` と聞く。一覧を確かめて `y` と答える（一覧の読み方は下にある）。
4. CloudFormation がリソースを作る。進み具合が表示される。
5. 完了すると `Outputs` に API の URL が表示される。

手順 3 では、次のような一覧が表示される（スタックがない状態でデプロイした例）。

```
CloudFormation stack changeset
---------------------------------------------------------------------------------------------------
Operation       LogicalResourceId                          ResourceType               Replacement
---------------------------------------------------------------------------------------------------
+ Add           HelloFunctionHelloApiPermission            AWS::Lambda::Permission    N/A
+ Add           HelloFunctionLogGroup                      AWS::Logs::LogGroup        N/A
+ Add           HelloFunctionRole                          AWS::IAM::Role             N/A
+ Add           HelloFunction                              AWS::Lambda::Function      N/A
+ Add           ServerlessHttpApiApiGatewayDefaultStage    AWS::ApiGatewayV2::Stage   N/A
+ Add           ServerlessHttpApi                          AWS::ApiGatewayV2::Api     N/A
---------------------------------------------------------------------------------------------------
Deploy this changeset? [y/N]:
```

列の意味は次のとおり。

| 列 | 意味 |
|---|---|
| Operation | そのリソースに対して行う操作。`+ Add` は新しく作る、`* Modify` は変更する、`- Remove` は削除する |
| LogicalResourceId | `template.yaml` の中での呼び名 |
| ResourceType | リソースの種類 |
| Replacement | `* Modify` のとき、作り直しになるか（`True`）、そのまま変更できるか（`False`）。`+ Add` では `N/A` |

各行のリソースは次のとおり。`template.yaml` に書いているのは `HelloFunction` と `HelloFunctionLogGroup` の 2 つで、残りの 4 つは SAM が自動で追加する。

| LogicalResourceId | 種類 | 役割 | `template.yaml` に書いているか |
|---|---|---|---|
| `HelloFunction` | Lambda の関数 | `src/app.py` を実行する | 書いている |
| `HelloFunctionLogGroup` | CloudWatch Logs のロググループ | Lambda のログを 7 日間保存する | 書いている |
| `HelloFunctionRole` | IAM ロール | Lambda がログを書き込むための権限 | SAM が追加 |
| `ServerlessHttpApi` | API Gateway の HTTP API | インターネットからのリクエストを受け付ける | SAM が追加（`Events` の `HttpApi` から） |
| `ServerlessHttpApiApiGatewayDefaultStage` | API Gateway のステージ | API を公開して呼び出せる状態にするための設定 | SAM が追加 |
| `HelloFunctionHelloApiPermission` | Lambda の呼び出し許可 | API Gateway が Lambda を呼び出してよいという許可 | SAM が追加 |

一覧で確かめる点は、意図しない `- Remove`（削除）や、`Replacement` が `True`（作り直し）の行がないか。問題がなければ `y`、やめる場合は `n` と答える。`n` と答えると、AWS には何も変更されない。

```
Key                 HelloApiUrl
Description         URL of GET /hello
Value               https://abcd1234.execute-api.ap-southeast-2.amazonaws.com/hello
```

### B. 2 回目以降のデプロイ（`samconfig.toml` がある場合）

A を行ったときの回答が `samconfig.toml` に保存されているため、`--guided` を付けない。質問が出ないこと以外は、A の「デプロイの流れ」と同じ順に進む。

```bash
sam deploy
```

- 質問は出ず、`samconfig.toml` のスタック名やリージョンが使われる。
- 変更点の一覧（変更セット）が表示され、`Deploy this changeset? [y/N]` と聞かれる。一覧を確かめて `y` と答える。一覧の読み方は、A の「デプロイの流れ」にある。

スタックの有無によって、結果が次のように変わる。

| 状況 | 変更点の一覧の表示 | 完了後のスタックの状態 |
|---|---|---|
| スタックがある（前回のデプロイが残っている） | 変える部分が `* Modify` になる | `UPDATE_COMPLETE` |
| スタックがない（10 章の `sam delete` の後など） | すべての行が `+ Add` になる | `CREATE_COMPLETE` |
| 前回から何も変わっていない | 一覧は出ず、`No changes to deploy` と表示されて終わる | 変わらない |

`sam delete` の後にもう一度デプロイした場合は、API の URL が前回と変わる。API が作り直されて、新しい ID が付くため。

コードを変更して再デプロイする例は、9 章にある。

## 8. 動作確認

### curl で呼び出す

デプロイの `Outputs` に表示された `HelloApiUrl` を使う。7 章の出力例にある `https://abcd1234...` は例の URL で、実際には存在しない。そのまま使うと `Could not resolve host` というエラーになる。

次のコマンドは、デプロイで作られた URL を AWS から取り出して `URL` という変数に入れ、それを使って呼び出す。

`# 出力の例:` の行は、直前のコマンドの出力の例。

```bash
URL=$(aws cloudformation describe-stacks --stack-name aws-lambda-minimal --query "Stacks[0].Outputs[?OutputKey=='HelloApiUrl'].OutputValue" --output text)
echo "$URL"
# 出力の例: https://<API ごとに異なる ID>.execute-api.ap-southeast-2.amazonaws.com/hello
```

```bash
curl "$URL?name=test"
# 出力の例: {"message": "Hello, test!"}
```

```bash
curl "$URL"
# 出力の例: {"message": "Hello, World!"}
```

zsh は、ターミナルに直接入力した行では、標準の設定で `#` をコメントとして扱わない。`# 出力の例:` の行まで貼り付けると、その行もコマンドとして読まれ、例の中の `"` や `<` が別の意味に解釈される。その結果、`dquote>` と表示されて入力待ちになることがある。`dquote>` は Ctrl+C で抜けられる。

先に次のコマンドを実行しておくと、そのターミナルでは `#` の行がコメントとして扱われ、ブロックをまとめて貼り付けても動く。`~/.zshrc` に書くと、新しく開くターミナルでも同じになる。

```bash
setopt interactivecomments
```

ブラウザで URL を開いても同じ結果が表示される。

#### コマンドの意味

- **`curl`**: URL に HTTP のリクエストを送り、返ってきた返事をターミナルに表示するコマンド。ブラウザで URL を開くのと同じことを、文字だけで行う。
- **`$URL`**: 直前の `URL=$(...)` で値を入れた変数。シェルが `$URL` を中身に置き換えてから curl を実行する。そのため、`curl "$URL?name=test"` は `curl "https://<ID>.execute-api.ap-southeast-2.amazonaws.com/hello?name=test"` と同じになる。
- **`?name=test`**: クエリ文字列。URL の `?` より後ろに `名前=値` の形で書き、サーバーに値を渡す。ここでは `lambda_handler` に `name` を渡している。
- **`"`（ダブルクォート）**: zsh では `?` がファイル名の検索に使われる特別な文字で、囲まないと `no matches found` というエラーになることがある。`"` で囲むと、URL がそのまま curl に渡る。

| コマンド | 送る内容 | 返事 |
|---|---|---|
| `curl "$URL?name=test"` | `GET /hello` と `name=test` | `{"message": "Hello, test!"}` |
| `curl "$URL"` | `GET /hello` だけ | `{"message": "Hello, World!"}` |

2 つ実行しているのは、名前を渡した場合と、渡さなかった場合（`World` になる）の両方を確かめるため。

`Hello, test!` という文字列が `src/app.py` のどこで作られるかは、[仕組みの説明](how-it-works.md)の 3 章「返事の文字列ができるまで」にある。

### AWS コンソールで見る

上の検索欄にサービス名を入力して開く。

- **CloudFormation**: 「スタック」に `aws-lambda-minimal` がある。「リソース」タブに、SAM が作ったリソース（Lambda 関数、IAM ロール、HTTP API、ロググループなど）が並ぶ。「出力」タブに API の URL がある。
- **Lambda**: 「関数」に `aws-lambda-minimal-HelloFunction-...` がある。「コード」タブで `app.py` の中身を、「設定」タブでメモリ（128 MB）やタイムアウト（10 秒）を見られる。
- **CloudWatch Logs**: 次の「ログを見る」にある。

### ログを見る（CloudWatch Logs）

Lambda の上で `print` した内容は、curl の返事には入らない。curl が受け取るのは、`lambda_handler` の戻り値の `"body"` だけ。`print` の出力は、Lambda が CloudWatch Logs に書く。

`src/app.py` の `lambda_handler` の中（`name = ...` の行の後）には、`name` の値をログに出す次の行が入っている。curl で呼ぶたびに、この行が実行される。

```python
print(f"name:{{ {name} }}  @lambda_handler in app.py")
```

f 文字列の中の `{{` と `}}` は、`{` と `}` そのものを表す。`?name=test` で呼ぶと、`name:{ test }  @lambda_handler in app.py` が出力される。

#### コンソールで見る手順

1. 上の検索欄に「CloudWatch」と入力して開く。
2. 左のメニューの「ログ」の下にある「ログ管理」を押す。
3. 「ロググループ」タブの表に、`/aws/lambda/aws-lambda-minimal-HelloFunction-...` の行がある。`/aws/lambda/` で始まるのは Lambda 関数のログの置き場所で、後ろは関数の名前。名前（青い文字）を押す。「保持」の列の「1 週間」は、`template.yaml` で決めた保存期間（7 日）。
4. 下の「ログストリーム」の表で、一番上の行の名前（青い文字）を押す。ログストリームはログを入れる箱で、Lambda が起動するたびに 1 つ作られる。名前は `2026/10/19/[$LATEST]...` のように日付で始まり、表は「最終イベント時刻」が新しい順に並ぶ。時刻は UTC で、日本時間は 9 時間を足した時刻。
5. 「ログイベント」の画面に、ログの行が時刻の順に並ぶ。

curl を実行してから、ログに出るまで数秒かかることがある。

ターミナルでは、次のコマンドで同じログを見られる。

```bash
sam logs --stack-name aws-lambda-minimal -n HelloFunction --start-time '5min ago'
```

#### ログの読み方

curl で `?name=test` を付けて 2 回、付けずに 2 回呼んだときのログの例（`RequestId` などは省略）。

```text
INIT_START Runtime Version: python:3.14...
START RequestId: ...
name:{ test }  @lambda_handler in app.py
END RequestId: ...
REPORT RequestId: ... Duration: 1.95 ms Billed Duration: 82 ms Memory Size: 128 MB Max Memory Used: 38 MB Init Duration: 79.74 ms
START RequestId: ...
name:{ test }  @lambda_handler in app.py
END RequestId: ...
REPORT RequestId: ... Duration: 1.53 ms Billed Duration: 2 ms Memory Size: 128 MB Max Memory Used: 38 MB
START RequestId: ...
name:{ World }  @lambda_handler in app.py
END RequestId: ...
REPORT RequestId: ...
START RequestId: ...
name:{ World }  @lambda_handler in app.py
END RequestId: ...
REPORT RequestId: ...
```

1 回の呼び出しで、次の 4 行が出る。

| 行 | 意味 |
|---|---|
| `START` | `lambda_handler` の実行が始まった |
| `name:{ ... }` | `print` の出力。`?name=` を付けない場合は `World` になる |
| `END` | `lambda_handler` の実行が終わった |
| `REPORT` | 実行時間（`Duration`）、料金の計算に使う時間（`Billed Duration`）、使ったメモリ（`Max Memory Used`） |

一番上の `INIT_START` は、Lambda が起動したとき（コールドスタート）に 1 回だけ出る行。最初の `REPORT` にだけ、起動にかかった時間 `Init Duration` が付く。2 回目以降は起動済みの Lambda が使い回されるため、`INIT_START` の行は出ない。しばらく呼ばれずに Lambda が片付けられると、次の呼び出しで新しいログストリームが作られ、`INIT_START` から始まる。起動と呼び出しの違いは、[仕組みの説明](how-it-works.md)の 3 章「起動したときと、注文が来たとき」にある。

## 9. コードを変更して再デプロイする

例として、`src/app.py` の挨拶を変える。

```python
"body": json.dumps({"message": f"Hi, {name}!"}, ensure_ascii=False),
```

テストも期待値に合わせて変え（`Hello` → `Hi`）、テストを実行してから、ビルドとデプロイを行う。

```bash
pytest
sam build
sam deploy
```

2 回目以降は `--guided` を付けない。初回の回答は `samconfig.toml` に保存されていて、`sam deploy` はそれを使う。変更点の一覧が表示されたら `y` と答える。同じ URL を curl で呼ぶと、新しい挨拶が返る。

### ビルドとデプロイが必要な場合

`src/app.py` を変えても、AWS 上の Lambda 関数のコードは変わらない。AWS に反映するには、`sam build` と `sam deploy` の両方が必要。

| コマンド | 必要な理由 |
|---|---|
| `sam build` | `sam deploy` がアップロードするのは `src/app.py` ではなく、`sam build` が `.aws-sam/build/` に作ったコピー。`sam build` を実行しないと、コピーは古いコードのまま |
| `sam deploy` | 新しいコピーを AWS にアップロードし、Lambda 関数のコードを置き換える。URL は変わらない |

次の場合は、ビルドとデプロイがなくても困らない。

| 場合 | 理由 |
|---|---|
| `pytest` で Mac の中でテストする | テストは `src/app.py` を直接呼び出す |
| コメントだけを変えた | AWS 上の動きは変わらない。AWS 上のコピーのコメントが古いまま残るだけ |

## 10. 後片付け

### スタックを削除する

```bash
sam delete
```

質問が 2 つ出る。どちらも `y` と答える。

```text
Are you sure you want to delete the stack aws-lambda-minimal in the region ap-southeast-2 ? [y/N]: y
Are you sure you want to delete the folder aws-lambda-minimal in S3 which contains the artifacts? [y/N]: y
```

| 質問 | 意味 |
|---|---|
| 1 つ目 | スタック `aws-lambda-minimal` を削除するか |
| 2 つ目 | SAM 用の S3 バケットの中にある、フォルダ `aws-lambda-minimal` を削除するか |

2 つ目の質問のフォルダについて：

- **中身（artifacts）**：`sam deploy` のたびにアップロードされた、コードの zip とテンプレート。
- **名前**：`samconfig.toml` の `s3_prefix = "aws-lambda-minimal"` で決まっている。
- **`y` と答えてよい理由**：スタックを削除すると、中のファイルは使われなくなる。次に `sam deploy` を実行すると、必要なファイルはもう一度アップロードされる。
- **`n` と答えた場合**：ファイルが残る。数 KB なので無料枠に収まるが、残しておく理由はない。

どちらの答えでも、バケットそのものと `aws-sam-cli-managed-default` スタックは残る（下の「SAM 用の S3 バケットについて」）。

CloudFormation がスタックのリソース（Lambda 関数、IAM ロール、HTTP API、ロググループ）をまとめて削除する。

### 消えたことを確かめる

コンソールで次を確かめる。

- CloudFormation の「スタック」に `aws-lambda-minimal` がない（「削除済み」のフィルタに `DELETE_COMPLETE` として表示される）
- Lambda の「関数」に `aws-lambda-minimal-HelloFunction-...` がない
- API Gateway の API 一覧に `aws-lambda-minimal` がない
- CloudWatch Logs の「ロググループ」に `/aws/lambda/aws-lambda-minimal-HelloFunction-...` がない

curl で URL を呼ぶと、接続できないエラーになる。

### SAM 用の S3 バケットについて

`sam delete` は、7 章で自動で作られた `aws-sam-cli-managed-default` スタックとその S3 バケットを削除しない。このバケットを、同じリージョンにあるほかの SAM アプリもデプロイのときに使うため。

#### バケットとは

バケット（bucket）は、S3 で、ファイルを入れる一番外側の入れ物を指す。

| 用語 | 意味 | パソコンでたとえると |
|---|---|---|
| バケット（bucket） | ファイルを入れる、一番外側の入れ物 | ドライブ（外付けの HDD など 1 台） |
| フォルダ（プレフィックス） | バケットの中の区切り | フォルダ |
| オブジェクト | 中に入っている 1 つ 1 つのファイル | ファイル |

- バケットの名前は、世界中のすべての AWS の利用者の間で重なってはいけない。SAM のバケットの名前が `aws-sam-cli-managed-default-samclisourcebucket-` の後ろにランダムな文字列が付いた長い名前なのは、このため。
- バケットごとに、どのリージョンに置くか、誰が読めるかなどを設定する。
- S3 の「フォルダ」は、正式には「プレフィックス」と呼ぶ。ファイル名の頭に付いた `aws-lambda-minimal/` を、画面上でフォルダのように見せているもの。`samconfig.toml` の `s3_prefix` の prefix は、このことを指す。

#### バケットが残る理由

SAM 用の S3 バケットは、SAM アプリごとではなく、1 つのリージョンに 1 つだけ作られる。そのリージョンでデプロイする SAM アプリは、すべて同じバケットに、アプリごとにフォルダを分けてファイルを置く。たとえば、このサンプルのほかにアプリ B も同じリージョンにデプロイした場合は、次のようになる。

```text
S3 バケット（aws-sam-cli-managed-default のもの）
├─ aws-lambda-minimal/   ← このサンプルのファイル
└─ app-b/                ← アプリ B のファイル
```

このサンプルの `sam delete` で消してよいのは、このサンプルのものだけ。

| 消すもの | 消してよいか |
|---|---|
| スタック `aws-lambda-minimal` | よい（このサンプルだけのもの） |
| フォルダ `aws-lambda-minimal/`（2 つ目の質問） | よい（このサンプルだけのもの） |
| バケットそのもの | よくない。アプリ B のファイルも一緒に消える |

そのため、`sam delete` はバケットを消さない。バケットはスタック `aws-sam-cli-managed-default` の中のリソースなので、このスタックも消さない。ほかに SAM アプリがなければ、次の手順で消しても困ることはない。消さずに残した場合、次の `sam deploy` でそのまま使われる。消した場合は、次の `sam deploy` で SAM がもう一度作る。

#### 残した場合の費用

スタックとバケットは、あるだけでは費用がかからない。費用がかかるのは、バケットの中のファイル。

| もの | あるだけで費用がかかるか |
|---|---|
| スタック `aws-sam-cli-managed-default` | かからない（CloudFormation は、スタックを持っているだけでは料金がかからない） |
| S3 バケット（入れ物そのもの） | かからない |
| バケットの中のファイル | 保存している量に応じてかかる |
| バケットのアクセス設定（ポリシー） | かからない |

`sam delete` の 2 つ目の質問に `y` と答えると、このサンプルのファイルは消える。ただし、このバケットはバージョニングが有効なので、消したファイルの古いバージョンが残り、保存料金の対象になることがある。このサンプルの量では数 KB から数 MB で、料金はほぼゼロ。Free プランでは請求は発生せず、かかった分はクレジットから引かれる。

費用がかかるものを何も残さない場合は、次の手順でバケットとスタックを消す。

#### バケットを消す手順

完全に消す場合は次の順に行う。

1. S3 のコンソールで `aws-sam-cli-managed-default-samclisourcebucket-...` を選び、「空にする」を実行する（このバケットはバージョニングが有効なので、「空にする」で古いバージョンも含めて消える）。
2. CloudFormation のコンソールで `aws-sam-cli-managed-default` スタックを選び、「削除」を実行する。

スタックを削除すると、中の S3 バケットも削除される。ただし、バケットが空であることが条件。

| バケットの状態 | スタックを削除すると |
|---|---|
| 空（古いバージョンも含めて何もない） | バケットも一緒に消える |
| 中にファイルが残っている | バケットを消せず、スタックの削除が失敗する（`DELETE_FAILED`） |

AWS は、中身が入った S3 バケットの削除を受け付けない。CloudFormation もこの決まりに従うので、中身を消してからバケットを削除するようなことはしない。手順の 1 で先に「空にする」を実行するのは、このため。

SAM CLI 1.167.0 のソースで、このスタックのテンプレートを確かめた結果は次のとおり。

- バケットに、スタックを消しても残す設定（`DeletionPolicy: Retain`）は付いていない。そのため、空であればスタックと一緒に消える。
- バージョニングが有効（`VersioningConfiguration: Enabled`）になっている。そのため、画面で空に見えても、消したファイルの古いバージョンが残っていると空にならない。

S3 の画面で、バケットを「空にする」の後に「削除」まで行った場合も、その後に CloudFormation でスタックを削除すると、失敗せずに終わった（2026-10-20 に実機で確認）。CloudFormation は、すでにないバケットを消えたものとして扱う。ただし、バケットだけを消してスタックを残すと、次の `sam deploy` が、もうないバケットにファイルを置こうとして失敗する。バケットを S3 の画面で削除した場合も、スタックを削除するところまで行う。

「スタック (0)」になれば、SAM 用の置き場も含めて、このサンプルで AWS に作ったものはすべて消えている。次に `sam deploy --guided` を実行すると、SAM 用のバケットとスタックは自動で作り直される。

### プロジェクトとアカウント

プロジェクトを閉じる場合や、AWS の利用をやめる場合は、AWS Settings（<https://settings.aws.com>）から手続きする。

参考: [Close a project in AWS Settings](https://docs.aws.amazon.com/accounts/latest/reference/close-project.html)、[Close your account in AWS Settings](https://docs.aws.amazon.com/accounts/latest/reference/close-account-new-experience.html)

## 11. よくあるエラーと対処

### 「リージョン ... は利用できません」と表示される

```
リージョン アジアパシフィック (東京) は利用できません
Your project is assigned to アジアパシフィック (シドニー) ap-southeast-2.
```

プロジェクトのリージョン以外を開いている。「Return to（プロジェクトのリージョン）」を選ぶと元に戻る。同じ画面の「高度な機能をアクティブ化する」の注意点は 2 章にある。

### `service control policy explicitly denies the action`

```
User: arn:aws:sts::123456789012:assumed-role/AccountFullAccessRole/... is not authorized to perform: ...
because no identity-based policy allows the action / a service control policy explicitly denies the action
```

新しい登録方式では、AWS が管理する制限（サービスコントロールポリシー、SCP）がかかっている。主な原因は次の 2 つ。

- **プロジェクトのリージョン以外を操作している**: CLI のリージョンを `aws configure get region` で確かめる。違っていれば `aws configure set region ap-southeast-2`（プロジェクトのリージョン）で直す。`sam deploy` のリージョンは `samconfig.toml` の `region` に保存されている。
- **Free プランで使えないサービスを使おうとしている**: 使えるサービスは [Supported AWS services for Sign up for AWS (new)](https://docs.aws.amazon.com/accounts/latest/reference/supported-services-sign-up-new.html) に一覧がある。このサンプルが使うサービスは、すべて Free プランで使える。

### ログインの期限切れ

```
Unable to locate credentials
```

または `The security token included in the request is expired`、`login session has expired` などと表示される。

`aws login` の有効期間（12 時間）が過ぎている。`aws login` をもう一度実行する。`aws sts get-caller-identity` でログインできているかを確かめられる。

### SAM CLI が `aws login` の認証情報を読めない

`aws sts get-caller-identity` は成功するのに、`sam deploy` だけが `Unable to locate credentials` になる場合、SAM CLI に含まれる AWS SDK が `aws login` の認証情報に対応していない可能性がある。`brew upgrade aws-sam-cli` で最新版にすると直ることがある。

最新版でも直らない場合は、AWS CLI に認証情報を渡してもらう設定を `~/.aws/config` に追加する（AWS 公式ドキュメントに記載されている方法）。

```ini
[profile sam]
credential_process = aws configure export-credentials --profile default --format process
region = ap-southeast-2
```

SAM のコマンドに `--profile sam` を付けて実行する。

```bash
sam deploy --guided --profile sam
```

`--guided` のときに指定したプロファイルは `samconfig.toml` に保存され、以降の `sam deploy` でも使われる。

### コンソールでリソースが見つからない

コンソールの URL のリージョン（2 章）が、デプロイしたリージョンと同じかを確かめる。

### `sam build` で Python が見つからない

```
Binary validation failed for python, searched for python in following locations: ...
which did not satisfy constraints for runtime: python3.14
```

PC に Python 3.14 がない。`brew install python@3.14` で入れる。

### スタックが `ROLLBACK_COMPLETE` になった

初回のデプロイが途中で失敗すると、スタックが `ROLLBACK_COMPLETE` の状態で残り、同じ名前で再デプロイできなくなる。`sam delete` でスタックを消してから、原因（CloudFormation の「イベント」タブに表示される）を直して、もう一度 `sam deploy` を実行する。
