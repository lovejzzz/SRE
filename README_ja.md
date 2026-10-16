[English](README.md) · [简体中文](README_zh.md) · [日本語](README_ja.md) · [Español](README_es.md) · [Français](README_fr.md) · [Deutsch](README_de.md) · [Português (Brasil)](README_pt-BR.md)

# SRE — Software Resynthesis Engine

[![Tests](https://github.com/lovejzzz/SRE/actions/workflows/test.yml/badge.svg)](https://github.com/lovejzzz/SRE/actions/workflows/test.yml)

**再構築したいソフトウェア、移行先のプラットフォーム、改善したい点を伝えてください。**

SRE は、既存ソフトウェアを調査し、必要な動作を保ち、新しい環境に適応させ、機能を追加・改善するためのエージェント用 skill です。ゲーム、デスクトップ、CLI、Web、モバイルを対象とする構想ですが、実現可能性は証拠へのアクセス、依存関係、移行先の能力に左右されます。

**v0.2：skill と実行可能な調査・検証ツール。** 調査と実装はホストのエージェントが行います。あらゆるソフトウェアの完全なワンクリック再現を保証するものではありません。

## インストール

ローカル skill 対応のホストと **Python 3.10+** が必要です。Python の外部依存はありません。[REA](https://github.com/morluto/rea) は任意で、自動インストールされません。

```bash
git clone https://github.com/lovejzzz/SRE.git
python3 SRE/scripts/install.py
```

既定の配置先は `$CODEX_HOME/skills` または `~/.codex/skills`。既存の配置は上書きしません。`--skills-dir /path/to/skills` で変更できます。更新時はローカルの変更を保持し、ホストで skill を再読み込みしてください。

> $software-resynthesis を使い、このデスクトップアプリを調査してオフライン Web アプリとして再構築してください。文書操作を保ち、バッチ処理を追加し、元のアプリと比較検証してください。全体の要件を保持したまま、検証済みの最初のマイルストーンを届けてください。

## 実装済みの機能

- 複数の情報源に基づく機能一覧、対応付け、依存関係、未対応項目の監査、版管理された基準。
- 対立する仮説、予測、仮説を識別する実験の優先順位、矛盾の検出。
- 明示的なコマンドによるアダプター実行、独立した実行ディレクトリ、リセット・操作・観察・終了の契約、ハッシュ、ログ、タイムアウト。
- 正規化画像の誤差、ファイル往復後の意味情報、操作履歴、機器と負荷を指定した性能予算の検証。
- 動作の証拠と調査監査の両方を求める受け入れ判定。古い記録や未解決の重要事項は通過できません。

REA は分析を支援できます。SRE は調査を仕様・実装・検証につなげます。REA クライアントは内蔵しておらず、REA より優れているという比較評価もありません。

## 実行例

```bash
cd SRE
python3 -m unittest discover -s tests -v
python3 examples/posix-path/run.py --workspace work/posix-run-1
```

Python の `posixpath.normpath` と独立した JavaScript 実装を実際に実行し、**417 入力**を比較します。観察によって調査課題を解決し、意図的な不具合も検出します。Node.js 18+ が必要で、出力先は未作成である必要があります。完全なアプリ再構築能力の独立評価ではありません。

## コマンドと制限

`sre.py`：`init`、`fingerprint`、`seal`、`audit`、`plan`、`run-adapter`、`compare`、`domain-check`、`check`。引数は各 `--help` を参照。出力は上書きしません。終了コードは成功 0、比較・受け入れ・実行の不合格 1、入力または実行エラー 2。v0.1 の作業領域には実際の調査記録と基準の追加が必要です。

未発見の機能がないことや証拠の真正性は証明できません。マイルストーン完了は製品全体の完成ではありません。汎用クローラー、常駐スケジューラー、PZ/Photoshop 用実行アダプターはありません。仮説と調査記録はエージェントが作成します。アダプターはホスト権限で動作し、サンドボックスではありません。検証入力は正規化 JSON で、PSD 解析、画像デコード、GUI 操作、機器測定には専用アダプターが必要です。アクセスできないサーバー実装を復元することも、任意の機器で任意の処理を実現することも保証しません。

独立したエージェント評価は未実施です。機密サンプル、認証情報、個人データは非公開の作業領域に保管し、コード再利用時は元のライセンスに従ってください。

[調査プロトコル](skills/software-resynthesis/references/research-protocol.md) · [アダプター](skills/software-resynthesis/references/adapters.md) · [領域別検証](skills/software-resynthesis/references/domain-validation.md) · [評価](evals/behavioral.md)

再現可能で機密情報を除去した不具合報告と翻訳改善を歓迎します。バージョン、入力、期待値・実測値、証拠を添えてください。詳細な技術文書は現在英語です。

証拠の整合性更新：対象環境の検証と調査観測には SHA-256 が必要です。[移行方法と検証の限界](skills/software-resynthesis/references/validation.md#recorded-evidence-integrity)と[変更履歴](CHANGELOG.md)を参照してください。

作業記録：`sre.py record` / `report` は操作、失敗、修正、証拠のハッシュを保存します。[記録仕様](skills/software-resynthesis/references/work-journal.md)と進行中の [Project Zomboid 事例](docs/project-zomboid/PROCESS.md)を参照してください（未完成、忠実性の証明ではありません）。
