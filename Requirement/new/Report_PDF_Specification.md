# 報告書（PDF）詳細仕様

## 1. 報告書の種類

| 報告書 | 内容 | 出力タイミング |
|--------|------|---------------|
| 日別試合結果 | その日の全試合結果・得点経過 | 毎日（1日目、2日目、3日目） |
| 最終結果 | 決勝T結果、最終順位、優秀選手、研修試合結果 | 大会終了後 |

---

## 2. 日別試合結果報告書

### 2.1 ヘッダー部分

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│     送信先：                                              御中              │
│     発信元：          県立浦和高校　森川大地                    2025.3.29   │
│     連絡先：          090－XXXX－XXXX                                       │
│                                                                             │
│         第44回　浦和カップ高校サッカーフェスティバル                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 会場別試合ブロック（繰り返し）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  大会会場：          浦和南高                                  Ｇ           │
├───────────────────────────────────────────┬─────────────────────────────────┤
│            試合結果                        │          得点経過              │
│                                           │   時間      │     チーム       │
├───────────────────────────────────────────┼─────────────┼─────────────────┤
│                                           │    16       │   専大北上      │
│  第        浦和南       VS    専大北上    │    41       │   専大北上      │
│  1     0       前半         1             │             │                 │
│  試合  0       後半         1             │             │                 │
├───────────────────────────────────────────┼─────────────┼─────────────────┤
│                                           │     6       │   東海大相模    │
│  第        東海大相模   VS    健大高崎    │             │                 │
│  2     1       前半         0             │             │                 │
│  試合  0       後半         0             │             │                 │
├───────────────────────────────────────────┼─────────────┼─────────────────┤
│  ... 続く                                 │             │                 │
└───────────────────────────────────────────┴─────────────┴─────────────────┘
```

### 2.3 データ構造

```typescript
interface DailyReportData {
  // ヘッダー
  header: {
    recipient: string;           // "御中"（固定または設定）
    sender: string;              // "県立浦和高校　森川大地"
    contact: string;             // "090－XXXX－XXXX"
    date: string;                // "2025.3.29"
    tournamentName: string;      // "第44回　浦和カップ高校サッカーフェスティバル"
  };
  
  // 会場別ブロック
  venueBlocks: VenueBlock[];
}

interface VenueBlock {
  venueName: string;             // "浦和南高"
  venueType: string;             // "Ｇ"
  matches: MatchResult[];
}

interface MatchResult {
  matchNumber: number;           // 第1試合、第2試合...
  homeTeam: string;
  awayTeam: string;
  homeScoreHalf1: number;
  homeScoreHalf2: number;
  awayScoreHalf1: number;
  awayScoreHalf2: number;
  // PK戦がある場合
  homePK?: number;
  awayPK?: number;
  // 得点経過
  goals: GoalEvent[];
}

