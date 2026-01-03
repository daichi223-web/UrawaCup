# TournaMate - 報告書フォーマット仕様

---

# 1. 報告書の種類

| 種類 | 用途 | 出力タイミング |
|------|------|---------------|
| **日次試合結果報告書** | 各日の試合結果を報告 | 毎日の試合終了後 |
| **最終日組み合わせ表** | 順位リーグ・決勝トーナメントの組み合わせ | 予選終了後 |
| **最終結果報告書** | 決勝・3決の結果、優秀選手 | 大会終了後 |

---

# 2. 日次試合結果報告書

## 2.1 レイアウト

```
┌─────────────────────────────────────────────────────────────┐
│  第44回 浦和カップ高校サッカーフェスティバル 試合結果報告書  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  送信先：○○○○御中                                         │
│  発信元：県立浦和高校 森川大地                              │
│  連絡先：090-XXXX-XXXX                                      │
│                                                             │
│  2025年3月29日（第1日）                                     │
│  大会会場：浦和南高G                                        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  試合結果                                                    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 第1試合                                              │   │
│  │                                                      │   │
│  │   浦和南    0 - 2    専大北上                        │   │
│  │            0 前半 1                                  │   │
│  │            0 後半 1                                  │   │
│  │                                                      │   │
│  │ 得点経過                                             │   │
│  │ ┌──────┬──────────┬────────────┐                   │   │
│  │ │ 時間 │ チーム   │ 得点者名   │                   │   │
│  │ ├──────┼──────────┼────────────┤                   │   │
│  │ │  16  │ 専大北上 │ 山崎 諒太  │                   │   │
│  │ │  41  │ 専大北上 │ 稲葉 蓮    │                   │   │
│  │ └──────┴──────────┴────────────┘                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 第2試合                                              │   │
│  │                                                      │   │
│  │   東海大相模  1 - 0    健大高崎                      │   │
│  │              1 前半 0                                │   │
│  │              0 後半 0                                │   │
│  │                                                      │   │
│  │ 得点経過                                             │   │
│  │ ┌──────┬────────────┬────────────┐                 │   │
│  │ │ 時間 │ チーム     │ 得点者名   │                 │   │
│  │ ├──────┼────────────┼────────────┤                 │   │
│  │ │   6  │ 東海大相模 │ 戸川 昌也  │                 │   │
│  │ └──────┴────────────┴────────────┘                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  （第3試合、第4試合...続く）                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 2.2 データ構造

```typescript
interface DailyReport {
  tournament: {
    name: string;           // "第44回 浦和カップ高校サッカーフェスティバル"
    edition: number;        // 44
  };
  reportDate: string;       // "2025-03-29"
  dayNumber: number;        // 1 (第1日)
  venue: {
    name: string;           // "浦和南高G"
  };
  sender: {
    organization: string;   // "県立浦和高校"
    name: string;           // "森川大地"
    contact: string;        // "090-XXXX-XXXX"
  };
  recipients: string[];     // ["埼玉県サッカー協会", "さいたま市サッカー協会", ...]
  matches: MatchResult[];
}

interface MatchResult {
  matchNumber: number;      // 1, 2, 3, 4...
  homeTeam: string;         // "浦和南"
  awayTeam: string;         // "専大北上"
  homeScoreHalf1: number;   // 0
  homeScoreHalf2: number;   // 0
  homeScoreTotal: number;   // 0
  awayScoreHalf1: number;   // 1
  awayScoreHalf2: number;   // 1
  awayScoreTotal: number;   // 2
  hasPenaltyShootout: boolean;
  homePK?: number;
  awayPK?: number;
  goals: Goal[];
}

