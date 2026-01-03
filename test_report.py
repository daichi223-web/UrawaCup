"""報告書サブモジュールのテスト"""
import sys
sys.path.insert(0, "D:/UrawaCup/src/backend")

from datetime import date
from database import SessionLocal

# サブモジュールのインポートテスト
try:
    from services.reports import (
        DailyReportGenerator,
        FinalDayScheduleGenerator,
        FinalResultReportGenerator,
        SenderInfo,
        FinalRanking,
        OutstandingPlayer,
    )
    from services.reports.types import DailyReportData, MatchResultData, GoalData
    print("OK: サブモジュールのインポート成功")
except ImportError as e:
    print(f"ERROR: インポート失敗 - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# データベースセッション
db = SessionLocal()

try:
    # 試合データの確認
    from models.match import Match, MatchStatus
    matches = db.query(Match).filter(
        Match.tournament_id == 1,
        Match.status == MatchStatus.COMPLETED
    ).all()

    print(f"\n完了済み試合数: {len(matches)}")

    if matches:
        # 最初の完了試合の日付を取得
        sample_match = matches[0]
        target_date = sample_match.match_date
        print(f"対象日: {target_date}")

        # DailyReportGenerator のテスト
        print("\nDailyReportGeneratorのテスト...")

        sender = SenderInfo(
            organization="テスト高校",
            name="テスト太郎",
            contact="000-0000-0000"
        )

        generator = DailyReportGenerator(
            db=db,
            tournament_id=1,
            target_date=target_date,
            venue_id=None,
            sender=sender,
        )

        # データ読み込みテスト
        data = generator._load_data()
        print(f"  大会名: {data.tournament.name}")
        print(f"  日付: {data.report_date}")
        print(f"  第{data.day_number}日")
        print(f"  試合数: {len(data.matches)}")

        for match in data.matches[:3]:  # 最初の3試合を表示
            print(f"    - 第{match.match_number}試合: {match.home_team} {match.score_display} {match.away_team}")
            for goal in match.goals:
                print(f"      得点: {goal.scorer_name} ({goal.team_name})")

        # PDF生成テスト
        print("\nPDF生成テスト...")
        try:
            pdf_buffer = generator.generate()
            pdf_size = len(pdf_buffer.getvalue())
            print(f"  PDF生成成功: {pdf_size} bytes")

            # テスト用にファイルに保存
            with open("D:/UrawaCup/test_report_output.pdf", "wb") as f:
                f.write(pdf_buffer.getvalue())
            print("  保存先: D:/UrawaCup/test_report_output.pdf")
        except Exception as e:
            print(f"  PDF生成エラー: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("完了済み試合がありません。テストデータを作成してください。")

    # FinalDayScheduleGenerator のテスト
    print("\n=== FinalDayScheduleGenerator のテスト ===")
    try:
        schedule_generator = FinalDayScheduleGenerator(
            db=db,
            tournament_id=1,
            target_date=target_date,
        )
        schedule_pdf = schedule_generator.generate()
        schedule_size = len(schedule_pdf.getvalue())
        print(f"  PDF生成成功: {schedule_size} bytes")

        with open("D:/UrawaCup/test_schedule_output.pdf", "wb") as f:
            f.write(schedule_pdf.getvalue())
        print("  保存先: D:/UrawaCup/test_schedule_output.pdf")
    except Exception as e:
        print(f"  エラー: {e}")
        import traceback
        traceback.print_exc()

    # FinalResultReportGenerator のテスト
    print("\n=== FinalResultReportGenerator のテスト ===")
    try:
        # テスト用のサンプルデータ
        sample_rankings = [
            FinalRanking(rank=1, team_name="浦和南"),
            FinalRanking(rank=2, team_name="武南"),
            FinalRanking(rank=3, team_name="浦和学院"),
            FinalRanking(rank=4, team_name="市立浦和"),
        ]
        sample_players = [
            OutstandingPlayer(award="最優秀選手", player_name="山田太郎", team_name="浦和南"),
            OutstandingPlayer(award="優秀選手", player_name="鈴木一郎", team_name="武南"),
        ]

        result_generator = FinalResultReportGenerator(
            db=db,
            tournament_id=1,
            final_rankings=sample_rankings,
            outstanding_players=sample_players,
        )
        result_pdf = result_generator.generate()
        result_size = len(result_pdf.getvalue())
        print(f"  PDF生成成功: {result_size} bytes")

        with open("D:/UrawaCup/test_result_output.pdf", "wb") as f:
            f.write(result_pdf.getvalue())
        print("  保存先: D:/UrawaCup/test_result_output.pdf")
    except Exception as e:
        print(f"  エラー: {e}")
        import traceback
        traceback.print_exc()

finally:
    db.close()

print("\n全テスト完了")