interface GoalEvent {
  minute: number;                // 得点時間
  team: string;                  // 得点チーム名
  scorerName?: string;           // 得点者名（任意）
}
```

### 2.4 レイアウト仕様

| 項目 | 値 |
|------|-----|
| 用紙サイズ | A4縦 |
| マージン | 上下左右 15mm |
| フォント | MS ゴシック（または NotoSansJP） |
| ヘッダーフォントサイズ | 11pt |
| タイトルフォントサイズ | 16pt（太字） |
| 本文フォントサイズ | 11pt |
| 行高さ | 約22.5pt |

### 2.5 列構成（試合結果部分）

```
列A: 余白（幅1）
列B: 第X試合（幅4）
列C-D: ホームチーム名（幅26、結合）
列E: ホームスコア（幅13）
列F: 前半/後半ラベル（幅13）
列G: VS（幅13）
列H-K: アウェイチーム名（幅52、結合）
列L-N: 得点時間（幅39、結合）
列O-R: 得点チーム（幅52、結合）
```

---

## 3. 最終結果報告書

### 3.1 全体構成

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  第44回浦和カップ高校サッカーフェスティバル                                 │
│  2025年3月31日                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ☆順位決定戦                                                               │
│                                                                             │
│    試合結果                              │          試合結果                │
│  ───────────────────────────────────────┼────────────────────────────────  │
│  ３位決定戦                              │  準決勝                          │
│       市立浦和    VS    佐野日大         │       浦和RY    VS    佐野日大   │
│   1       0   前半        0          0  │   2       2   前半        0      │
│           1   後半        0              │           0   後半        0      │
│  ───────────────────────────────────────┼────────────────────────────────  │
│  決勝                                    │  準決勝                          │
│       浦和RY     VS    富士市立          │       富士市立  VS    佐野日大   │
│   2       1   前半        1          1  │   3       1   前半        3      │
│           1   後半        0              │           2   後半        0      │
│                                          │           4   PK         5      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ☆研修試合結果                                                             │
│                                                                             │
│  浦和南高G          │  市立浦和高G       │  ＲＨＦ駒場                      │
│  ────────────────────┼───────────────────┼────────────────────────────────  │
│  浦和南 vs 聖和学園  │  日本文理 vs 旭川実業│  浦和RY vs 佐野日大           │
│   0      前半    1  │   0      前半    0 │   2      前半    0              │
│   0      後半    1  │   0      後半    0 │   0      後半    0              │
│  ────────────────────┼───────────────────┼────────────────────────────────  │
│  ... 続く            │  ... 続く          │  ... 続く                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ☆優秀選手                                                                 │
│                                                                             │
│  順位  │  チーム名            │              │  名前          │  チーム名   │
│  ─────┼──────────────────────┼──────────────┼────────────────┼─────────────│
│  １位  │  浦和レッズユース    │  最優秀選手  │  中村 虎太郎   │  浦和RY     │
│  ２位  │  富士市立            │  優秀選手    │  安藤 純和     │  浦和RY     │
│  ３位  │  市立浦和            │  優秀選手    │  田中 一郎     │  富士市立   │
│  ４位  │  佐野日大            │  優秀選手    │  ...           │  ...        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 データ構造

```typescript
interface FinalResultReportData {
  // ヘッダー
  tournamentName: string;
  date: string;
  
  // 順位決定戦
  knockout: {
    thirdPlace: KnockoutMatch;     // 3位決定戦
    final: KnockoutMatch;          // 決勝
    semifinal1: KnockoutMatch;     // 準決勝1
    semifinal2: KnockoutMatch;     // 準決勝2
  };
  
  // 研修試合結果（会場別）
  trainingResults: TrainingVenueResult[];
  
  // 最終順位
  standings: FinalStanding[];
  
  // 優秀選手
  awards: AwardData[];
}

interface KnockoutMatch {
  matchType: string;              // "３位決定戦", "決勝", "準決勝"
  homeTeam: string;
  awayTeam: string;
  homeScoreHalf1: number;
  homeScoreHalf2: number;
  awayScoreHalf1: number;
  awayScoreHalf2: number;
  homeTotalScore: number;
  awayTotalScore: number;
  homePK?: number;
  awayPK?: number;
}

interface TrainingVenueResult {
  venueName: string;              // "浦和南高G", "市立浦和高G", "ＲＨＦ駒場"
  matches: TrainingMatch[];
}

interface TrainingMatch {
  homeTeam: string;
  awayTeam: string;
  homeScoreHalf1: number;
  homeScoreHalf2: number;
  awayScoreHalf1: number;
  awayScoreHalf2: number;
  homePK?: number;
  awayPK?: number;
}

interface FinalStanding {
  rank: number;                   // 1, 2, 3, 4
  teamName: string;
}

interface AwardData {
  awardType: 'mvp' | 'outstanding';
  playerName: string;
  teamName: string;
}
```

---

## 4. PDF生成仕様

### 4.1 使用ライブラリ

```
ReportLab（Python）
- 日本語フォント: NotoSansJP-Regular.ttf
```

### 4.2 フォント設定

```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 日本語フォント登録
pdfmetrics.registerFont(TTFont('NotoSansJP', 'NotoSansJP-Regular.ttf'))
pdfmetrics.registerFont(TTFont('NotoSansJP-Bold', 'NotoSansJP-Bold.ttf'))
```

### 4.3 ページ設定

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_TOP = 15 * mm
MARGIN_BOTTOM = 15 * mm
MARGIN_LEFT = 15 * mm
MARGIN_RIGHT = 15 * mm
```

