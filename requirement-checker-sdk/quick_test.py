"""
クイックテスト - SDKの動作確認
"""
import sys
from pathlib import Path

# 設定
PROJECT_ROOT = Path("D:/UrawaCup")
OUTPUT_FILE = Path(__file__).parent / "test_output.txt"

def main():
    results = []
    results.append("=" * 60)
    results.append("UrawaCup 要件チェックSDK クイックテスト")
    results.append("=" * 60)
    results.append(f"Project root: {PROJECT_ROOT}")
    results.append(f"Src exists: {(PROJECT_ROOT / 'src').exists()}")
    results.append("")

    # ファイル数をカウント（node_modules除外）
    import glob
    EXCLUDE_DIRS = {'node_modules', '.git', '__pycache__', '.venv', 'venv', 'dist', 'build'}

    def should_exclude(path):
        return any(excluded in path for excluded in EXCLUDE_DIRS)

    py_files = [f for f in glob.glob(str(PROJECT_ROOT / "src" / "**/*.py"), recursive=True) if not should_exclude(f)]
    ts_files = [f for f in glob.glob(str(PROJECT_ROOT / "src" / "**/*.ts"), recursive=True) if not should_exclude(f)]
    tsx_files = [f for f in glob.glob(str(PROJECT_ROOT / "src" / "**/*.tsx"), recursive=True) if not should_exclude(f)]

    results.append(f"Python files: {len(py_files)}")
    results.append(f"TypeScript files: {len(ts_files)}")
    results.append(f"TSX files: {len(tsx_files)}")
    results.append("")

    # 主要ファイルの存在確認
    key_files = [
        "src/backend/models/team.py",
        "src/backend/models/match.py",
        "src/backend/models/standing.py",
        "src/backend/services/standing_service.py",
        "src/backend/services/report_service.py",
        "src/backend/routes/auth.py",
        "src/backend/utils/auth.py",
        "src/frontend/src/stores/authStore.ts",
    ]

    results.append("主要ファイル存在チェック:")
    for f in key_files:
        exists = (PROJECT_ROOT / f).exists()
        status = "[OK]" if exists else "[NG]"
        results.append(f"  {status} {f}")

    results.append("")
    results.append("テスト完了")

    # 出力
    output = "\n".join(results)
    print(output)

    # ファイルにも保存
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"\n結果を保存: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
