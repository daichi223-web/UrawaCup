/**
 * 試合結果承認画面
 * 管理者が試合結果を確認・承認・却下する
 */

import { useState, useEffect } from 'react';
import { matchApi } from '@/features/matches';
import { MatchWithDetails } from '@shared/types';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { CheckCircle, XCircle, AlertTriangle } from 'lucide-react'; import toast from 'react-hot-toast';

function MatchApproval() {
    const [matches, setMatches] = useState<MatchWithDetails[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // 却下モーダル用
    const [rejectingId, setRejectingId] = useState<number | null>(null);
    const [rejectionReason, setRejectionReason] = useState('');

    const fetchPendingMatches = async () => {
        try {
            setLoading(true);
            setError(null);
            // approval_status='pending' でフィルタリング
            // API側がStringEnumを受け取るか確認が必要だが、通常は文字列でOK
            const data = await matchApi.getMatches({ approval_status: 'pending' });
            setMatches(data.matches);
        } catch (err: any) {
            console.error(err);
            setError('承認待ちデータの取得に失敗しました');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPendingMatches();
    }, []);

    const handleApprove = async (id: number) => {
        if (!window.confirm('この試合結果を承認しますか？')) return;

        try {
            await matchApi.approveMatch(id);
            toast.success('承認しました');
            // リストから削除
            setMatches(prev => prev.filter(m => m.id !== id));
        } catch (err: any) {
            toast.error('承認に失敗しました');
            console.error(err);
        }
    };

    const handleReject = async () => {
        if (!rejectingId || !rejectionReason.trim()) return;

        try {
            await matchApi.rejectMatch(rejectingId, rejectionReason);
            toast.error('却下しました'); // 赤色のトースト
            setMatches(prev => prev.filter(m => m.id !== rejectingId));
            setRejectingId(null);
            setRejectionReason('');
        } catch (err: any) {
            toast.error('却下に失敗しました');
            console.error(err);
        }
    };

    if (loading) return <LoadingSpinner />;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">試合結果承認</h1>
                <p className="text-gray-600 mt-1">
                    会場担当者から送信された試合結果を確認します
                </p>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5" />
                    {error}
                </div>
            )}

            {matches.length === 0 && !error ? (
                <div className="text-center py-12 bg-gray-50 rounded-lg">
                    <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900">承認待ちの試合はありません</h3>
                    <p className="text-gray-500 mt-1">現在すべての結果が処理されています</p>
                </div>
            ) : (
                <div className="grid gap-6">
                    {matches.map((match) => (
                        <div key={match.id} className="card overflow-hidden">
                            <div className="card-header bg-yellow-50 border-b border-yellow-100 flex justify-between items-center">
                                <div className="text-sm font-medium text-yellow-800 flex items-center gap-2">
                                    <span className="w-2 h-2 rounded-full bg-yellow-500" />
                                    承認待ち
                                </div>
                                <div className="text-sm text-gray-500">
                                    {match.match_order}試合目 ({match.match_time}) @ {match.venue?.name}
                                </div>
                            </div>

                            <div className="p-6">
                                {/* スコア表示 */}
                                <div className="flex items-center justify-center gap-8 mb-6">
                                    <div className="text-right flex-1">
                                        <div className="text-xl font-bold text-gray-900">{match.home_team?.name}</div>
                                        <div className="text-sm text-gray-500">{match.home_team?.short_name}</div>
                                    </div>

                                    <div className="flex flex-col items-center">
                                        <div className="text-4xl font-bold text-gray-900 bg-gray-100 px-6 py-2 rounded-lg">
                                            {match.home_score_total} - {match.away_score_total}
                                        </div>
                                        {match.has_penalty_shootout && (
                                            <div className="mt-2 text-sm text-gray-600">
                                                PK: {match.home_pk} - {match.away_pk}
                                            </div>
                                        )}
                                    </div>

                                    <div className="text-left flex-1">
                                        <div className="text-xl font-bold text-gray-900">{match.away_team?.name}</div>
                                        <div className="text-sm text-gray-500">{match.away_team?.short_name}</div>
                                    </div>
                                </div>

                                {/* 得点者・警告（簡易表示 - 詳細が必要ならここに追加） */}
                                {/* 
                  TODO: View Goal Scorers here if needed. 
                  Currently focusing on high-level score verification. 
                */}

                                {/* アクションボタン */}
                                <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                                    <button
                                        onClick={() => setRejectingId(match.id)}
                                        className="btn btn-secondary text-red-600 hover:bg-red-50 hover:border-red-200"
                                    >
                                        <XCircle className="w-4 h-4 mr-2" />
                                        却下
                                    </button>
                                    <button
                                        onClick={() => handleApprove(match.id)}
                                        className="btn btn-primary bg-green-600 hover:bg-green-700 border-green-600 text-white"
                                    >
                                        <CheckCircle className="w-4 h-4 mr-2" />
                                        承認
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* 却下モーダル */}
            {rejectingId && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">却下理由を入力</h3>
                        <p className="text-sm text-gray-600 mb-4">
                            会場担当者に修正指示として送信されます。
                        </p>
                        <textarea
                            className="form-textarea w-full h-32 mb-4"
                            placeholder="例: アウェイチームの得点者が間違っています。"
                            value={rejectionReason}
                            onChange={(e) => setRejectionReason(e.target.value)}
                            autoFocus
                        />
                        <div className="flex justify-end gap-2">
                            <button
                                onClick={() => {
                                    setRejectingId(null);
                                    setRejectionReason('');
                                }}
                                className="btn btn-secondary"
                            >
                                キャンセル
                            </button>
                            <button
                                onClick={handleReject}
                                disabled={!rejectionReason.trim()}
                                className="btn btn-primary bg-red-600 hover:bg-red-700 border-red-600"
                            >
                                確定して却下
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default MatchApproval;