### 4.4 色設定

```python
from reportlab.lib.colors import black, white, HexColor

COLOR_HEADER_BG = HexColor('#E0E0E0')    # ヘッダー背景
COLOR_BORDER = black                       # 罫線
COLOR_TEXT = black                         # テキスト
```

---

## 5. テーブルレイアウト詳細

### 5.1 日別試合結果 - 1試合分のセル構成

```
┌────┬────────────────┬─────┬──────┬─────┬────────────────┬───────┬──────────┐
│ B  │     C-D        │  E  │  F   │  G  │     H-K        │ L-N   │   O-R    │
├────┼────────────────┼─────┼──────┼─────┼────────────────┼───────┼──────────┤
│    │                │     │      │     │                │  16   │ 専大北上 │ ← 得点経過1
│ 第 │    浦和南      │     │      │ VS  │   専大北上     │  41   │ 専大北上 │ ← 得点経過2
│ 1  │      0         │     │ 前半 │     │      1         │       │          │
│試合│      0         │     │ 後半 │     │      1         │       │          │
├────┼────────────────┼─────┼──────┼─────┼────────────────┼───────┼──────────┤

セル構成:
- B列: 第X試合（3行結合）
- C-D列: ホームチーム名（1行目）、ホームスコア（2-3行目）
- F列: 前半/後半ラベル
- G列: VS
- H-K列: アウェイチーム名、アウェイスコア
- L-N列: 得点時間（複数行可）
- O-R列: 得点チーム名（複数行可）
```

### 5.2 得点経過の表示ルール

```
【得点経過の表示】
- 得点があった時間と得点チーム名を縦に並べる
- 最大表示行数: 試合ブロックの高さに依存（通常4行）
- 時間は分単位（例: 16, 41, 45+2）
- 同時間の得点は同じ行に表示

【例】
時間  │ チーム
──────┼──────────
 16   │ 専大北上
 41   │ 専大北上
 6    │ 浦和南
 51   │ 東海大相模
```

---

## 6. API仕様

### 6.1 日別報告書PDF生成

```yaml
POST /tournaments/{id}/reports/daily

Request:
{
  "date": "2025-03-29",
  "venueIds": [1, 2, 3, 4]    // 省略時は全会場
}

Response:
{
  "downloadUrl": "/downloads/report_2025-03-29.pdf",
  "filename": "浦和カップ_試合結果_2025-03-29.pdf"
}
```

### 6.2 最終結果報告書PDF生成

```yaml
POST /tournaments/{id}/reports/final

Response:
{
  "downloadUrl": "/downloads/final_result.pdf",
  "filename": "浦和カップ_最終結果.pdf"
}
```

### 6.3 報告書設定取得・更新

```yaml
GET /tournaments/{id}/report-settings

Response:
{
  "senderOrganization": "県立浦和高校サッカー部",
  "senderName": "森川大地",
  "senderContact": "090-XXXX-XXXX",
  "recipients": ["埼玉県サッカー協会", "参加校"]
}

PUT /tournaments/{id}/report-settings

Request:
{
  "senderOrganization": "県立浦和高校サッカー部",
  "senderName": "森川大地",
  "senderContact": "090-XXXX-XXXX",
  "recipients": ["埼玉県サッカー協会", "参加校"]
}
```

---

