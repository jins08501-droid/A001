#!/usr/bin/env python3
"""
経営資料作成マルチエージェントパイプライン（Agent SDK版）
APIキー不要 — Claude Code の認証をそのまま利用

【ステップ構成】
  1. イシュー整理
  2. ベストプラクティス調査（Web検索）
  3. 300人規模での実現方法
  4. 論点ツリー・ストーリー作成
  5. 文書作成（初稿）
  6. 9視点からの反論（並列実行）
  7. 反論を踏まえた資料修正
  8. 想定問答作成

【使い方】
  python document_pipeline.py
  python document_pipeline.py "テーマ名"
"""

import asyncio
import sys
from datetime import datetime

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    ResultMessage,
    AssistantMessage,
    TextBlock,
)


# ─────────────────────────────────────────────────────────────
# エージェント実行ヘルパー
# ─────────────────────────────────────────────────────────────

async def run_stream(system: str, user: str, label: str) -> str:
    """逐次処理用：テキストをリアルタイム表示"""
    print(f"\n{'─' * 60}")
    print(f"▶ {label}")
    print(f"{'─' * 60}")

    result = ""
    async for message in query(
        prompt=user,
        options=ClaudeAgentOptions(
            system_prompt=system,
            allowed_tools=[],
            max_turns=5,
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


async def run_with_search(system: str, user: str, label: str) -> str:
    """Web検索あり：WebSearch / WebFetch ツールを使用"""
    print(f"\n{'─' * 60}")
    print(f"▶ {label}")
    print(f"{'─' * 60}")

    result = ""
    async for message in query(
        prompt=user,
        options=ClaudeAgentOptions(
            system_prompt=system,
            allowed_tools=["WebSearch", "WebFetch"],
            max_turns=20,
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


async def run_silent(system: str, user: str, label: str) -> str:
    """並列処理用：サイレント実行（9ペルソナ同時起動）"""
    print(f"  ・{label} 生成中...", flush=True)

    result = ""
    async for message in query(
        prompt=user,
        options=ClaudeAgentOptions(
            system_prompt=system,
            allowed_tools=[],
            max_turns=5,
        ),
    ):
        if isinstance(message, ResultMessage):
            result = message.result

    print(f"  ✓ {label} 完了")
    return result


# ─────────────────────────────────────────────────────────────
# システムプロンプト
# ─────────────────────────────────────────────────────────────

PROMPT_ISSUE = """
あなたは経営コンサルタントです。与えられたテーマと背景情報を構造的に整理してください。

以下の観点で整理してください：
1. 核心イシュー（問題の本質は何か）
2. 解決すべき論点リスト（MECEに）
3. 前提条件と制約
4. 主要ステークホルダーとその関心
5. 成功の定義・KPI

日本語で、箇条書きを活用して簡潔に。
""".strip()

PROMPT_RESEARCH = """
あなたは経営・IT戦略の専門家です。
あなたの知識に基づき、与えられたテーマに関するベストプラクティスをまとめてください。

対象：
1. IT投資管理・ITポートフォリオ管理のグローバルベストプラクティス
2. 代表的フレームワーク（Gartner・McKinsey・ITIL・COBIT等）
3. 大規模システムリプレースの成功・失敗事例と教訓
4. 日本企業での適用事例と留意点

日本語でわかりやすくまとめてください。
""".strip()

PROMPT_IMPLEMENT = """
あなたは中堅企業（従業員300人規模）の経営企画・IT戦略の専門家です。
理想のベストプラクティスを、リソースが限られた300人規模の企業で現実的に実現する方法を検討してください。

検討観点：
1. 人員・予算制約を踏まえた現実的アプローチ
2. 優先順位付けと段階的実施計画
3. 外部リソース（コンサル・ベンダー）の活用方法
4. 社内合意形成プロセスの現実解
5. クイックウィンとロングタームのバランス

具体的に日本語で。
""".strip()

PROMPT_STORY = """
あなたはマッキンゼー出身の戦略コンサルタントです。
以下を作成してください：

1. 論点ツリー（イシューを分解した構造的な問いの体系）
2. ストーリーライン（経営層を動かす論理の流れ）
3. 「空・雨・傘」による資料構成案
   - 空：現状認識・事実
   - 雨：分析・示唆
   - 傘：提言・アクション

MECEを徹底し、経営会議で最大の説得力を持つ構成を設計してください。日本語で。
""".strip()

PROMPT_WRITE = """
あなたは経営企画部門の資料作成の専門家です。
Markdown形式で、経営会議向けの資料を作成してください。

必須セクション：
1. エグゼクティブサマリー（3〜5行）
2. 背景・問題認識
3. 基本方針・原則
4. 実施プロセス・スケジュール（ステップ形式）
5. 投資規模の概算
6. 優先順位付けの基準
7. ガバナンス体制・承認フロー
8. リスクと対応方針
9. 今後のアクション

経営層が読む資料として、簡潔かつ説得力のある内容に。
固有名詞は「○○」のプレースホルダーを使用してください。
""".strip()

PROMPT_REVISE = """
あなたは経営企画部門の資料作成の専門家です。
初稿資料と複数ステークホルダーからの反論を踏まえ、資料を改善してください。

改善の方針：
- すべての反論を盲目的に取り込まず、重要度・妥当性で選別する
- 取り込む反論は資料に明示的に反映する
- 説得力と完成度を高める

Markdown形式で改善版を出力してください。
""".strip()

PROMPT_QA = """
あなたは経営会議のファシリテーター兼資料作成責任者です。
資料と各ステークホルダーからの反論を踏まえ、経営会議・取締役会で想定される質問と回答を作成してください。

出力形式：
---
**Q（質問者）：** 質問内容
**A：** 回答内容
---

最低15問、主要論点を網羅。難問・鋭い質問も含め、実際の会議で使える回答を。日本語で。
""".strip()


def critic_prompt(persona: str, focus: str) -> str:
    return f"""
あなたは{persona}です。
提示された経営資料に対して、{persona}の立場から徹底的に反論・問題提起してください。

特に以下の観点から具体的な問題点を指摘してください：
{focus}

遠慮なく、鋭く指摘してください。曖昧な反論ではなく、具体的に。日本語で。
""".strip()


CRITICS = [
    ("IT部門長",      "技術的実現可能性・IT部門の負荷・スケジュールの妥当性・技術的リスク・アーキテクチャ上の懸念"),
    ("CFO（財務）",   "投資対効果・コスト試算の根拠・資金調達計画・予算承認プロセス・財務リスク"),
    ("事業部門長",    "業務継続への影響・現場の実態との乖離・顧客・売上への影響・変革への現場抵抗"),
    ("CISO",          "情報セキュリティリスク・移行時のリスク・データ保護・サイバーリスク・コンプライアンス"),
    ("CRO（リスク）", "プロジェクトリスク・業務継続リスク・ベンダーリスク・規制対応・組織リスク"),
    ("CEO",           "経営戦略との整合性・競合優位性・市場環境・株主への説明責任・優先順位の妥当性"),
    ("社外取締役",    "ガバナンス・説明責任・株主価値・リスク監視・経営判断の妥当性・透明性"),
    ("金融庁",        "システムリスク管理規制・BCP要件・情報セキュリティ規制・内部統制・監督指針との整合性"),
    ("一般利用者",    "移行時の業務停止リスク・使い勝手の変化・トレーニング負担・現場への配慮不足・不安への対応"),
]


# ─────────────────────────────────────────────────────────────
# メインパイプライン
# ─────────────────────────────────────────────────────────────

async def run_pipeline(theme: str, background: str) -> dict:
    results = {}

    # Step 1: イシュー整理
    results["issue"] = await run_stream(
        PROMPT_ISSUE,
        f"テーマ: {theme}\n\n背景情報:\n{background}",
        "Step 1: イシュー整理",
    )

    # Step 2: ベストプラクティス調査（LLM知識ベース）
    results["research"] = await run_stream(
        PROMPT_RESEARCH,
        f"テーマ: {theme}\n\nイシュー整理結果:\n{results['issue']}",
        "Step 2: ベストプラクティス調査",
    )

    # Step 3: 300人規模での実現方法
    results["implement"] = await run_stream(
        PROMPT_IMPLEMENT,
        (
            f"テーマ: {theme}\n\n"
            f"イシュー:\n{results['issue']}\n\n"
            f"ベストプラクティス:\n{results['research']}"
        ),
        "Step 3: 300人規模での実現方法",
    )

    # Step 4: 論点ツリー・ストーリー
    results["story"] = await run_stream(
        PROMPT_STORY,
        (
            f"テーマ: {theme}\n\n"
            f"イシュー:\n{results['issue']}\n\n"
            f"実現方法:\n{results['implement']}"
        ),
        "Step 4: 論点ツリー・ストーリー作成",
    )

    # Step 5: 文書作成（初稿）
    results["draft"] = await run_stream(
        PROMPT_WRITE,
        (
            f"テーマ: {theme}\n\n"
            f"イシュー:\n{results['issue']}\n\n"
            f"ベストプラクティス:\n{results['research']}\n\n"
            f"実現方法:\n{results['implement']}\n\n"
            f"ストーリーライン:\n{results['story']}"
        ),
        "Step 5: 文書作成（初稿）",
    )

    # Step 6: 9ペルソナの反論（並列実行）
    print(f"\n{'─' * 60}")
    print("▶ Step 6: 反論生成（9ペルソナ 並列実行）")
    print(f"{'─' * 60}")

    draft_msg = f"以下の資料に対して、あなたの立場から徹底的に反論してください。\n\n{results['draft']}"

    critique_tasks = [
        run_silent(critic_prompt(persona, focus), draft_msg, persona)
        for persona, focus in CRITICS
    ]
    critique_results = await asyncio.gather(*critique_tasks)
    results["critiques"] = {p: r for (p, _), r in zip(CRITICS, critique_results)}

    # Step 7: 資料修正
    critiques_text = "\n\n".join(
        f"### {p}からの反論\n{r}"
        for p, r in results["critiques"].items()
    )
    results["revised"] = await run_stream(
        PROMPT_REVISE,
        (
            f"【初稿資料】\n{results['draft']}\n\n"
            f"【各ステークホルダーからの反論】\n{critiques_text}"
        ),
        "Step 7: 資料修正（最終版）",
    )

    # Step 8: 想定問答
    results["qa"] = await run_stream(
        PROMPT_QA,
        (
            f"【最終資料】\n{results['revised']}\n\n"
            f"【各ステークホルダーからの反論（参考）】\n{critiques_text}"
        ),
        "Step 8: 想定問答作成",
    )

    return results


# ─────────────────────────────────────────────────────────────
# 保存
# ─────────────────────────────────────────────────────────────

def save_output(theme: str, results: dict) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"pipeline_output_{ts}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {theme}\n")
        f.write(f"生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n\n---\n\n")

        for title, key in [
            ("Step 1: イシュー整理",          "issue"),
            ("Step 2: ベストプラクティス調査", "research"),
            ("Step 3: 300人規模での実現方法",  "implement"),
            ("Step 4: 論点ツリー・ストーリー", "story"),
            ("Step 5: 文書初稿",              "draft"),
            ("Step 7: 修正版資料（最終）",     "revised"),
            ("Step 8: 想定問答",              "qa"),
        ]:
            f.write(f"## {title}\n\n{results[key]}\n\n")

        f.write("## Step 6: 各ステークホルダーからの反論\n\n")
        for persona, critique in results["critiques"].items():
            f.write(f"### {persona}からの反論\n\n{critique}\n\n")

    return filename


# ─────────────────────────────────────────────────────────────
# エントリーポイント
# ─────────────────────────────────────────────────────────────

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


async def main():
    theme = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_THEME

    print("=" * 60)
    print("経営資料作成マルチエージェントパイプライン")
    print("=" * 60)
    print(f"\nテーマ: {theme}")
    print(f"\n背景:\n{DEFAULT_BACKGROUND}")
    print("\nパイプライン開始...\n")

    results = await run_pipeline(theme, DEFAULT_BACKGROUND)
    filename = save_output(theme, results)

    print(f"\n{'=' * 60}")
    print(f"✅ 完了！  出力ファイル: {filename}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