interface Goal {
  minute: number;           // 16 (前半16分 or 後半16分=41分として記録)
  team: string;             // "専大北上"
  scorer: string;           // "山崎 諒太"
}
```

## 2.3 PDF生成仕様

| 項目 | 仕様 |
|------|------|
| 用紙サイズ | A4 |
| 向き | 縦 |
| マージン | 上下左右 20mm |
| フォント | IPAゴシック / Noto Sans JP |
| 文字サイズ（タイトル） | 14pt |
| 文字サイズ（本文） | 10pt |
| 文字サイズ（表） | 9pt |
| 1ページあたり試合数 | 4試合（得点経過の量による） |

---

# 3. 最終日組み合わせ表

## 3.1 レイアウト

```
┌─────────────────────────────────────────────────────────────────────────┐
│              3月31日（日）【順位リーグ】                                 │
├───────────────┬───────────────┬───────────────┬───────────────┬────────┤
│   浦和南高G   │  市立浦和高G  │  浦和学院高G  │    武南高G    │        │
├───────┬───────┼───────┬───────┼───────┬───────┼───────┬───────┤        │
│ KO    │ 対戦  │ KO    │ 対戦  │ KO    │ 対戦  │ KO    │ 対戦  │        │
├───────┼───────┼───────┼───────┼───────┼───────┼───────┼───────┤        │
│ 9:30  │4位③  │ 9:00  │野辺地西│ 9:30  │浦和学院│ 9:30  │武南   │ 審判欄 │
│       │vs     │       │vs     │       │vs     │       │vs     │        │
│       │5位①  │       │日大明誠│       │C1位   │       │聖和学園│        │
├───────┼───────┼───────┼───────┼───────┼───────┼───────┼───────┤        │
│10:35  │明秀日立│10:05  │市立浦和│10:35  │旭川実業│10:35  │國學院 │        │
│       │vs     │       │vs     │       │vs     │       │久我山 │        │
│       │日本文理│       │敬愛学園│       │東海大相模│     │vs韮崎 │        │
├───────┼───────┼───────┼───────┼───────┼───────┼───────┼───────┤        │
│ ...   │ ...   │ ...   │ ...   │ ...   │ ...   │ ...   │ ...   │        │
└───────┴───────┴───────┴───────┴───────┴───────┴───────┴───────┴────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│              3月31日（日）【3決・決勝戦】                                │
├─────────────────────────────────────────────────────────────────────────┤
│                        駒場スタジアム                                    │
├───────┬─────────────────────────────┬───────────────────────────────────┤
│ KO    │           対戦             │              審判                 │
├───────┼─────────────────────────────┼───────────────────────────────────┤
│ 9:00  │ ツエーゲン金沢 vs 浦和RY   │ 主審：派遣  副審：当該            │
├───────┼─────────────────────────────┼───────────────────────────────────┤
│10:05  │ 研修                        │                                   │
├───────┼─────────────────────────────┼───────────────────────────────────┤
│12:00  │ 3位決 A1位 vs C1位          │ 主審：派遣  副審：派遣            │
├───────┼─────────────────────────────┼───────────────────────────────────┤
│13:05  │ 決勝  B1位 vs D1位          │ 主審：派遣  副審：派遣            │
└───────┴─────────────────────────────┴───────────────────────────────────┘
```

## 3.2 データ構造

```typescript
interface FinalDaySchedule {
  date: string;             // "2025-03-31"
  sections: ScheduleSection[];
}

interface ScheduleSection {
  title: string;            // "順位リーグ" | "3決・決勝戦"
  venues: VenueSchedule[];
}

interface VenueSchedule {
  venue: string;            // "浦和南高G"
  venueManager: string;     // "浦和南"
  matches: FinalMatch[];
}