## 7. 画面仕様（報告書出力画面）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  報告書出力                                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  【日別試合結果】                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  日付選択:  [3/29 ▼]                                                │   │
│  │                                                                      │   │
│  │  会場選択:  ☑ 浦和南高G                                             │   │
│  │            ☑ 市立浦和高G                                            │   │
│  │            ☑ 浦和学院高G                                            │   │
│  │            ☑ 武南高G                                                │   │
│  │                                                                      │   │
│  │                                               [プレビュー] [PDF出力] │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  【最終結果】                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  出力内容:  ☑ 順位決定戦結果（3決・決勝・準決勝）                   │   │
│  │            ☑ 研修試合結果                                           │   │
│  │            ☑ 最終順位（1〜4位）                                     │   │
│  │            ☑ 優秀選手                                               │   │
│  │                                                                      │   │
│  │  ⚠️ 未入力: 決勝戦の結果、優秀選手3名                               │   │
│  │                                                                      │   │
│  │                                               [プレビュー] [PDF出力] │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  【報告書設定】                                                    [編集]   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  送付者: 県立浦和高校サッカー部 森川大地                             │   │
│  │  連絡先: 090-XXXX-XXXX                                              │   │
│  │  宛先:   埼玉県サッカー協会、参加校                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. 実装チェックリスト

### PDF生成
- [ ] ReportLab環境構築
- [ ] 日本語フォント（NotoSansJP）設定
- [ ] 日別試合結果テンプレート作成
- [ ] 最終結果テンプレート作成
- [ ] 得点経過の動的レイアウト
- [ ] PK戦表示対応
- [ ] 複数ページ対応

### API
- [ ] 日別報告書生成エンドポイント
- [ ] 最終結果報告書生成エンドポイント
- [ ] 報告書設定CRUD

### 画面
- [ ] 日別報告書出力UI
- [ ] 最終結果報告書出力UI
- [ ] 報告書設定編集モーダル
- [ ] プレビュー機能
- [ ] 未入力警告表示

### データ
- [ ] 試合結果からの自動集計
- [ ] 得点経過データの取得
- [ ] 優秀選手データの取得

---

## 9. サンプルPDF出力（擬似コード）

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_daily_report(tournament_id: int, date: str, venue_ids: list):
    """日別試合結果PDFを生成"""
    
    # データ取得
    matches = get_matches_by_date(tournament_id, date, venue_ids)
    settings = get_report_settings(tournament_id)
    
    # PDF作成
    doc = SimpleDocTemplate(
        f"report_{date}.pdf",
        pagesize=A4,
        topMargin=15*mm,
        bottomMargin=15*mm,
        leftMargin=15*mm,
        rightMargin=15*mm
    )
    
    elements = []
    
    # ヘッダー
    elements.append(create_header(settings, date))
    elements.append(Spacer(1, 10*mm))
    
    # 会場別ブロック
    for venue in group_by_venue(matches):
        elements.append(create_venue_header(venue.name))
        elements.append(create_match_table(venue.matches))
        elements.append(Spacer(1, 5*mm))
    
    doc.build(elements)
    
    return f"report_{date}.pdf"


def create_match_table(matches):
    """試合結果テーブルを作成"""
    
    data = []
    
    # ヘッダー行
    data.append(['', '', '試合結果', '', '', '', '', '', '得点経過', ''])
    data.append(['', '', '', '', '', '', '', '', '時間', 'チーム'])
    
    # 試合データ
    for i, match in enumerate(matches):
        # 得点経過を取得
        goals = get_goals_for_match(match.id)
        goal_times = '\n'.join([str(g.minute) for g in goals])
        goal_teams = '\n'.join([g.team for g in goals])
        
        # 試合ブロック（4行）
        data.append([
            '', '', '', '', '', '', '', '',
            goal_times, goal_teams
        ])
        data.append([
            f'第', match.home_team, '', '', 'VS', match.away_team, '', '',
            '', ''
        ])
        data.append([
            f'{i+1}', match.home_score_h1, '', '前半', '', match.away_score_h1, '', '',
            '', ''
        ])
        data.append([
            '試合', match.home_score_h2, '', '後半', '', match.away_score_h2, '', '',
            '', ''
        ])
    
    # テーブルスタイル
    style = TableStyle([
        ('FONT', (0, 0), (-1, -1), 'NotoSansJP', 11),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        # セル結合はここで指定
    ])
    
    table = Table(data)
    table.setStyle(style)
    
    return table
```
