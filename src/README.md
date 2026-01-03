# 浦和カップ トーナメント管理システム

さいたま市招待高校サッカーフェスティバル浦和カップの運営管理システム

## プロジェクト構成

```
src/
├── backend/          # バックエンドAPI (FastAPI)
│   ├── models/       # SQLAlchemyモデル
│   ├── routes/       # APIルート
│   ├── services/     # ビジネスロジック
│   ├── schemas/      # Pydanticスキーマ
│   └── utils/        # ユーティリティ
├── frontend/         # フロントエンド (React + Vite)
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       └── utils/
└── shared/           # 共有型定義
    └── types/
```

## 技術スタック

### バックエンド
- Python 3.11+
- FastAPI
- SQLAlchemy (SQLite)
- Pydantic

### フロントエンド
- React 18
- TypeScript
- Vite
- TailwindCSS
- React Query (TanStack Query)
- React Router

## セットアップ

### バックエンド

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### フロントエンド

```bash
cd frontend
npm install
```

## 開発サーバー起動

### バックエンド

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### フロントエンド

```bash
cd frontend
npm run dev
```

## API ドキュメント

バックエンド起動後、以下のURLでAPIドキュメントを確認できます：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 主な機能

1. **チーム管理**: 参加チームの登録・編集・グループ分け
2. **日程管理**: 予選リーグ・決勝トーナメントの日程生成
3. **試合結果入力**: スコア・得点者のリアルタイム入力
4. **順位表**: 自動計算による順位表示
5. **報告書出力**: PDF/Excel形式での報告書生成

## ライセンス

Private - さいたま市サッカー協会