interface FinalMatch {
  matchNumber: number;
  kickoffTime: string;      // "9:30"
  homeTeam: string;         // "4位③" or "浦和南"
  awayTeam: string;         // "5位①" or "市立浦和"
  matchType?: string;       // "準決勝" | "3位決" | "決勝" | "研修"
  referee: {
    main: string;           // "派遣" | "当該"
    assistant: string;      // "当該"
  };
}
```

---

# 4. 最終結果報告書

## 4.1 レイアウト

```
┌─────────────────────────────────────────────────────────────┐
│  第44回浦和カップ高校サッカーフェスティバル 組合せ及び日程表 │
│                     2025年3月31日                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ☆順位決定戦                                                │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               準決勝1                                │   │
│  │   A1位(浦和南)  1 - 0  C1位(浦和学院)                │   │
│  │                 1 前半 0                             │   │
│  │                 0 後半 0                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               準決勝2                                │   │
│  │   B1位(市立浦和)  2 - 2  D1位(武南)                  │   │
│  │                   2 前半 0                           │   │
│  │                   0 後半 2                           │   │
│  │                   4 PK  5                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               3位決定戦                              │   │
│  │   市立浦和  1 - 1  浦和学院                          │   │
│  │             1 前半 1                                 │   │
│  │             0 後半 0                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               決勝                                   │   │
│  │   浦和南  1 - 3  武南                                │   │
│  │           1 前半 3                                   │   │
│  │           0 後半 0                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  ☆最終順位                                                  │
│                                                             │
│  ┌──────┬────────────────────┐                             │
│  │ 順位 │ チーム名           │                             │
│  ├──────┼────────────────────┤                             │
│  │ 1位  │ 浦和レッズユース   │                             │
│  │ 2位  │ 富士市立           │                             │
│  │ 3位  │ 市立浦和           │                             │
│  │ 4位  │ 佐野日大           │                             │
│  └──────┴────────────────────┘                             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  ☆優秀選手                                                  │
│                                                             │
│  ┌────────────┬────────────────┬────────────────────┐      │
│  │ 賞         │ 名前           │ チーム名           │      │
│  ├────────────┼────────────────┼────────────────────┤      │
│  │ 最優秀選手 │ 中村 虎太郎    │ 浦和レッズユース   │      │
│  │ 優秀選手   │ 安藤 純和      │ 浦和レッズユース   │      │
│  │ 優秀選手   │ マルコム A.恵太│ 浦和レッズユース   │      │
│  │ 優秀選手   │ 蔦澤 洋紀      │ 浦和レッズユース   │      │
│  │ 優秀選手   │ 和田 武士      │ 浦和レッズユース   │      │
│  │ 優秀選手   │ 青木 利仁      │ 富士市立           │      │
│  │ ...        │ ...            │ ...                │      │
│  └────────────┴────────────────┴────────────────────┘      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  ☆研修試合結果                                              │
│                                                             │
│  （各会場の研修試合結果一覧）                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 4.2 データ構造

```typescript
interface FinalReport {
  tournament: {
    name: string;
    edition: number;
    date: string;
  };
  knockoutResults: KnockoutMatch[];
  finalRankings: FinalRanking[];
  outstandingPlayers: OutstandingPlayer[];
  trainingMatchResults: TrainingMatchResult[];
}

interface KnockoutMatch {
  round: string;            // "準決勝1" | "準決勝2" | "3位決定戦" | "決勝"
  homeTeam: {
    seed: string;           // "A1位"
    name: string;           // "浦和南"
  };
  awayTeam: {
    seed: string;           // "C1位"
    name: string;           // "浦和学院"
  };
  homeScoreHalf1: number;
  homeScoreHalf2: number;
  homeScoreTotal: number;
  awayScoreHalf1: number;
  awayScoreHalf2: number;
  awayScoreTotal: number;
  hasPenaltyShootout: boolean;
  homePK?: number;
  awayPK?: number;
}

interface FinalRanking {
  rank: number;             // 1, 2, 3, 4
  teamName: string;         // "浦和レッズユース"
}

interface OutstandingPlayer {
  award: string;            // "最優秀選手" | "優秀選手"
  playerName: string;       // "中村 虎太郎"
  teamName: string;         // "浦和レッズユース"
}

interface TrainingMatchResult {
  venue: string;
  matches: MatchResult[];
}
```

---

# 5. 研修試合一覧表

