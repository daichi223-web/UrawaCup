"""
SDK実行スクリプト - 結果をファイルに出力
"""
import sys
from pathlib import Path
from datetime import datetime

# 出力先設定
OUTPUT_FILE = Path(__file__).parent / "sdk_result.txt"
PROJECT_ROOT = "D:/UrawaCup"

# 出力バッファ
output_lines = []

def log(msg):
    output_lines.append(msg)
    # ファイルにも即時書き込み
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def main():
    # 初期化
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"SDK実行開始: {datetime.now()}\n")

    log("=" * 60)
    log("UrawaCup 要件チェックSDK")
    log("=" * 60)
    log(f"Project: {PROJECT_ROOT}")
    log("")

    # SDKインポート
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from src.code_checker import CodeChecker, format_summary
        from src.requirements_data import Phase
        log("SDKモジュールをインポートしました")
    except Exception as e:
        log(f"インポートエラー: {e}")
        return

    # チェッカー初期化
    log("チェッカーを初期化中...")
    checker = CodeChecker(PROJECT_ROOT)

    # 各フェーズごとにチェック
    for phase in [Phase.MINI, Phase.MIDDLE, Phase.MAX]:
        log(f"\n--- Phase {phase.value} ---")
        try:
            summary = checker.check_by_phase(phase)
            log(f"Total: {summary.total_requirements}")
            log(f"Completed: {summary.completed}")
            log(f"Partial: {summary.partial}")
            log(f"In Progress: {summary.in_progress}")
            log(f"Not Started: {summary.not_started}")
            log(f"Rate: {summary.completion_rate:.1f}%")

            # 詳細結果
            for result in summary.results:
                status_str = result.status.value
                log(f"  [{status_str}] {result.requirement.id}: {result.requirement.name}")
        except Exception as e:
            log(f"エラー: {e}")
            import traceback
            log(traceback.format_exc())

    log("\n" + "=" * 60)
    log(f"完了: {datetime.now()}")

if __name__ == "__main__":
    main()
    print(f"結果は {OUTPUT_FILE} に保存されました")
