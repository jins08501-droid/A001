#!/usr/bin/env python3
"""
経営資料作成パイプライン（シングルエージェント版）
1つのエージェントが全ステップを一気に実行する。

使い方:
  python document_pipeline.py
  python document_pipeline.py "テーマ名"
"""

import asyncio
import sys
from datetime import datetime

from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage, AssistantMessage, TextBlock

DEFAULT_THEME = "2032年システムリプレースのポートフォリオ、製品ロードマップ作成"

DEFAULT_BACKGROUND = """
- 2032年に基幹システムを一括リプレース予定
- IT部門が全体方針確定前に一部システムの先行開発を進めようとしている
- 製品・事業側のロードマップはまだ未策定
- 経営企画部門がIT投資ポートフォリオ策定プロセスを主導する
- システム基盤の先行検討は認めるが、アプリ・機能開発はロードマップ策定まで原則保留
- 事業ロードマップ策定も経営企画が主導する
- 従業員数300人規模の企業
- 経営会議・取締役会への承認が必要
""".strip()

SYSTEM_PROMPT = """
あなたは経営コンサルタント兼資料作成の専門家です。
ユーザーから与えられたテーマと背景情報をもとに、以下の8つのステップを順番に実行し、
各ステップの結果を出力してください。

【ステップ一覧】
Step 1: イシュー整理
  - 核心イシュー、解決すべき論点（MECE）、前提条件、ステークホルダー、成功の定義

Step 2: ベストプラクティス整理
  - IT投資管理・大規模リプレースのグローバルベストプラクティス
  - 代表的フレームワーク（Gartner・COBIT・ITIL等）、成功・失敗事例の教訓

Step 3: 300人規模での実現方法
  - リソース制約を踏まえた現実的アプローチ、段階的実施計画、外部活用方法

Step 4: 論点ツリー・ストーリー作成
  - 論点ツリー（MECE）、ストーリーライン、「空・雨・傘」構成案

Step 5: 経営会議向け資料（初稿）
  - Markdown形式。エグゼクティブサマリー、背景、方針、プロセス、投資概算、
    優先順位基準、ガバナンス、リスク、アクションを含む

Step 6: 各視点からの反論
  以下9つの視点から、資料の問題点を具体的に指摘してください：
  - IT部門長：技術的実現可能性・スケジュール・リソース
  - CFO：投資対効果・コスト根拠・財務リスク
  - 事業部門長：業務継続・現場影響・顧客影響
  - CISO：セキュリティリスク・データ保護・移行リスク
  - CRO：プロジェクトリスク・BCP・ベンダーリスク
  - CEO：戦略整合・競合・株主説明責任
  - 社外取締役：ガバナンス・透明性・株主価値
  - 金融庁：規制対応・内部統制・監督指針
  - 一般利用者：業務影響・使い勝手・移行時の混乱

Step 7: 資料修正（最終版）
  - Step 6の反論を踏まえ、重要な指摘を選別して反映した改善版をMarkdownで出力

Step 8: 想定問答
  - 経営会議・取締役会で想定される質問と回答を最低15問作成
  - 形式：**Q（質問者）：** 質問 / **A：** 回答

各ステップは「## Step N: タイトル」の見出しで始めてください。
日本語で、経営層が納得できる内容・品質で作成してください。
""".strip()


async def run_pipeline(theme: str, background: str) -> str:
    print(f"\n{'─' * 60}")
    print("▶ パイプライン実行中...")
    print(f"{'─' * 60}\n")

    prompt = f"テーマ: {theme}\n\n背景情報:\n{background}\n\n上記のテーマと背景について、Step 1からStep 8まで順番に実行してください。"

    result = ""
    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            system_prompt=SYSTEM_PROMPT,
            allowed_tools=[],
            max_turns=3,
        ),
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text, end="", flush=True)
        elif isinstance(message, ResultMessage):
            result = message.result

    print()
    return result


def save_output(theme: str, content: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"pipeline_output_{ts}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {theme}\n")
        f.write(f"生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n\n---\n\n")
        f.write(content)
    return filename


async def main():
    theme = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_THEME

    print("=" * 60)
    print("経営資料作成パイプライン（シングルエージェント版）")
    print("=" * 60)
    print(f"\nテーマ: {theme}\n")

    result = await run_pipeline(theme, DEFAULT_BACKGROUND)
    filename = save_output(theme, result)

    print(f"\n{'=' * 60}")
    print(f"✅ 完了！  出力ファイル: {filename}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