## 5.1 レイアウト

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ☆研修試合結果                                    │
│                        2025年3月31日                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【浦和南高G】                                                          │
│  ┌────┬─────────────┬───────┬─────────────┬────────────────────┐      │
│  │ No │ ホーム      │スコア │ アウェイ    │ 前半/後半          │      │
│  ├────┼─────────────┼───────┼─────────────┼────────────────────┤      │
│  │  1 │ 浦和南      │ 0 - 2 │ 聖和学園    │ 0-1 / 0-1          │      │
│  │  2 │ 浦和南      │ 0 - 0 │ 日大明誠    │ 0-0 / 0-0          │      │
│  │  3 │ 日大明誠    │ 1 - 0 │ 聖和学園    │ 0-0 / 1-0          │      │
│  └────┴─────────────┴───────┴─────────────┴────────────────────┘      │
│                                                                         │
│  【市立浦和高G】                                                        │
│  ┌────┬─────────────┬───────┬─────────────┬────────────────────┐      │
│  │ No │ ホーム      │スコア │ アウェイ    │ 前半/後半          │      │
│  ├────┼─────────────┼───────┼─────────────┼────────────────────┤      │
│  │  1 │ 市立浦和    │ 3 - 3 │ 富士市立    │ 1-3 / 2-0 (PK 4-5) │      │
│  │  2 │ 日本文理    │ 0 - 0 │ 旭川実業    │ 0-0 / 0-0          │      │
│  │  3 │ RB大宮      │ 0 - 0 │ 旭川実業    │ 0-0 / 0-0          │      │
│  │  4 │ 市立浦和    │ 0 - 1 │ 旭川実業    │ 0-1 / 0-0          │      │
│  └────┴─────────────┴───────┴─────────────┴────────────────────┘      │
│                                                                         │
│  （他会場も同様に続く）                                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

# 6. 送信先設定

## 6.1 デフォルト送信先

```typescript
interface ReportRecipient {
  id: number;
  name: string;             // "埼玉県サッカー協会"
  email?: string;           // "info@saitama-fa.or.jp"
  fax?: string;             // "048-XXX-XXXX"
  isDefault: boolean;       // true
}
```

## 6.2 設定画面

```
┌─────────────────────────────────────────────────────────────┐
│  報告書送信先設定                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ☑ 埼玉県サッカー協会                                │   │
│  │ ☑ さいたま市サッカー協会                            │   │
│  │ ☑ 各参加校                                          │   │
│  │ ☐ 報道機関                                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  発信元情報                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 所属：[県立浦和高校                              ]  │   │
│  │ 氏名：[森川大地                                  ]  │   │
│  │ 連絡先：[090-XXXX-XXXX                           ]  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│                              [キャンセル]  [保存]           │
└─────────────────────────────────────────────────────────────┘
```

---

# 7. PDF生成実装

## 7.1 使用ライブラリ

| ライブラリ | 用途 |
|-----------|------|
| **ReportLab** (Python) | PDF生成 |
| **WeasyPrint** (Python) | HTML→PDF変換（代替案） |
| **jsPDF** (JS) | フロントエンドでのPDF生成（オプション） |

## 7.2 バックエンド実装例

