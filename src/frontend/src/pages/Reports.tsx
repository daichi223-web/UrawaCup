import { useState } from 'react';
import { reportApi } from '@/features/reports';
import { httpClient } from '@/core/http';
import { FileText, Download, Trophy, Calendar, Table, Eye, X, Clock } from 'lucide-react'
import toast from 'react-hot-toast';

interface MatchPreview {
  id: number;
  match_time: string;
  home_team: { name: string; short_name?: string };
  away_team: { name: string; short_name?: string };
  home_score?: number;
  away_score?: number;
  status: string;
}

interface ReportPreviewData {
  date: string;
  venue: { id: number; name: string } | null;
  matches: MatchPreview[];
}

/**
 * 報告書出力画面
 * PDF/Excel形式での報告書生成・送信
 */
function Reports() {
  const [date, setDate] = useState('');
  const [venueId, setVenueId] = useState('');
  const [format, setFormat] = useState<'pdf' | 'excel'>('pdf');
  const [loading, setLoading] = useState(false);
  const [specialReportLoading, setSpecialReportLoading] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [previewData, setPreviewData] = useState<ReportPreviewData | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  // TODO: Context
  const tournamentId = 1;

  // 日付のマッピング（実際の大会日程に合わせて設定）
  const dateMap: Record<string, string> = {
    'day1': '2027-03-20',
    'day2': '2027-03-21',
    'day3': '2027-03-22',
  };

  const handleDownload = async () => {
    if (!date) {
      toast.error('日付を選択してください');
      return;
    }

    try {
      setLoading(true);
      const targetDate = dateMap[date];
      const venue = venueId ? parseInt(venueId) : undefined;

      let blob: Blob;
      let filename = `report_${targetDate}`;
      if (venue) filename += `_venue${venue}`;

      if (format === 'pdf') {
        blob = await reportApi.downloadPdf({
          tournamentId,
          date: targetDate,
          venueId: venue,
          format: 'pdf'
        });
        filename += '.pdf';
      } else {
        blob = await reportApi.downloadExcel({
          tournamentId,
          date: targetDate,
          venueId: venue,
          format: 'excel'
        });
        filename += '.xlsx';
      }

      // ダウンロード処理
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success('ダウンロードを開始しました');
    } catch (err: any) {
      console.error(err);
      toast.error('報告書の生成に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  // プレビューデータを取得
  const handlePreview = async () => {
    if (!date) {
      toast.error('日付を選択してください');
      return;
    }

    try {
      setPreviewLoading(true);
      const targetDate = dateMap[date];
      const venue = venueId ? parseInt(venueId) : undefined;

      const response = await httpClient.get<ReportPreviewData>('/reports/data', {
        params: {
          tournament_id: tournamentId,
          target_date: targetDate,
          venue_id: venue,
        }
      });

      setPreviewData(response.data);
      setShowPreview(true);
    } catch (err: unknown) {
      console.error(err);
      toast.error('プレビューデータの取得に失敗しました');
    } finally {
      setPreviewLoading(false);
    }
  };

  // 特別レポートのダウンロード
  const handleDownloadSpecialReport = async (type: 'groupStandings' | 'finalDaySchedule' | 'finalResult') => {
    try {
      setSpecialReportLoading(type);
      let blob: Blob;
      let filename: string;

      switch (type) {
        case 'groupStandings':
          blob = await reportApi.downloadGroupStandings({ tournamentId });
          filename = `group_standings_${tournamentId}.pdf`;
          break;
        case 'finalDaySchedule':
          if (!date) {
            toast.error('日付を選択してください');
            return;
          }
          blob = await reportApi.downloadFinalDaySchedule({
            tournamentId,
            date: dateMap[date]
          });
          filename = `final_day_schedule_${dateMap[date]}.pdf`;
          break;
        case 'finalResult':
          blob = await reportApi.downloadFinalResult(tournamentId);
          filename = `final_result_${tournamentId}.pdf`;
          break;
      }

      // ダウンロード処理
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success('ダウンロードを開始しました');
    } catch (err: any) {
      console.error(err);
      toast.error('レポートの生成に失敗しました');
    } finally {
      setSpecialReportLoading(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* ページヘッダー */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">報告書出力</h1>
        <p className="text-gray-600 mt-1">
          試合結果報告書をPDF/Excel形式で出力します
        </p>
      </div>

      {/* 出力条件設定 */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold">出力条件</h3>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="form-label">日付</label>
              <select
                className="form-input"
                value={date}
                onChange={(e) => setDate(e.target.value)}
              >
                <option value="">日付を選択</option>
                <option value="day1">Day1 (3/20)</option>
                <option value="day2">Day2 (3/21)</option>
                <option value="day3">Day3 (3/22)</option>
              </select>
            </div>
            <div>
              <label className="form-label">会場</label>
              <select
                className="form-input"
                value={venueId}
                onChange={(e) => setVenueId(e.target.value)}
              >
                <option value="">全会場</option>
                <option value="1">浦和南高G</option>
                <option value="2">市立浦和高G</option>
                <option value="3">浦和学院G</option>
                <option value="4">武南高G</option>
              </select>
            </div>
            <div>
              <label className="form-label">出力形式</label>
              <select
                className="form-input"
                value={format}
                onChange={(e) => setFormat(e.target.value as 'pdf' | 'excel')}
              >
                <option value="pdf">PDF</option>
                <option value="excel">Excel</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* プレビューエリア（アクションへ変更） */}
      <div className="card">
        <div className="card-header flex items-center justify-between">
          <h3 className="text-lg font-semibold">出力アクション</h3>
        </div>
        <div className="card-body">
          <div className="bg-gray-50 rounded-lg p-8 flex flex-col items-center justify-center text-center">
            <FileText className={`w-16 h-16 mb-4 ${date ? 'text-primary-500' : 'text-gray-300'}`} />

            {!date ? (
              <p className="text-gray-500">
                上のフォームから出力条件（特に日付）を選択してください
              </p>
            ) : (
              <div className="space-y-4">
                <p className="font-medium text-gray-900">
                  {dateMap[date]} の {venueId ? '指定会場' : '全会場'} の報告書を出力します
                </p>
                <div className="flex justify-center gap-4">
                  <button
                    onClick={handlePreview}
                    disabled={previewLoading}
                    className="btn btn-secondary flex items-center gap-2 px-6 py-3"
                  >
                    {previewLoading ? (
                      <>
                        <div className="animate-spin h-5 w-5 border-2 border-current border-t-transparent rounded-full" />
                        読込中...
                      </>
                    ) : (
                      <>
                        <Eye className="w-5 h-5" />
                        プレビュー
                      </>
                    )}
                  </button>
                  <button
                    onClick={handleDownload}
                    disabled={loading}
                    className="btn btn-primary flex items-center gap-2 px-6 py-3"
                  >
                    {loading ? (
                      <>
                        <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" />
                        生成中...
                      </>
                    ) : (
                      <>
                        <Download className="w-5 h-5" />
                        {format === 'pdf' ? 'PDF' : 'Excel'}をダウンロード
                      </>
                    )}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  ※ PDF生成には時間がかかる場合があります
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 特別レポート出力 */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold">特別レポート出力</h3>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* グループ順位表 */}
            <div className="bg-gray-50 rounded-lg p-6 flex flex-col items-center text-center">
              <Table className="w-10 h-10 mb-3 text-blue-500" />
              <h4 className="font-medium mb-2">グループ順位表</h4>
              <p className="text-sm text-gray-500 mb-4">予選リーグの順位表をPDFで出力</p>
              <button
                onClick={() => handleDownloadSpecialReport('groupStandings')}
                disabled={specialReportLoading === 'groupStandings'}
                className="btn btn-secondary flex items-center gap-2"
              >
                {specialReportLoading === 'groupStandings' ? (
                  <div className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
                ) : (
                  <Download className="w-4 h-4" />
                )}
                PDFダウンロード
              </button>
            </div>

            {/* 最終日組み合わせ表 */}
            <div className="bg-gray-50 rounded-lg p-6 flex flex-col items-center text-center">
              <Calendar className="w-10 h-10 mb-3 text-green-500" />
              <h4 className="font-medium mb-2">最終日組み合わせ表</h4>
              <p className="text-sm text-gray-500 mb-4">順位リーグ・決勝トーナメントの日程</p>
              <button
                onClick={() => handleDownloadSpecialReport('finalDaySchedule')}
                disabled={!date || specialReportLoading === 'finalDaySchedule'}
                className="btn btn-secondary flex items-center gap-2"
              >
                {specialReportLoading === 'finalDaySchedule' ? (
                  <div className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
                ) : (
                  <Download className="w-4 h-4" />
                )}
                PDFダウンロード
              </button>
              {!date && <p className="text-xs text-orange-500 mt-2">※日付を選択してください</p>}
            </div>

            {/* 最終結果報告書 */}
            <div className="bg-gray-50 rounded-lg p-6 flex flex-col items-center text-center">
              <Trophy className="w-10 h-10 mb-3 text-yellow-500" />
              <h4 className="font-medium mb-2">最終結果報告書</h4>
              <p className="text-sm text-gray-500 mb-4">決勝トーナメント結果・最終順位</p>
              <button
                onClick={() => handleDownloadSpecialReport('finalResult')}
                disabled={specialReportLoading === 'finalResult'}
                className="btn btn-secondary flex items-center gap-2"
              >
                {specialReportLoading === 'finalResult' ? (
                  <div className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
                ) : (
                  <Download className="w-4 h-4" />
                )}
                PDFダウンロード
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 送信先設定（モックのまま） */}
      <div className="card opacity-60 pointer-events-none">
        <div className="card-header flex items-center justify-between">
          <h3 className="text-lg font-semibold">送信先 (自動送信予定)</h3>
          <span className="text-xs bg-gray-200 px-2 py-1 rounded">Coming Soon</span>
        </div>
        <div className="card-body">
          <ul className="space-y-2 text-sm">
            <li className="flex items-center justify-between py-2 border-b">
              <span>埼玉新聞</span>
              <span className="text-gray-500">sports@saitama-np.co.jp</span>
            </li>
            <li className="flex items-center justify-between py-2 border-b">
              <span>テレビ埼玉</span>
              <span className="text-gray-500">sports@teletama.jp</span>
            </li>
          </ul>
        </div>
      </div>

      {/* プレビューモーダル */}
      {showPreview && previewData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold">
                報告書プレビュー - {previewData.date}
                {previewData.venue && ` (${previewData.venue.name})`}
              </h3>
              <button
                onClick={() => setShowPreview(false)}
                className="p-2 hover:bg-gray-100 rounded-full"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto max-h-[calc(90vh-120px)]">
              {previewData.matches.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>この条件に該当する試合がありません</p>
                  <p className="text-sm mt-2">日付や会場を確認してください</p>
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-sm text-gray-600 mb-4">
                    {previewData.matches.length}試合が報告書に含まれます
                  </p>
                  {previewData.matches.map((match) => (
                    <div
                      key={match.id}
                      className="border rounded-lg p-4 hover:bg-gray-50"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <span className="text-sm text-gray-500 flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            {match.match_time?.slice(0, 5) || '--:--'}
                          </span>
                          <span className="font-medium">
                            {match.home_team?.short_name || match.home_team?.name || '未定'}
                          </span>
                          <span className="px-3 py-1 bg-gray-100 rounded font-bold">
                            {match.status === 'completed'
                              ? `${match.home_score ?? 0} - ${match.away_score ?? 0}`
                              : 'vs'}
                          </span>
                          <span className="font-medium">
                            {match.away_team?.short_name || match.away_team?.name || '未定'}
                          </span>
                        </div>
                        <span className={`text-xs px-2 py-1 rounded ${
                          match.status === 'completed'
                            ? 'bg-green-100 text-green-800'
                            : match.status === 'in_progress'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-gray-100 text-gray-600'
                        }`}>
                          {match.status === 'completed' ? '終了'
                            : match.status === 'in_progress' ? '試合中'
                            : '予定'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="flex justify-end gap-3 p-4 border-t">
              <button
                onClick={() => setShowPreview(false)}
                className="btn btn-secondary"
              >
                閉じる
              </button>
              <button
                onClick={() => {
                  setShowPreview(false);
                  handleDownload();
                }}
                className="btn btn-primary flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                ダウンロード
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Reports