```python
# app/services/report_generator.py

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 日本語フォント登録
pdfmetrics.registerFont(TTFont('IPAGothic', 'fonts/ipag.ttf'))

class DailyReportGenerator:
    def __init__(self, report_data: DailyReport):
        self.data = report_data
        self.styles = getSampleStyleSheet()
        self.styles['Normal'].fontName = 'IPAGothic'
        
    def generate(self, output_path: str) -> str:
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        elements = []
        
        # タイトル
        elements.append(Paragraph(
            f"{self.data.tournament.name} 試合結果報告書",
            self.styles['Title']
        ))
        elements.append(Spacer(1, 12))
        
        # ヘッダー情報
        elements.append(Paragraph(f"送信先：○○御中", self.styles['Normal']))
        elements.append(Paragraph(
            f"発信元：{self.data.sender.organization} {self.data.sender.name}",
            self.styles['Normal']
        ))
        elements.append(Paragraph(
            f"連絡先：{self.data.sender.contact}",
            self.styles['Normal']
        ))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph(
            f"{self.data.report_date}（第{self.data.day_number}日）",
            self.styles['Normal']
        ))
        elements.append(Paragraph(
            f"大会会場：{self.data.venue.name}",
            self.styles['Normal']
        ))
        elements.append(Spacer(1, 24))
        
        # 各試合
        for match in self.data.matches:
            elements.extend(self._create_match_section(match))
            elements.append(Spacer(1, 16))
        
        doc.build(elements)
        return output_path
    
    def _create_match_section(self, match: MatchResult) -> list:
        elements = []
        
        # 試合タイトル
        elements.append(Paragraph(
            f"第{match.match_number}試合",
            self.styles['Heading2']
        ))
        
        # スコア
        score_data = [
            [match.home_team, f"{match.home_score_total} - {match.away_score_total}", match.away_team],
            ['', f"{match.home_score_half1} 前半 {match.away_score_half1}", ''],
            ['', f"{match.home_score_half2} 後半 {match.away_score_half2}", ''],
        ]
        
        if match.has_penalty_shootout:
            score_data.append(['', f"{match.home_pk} PK {match.away_pk}", ''])
        
        score_table = Table(score_data, colWidths=[150, 100, 150])
        score_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'IPAGothic'),
        ]))
        elements.append(score_table)
        
        # 得点経過
        if match.goals:
            elements.append(Paragraph("得点経過", self.styles['Heading3']))
            
            goal_data = [['時間', 'チーム', '得点者名']]
            for goal in match.goals:
                goal_data.append([str(goal.minute), goal.team, goal.scorer])
            
            goal_table = Table(goal_data, colWidths=[50, 100, 150])
            goal_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 0), (-1, -1), 'IPAGothic'),
            ]))
            elements.append(goal_table)
        
        return elements
```

## 7.3 API エンドポイント

```python
# app/api/reports.py

@router.post("/tournaments/{tournament_id}/reports/generate")
async def generate_report(
    tournament_id: int,
    request: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    job_id = str(uuid.uuid4())
    
    # ジョブをDBに登録
    job = ReportJob(
        id=job_id,
        tournament_id=tournament_id,
        status="pending",
        report_type=request.report_type,
        parameters=request.dict()
    )
    db.add(job)
    db.commit()
    
    # バックグラウンドで生成
    background_tasks.add_task(
        generate_report_task,
        job_id=job_id,
        tournament_id=tournament_id,
        report_type=request.report_type,
        date=request.date,
        venue_id=request.venue_id
    )
    
    return {"jobId": job_id}


@router.get("/reports/jobs/{job_id}")
async def get_report_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(ReportJob).filter(ReportJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404)
    
    return {
        "jobId": job.id,
        "status": job.status,
        "progress": job.progress,
        "url": job.file_url if job.status == "completed" else None,
        "error": job.error_message if job.status == "failed" else None
    }
```

---

# 8. 印刷設定

## 8.1 ブラウザ印刷用CSS

```css
@media print {
  /* ページ設定 */
  @page {
    size: A4;
    margin: 20mm;
  }
  
  /* 改ページ制御 */
  .match-result {
    page-break-inside: avoid;
  }
  
  .page-break {
    page-break-after: always;
  }
  
  /* 不要要素を非表示 */
  .no-print {
    display: none !important;
  }
  
  /* 背景色を印刷 */
  * {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
}
```

## 8.2 印刷プレビュー画面

```tsx
// src/pages/admin/ReportPreview.tsx

export function ReportPreview() {
  const handlePrint = () => {
    window.print();
  };
  
  return (
    <div>
      <div className="no-print mb-4">
        <button onClick={handlePrint}>印刷</button>
        <button onClick={downloadPDF}>PDFダウンロード</button>
      </div>
      
      <div className="print-area">
        {/* 報告書コンテンツ */}
      </div>
    </div>
  );
}
```
