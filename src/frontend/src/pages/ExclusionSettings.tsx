/**
 * 対戦除外設定画面
 * 変則リーグの日程生成用「対戦しないペア」を設定する
 */

import { useState, useEffect } from 'react';
import { exclusionApi } from '@/features/exclusions';
import { GroupExclusions, Team } from '@shared/types';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { Trash2, Info } from 'lucide-react';
import toast from 'react-hot-toast';

function ExclusionSettings() {
    const [groupExclusions, setGroupExclusions] = useState<GroupExclusions[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('A');

    // TODO: Context
    const tournamentId = 1;

    const fetchExclusions = async () => {
        try {
            setLoading(true);
            const data = await exclusionApi.getExclusionsByGroup(tournamentId);
            setGroupExclusions(data);
        } catch (err) {
            console.error(err);
            toast.error('除外設定の取得に失敗しました');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchExclusions();
    }, []);

    const handleToggleExclusion = async (group: GroupExclusions, team1: Team, team2: Team) => {
        // 既に設定されているか確認
        const existing = group.exclusions.find(
            ex =>
                (ex.team1Id === team1.id && ex.team2Id === team2.id) ||
                (ex.team1Id === team2.id && ex.team2Id === team1.id)
        );

        try {
            if (existing) {
                // 削除
                await exclusionApi.deleteExclusion(existing.id);
                toast.success('除外設定を解除しました');
            } else {
                // 追加
                // チェック: 各チーム2つまで
                const count1 = group.teamExclusionCount[team1.id] || 0;
                const count2 = group.teamExclusionCount[team2.id] || 0;

                if (count1 >= 2) {
                    toast.error(`${team1.name} は既に2チーム除外されています`);
                    return;
                }
                if (count2 >= 2) {
                    toast.error(`${team2.name} は既に2チーム除外されています`);
                    return;
                }

                await exclusionApi.createExclusion({
                    tournamentId,
                    groupId: group.groupId,
                    team1Id: team1.id,
                    team2Id: team2.id,
                    reason: 'manual'
                });
                toast.success('除外設定を追加しました');
            }
            // 再取得して画面更新
            fetchExclusions();
        } catch (err: any) {
            console.error(err);
            toast.error(err.response?.data?.detail || '操作に失敗しました');
        }
    };

    if (loading) return <LoadingSpinner />;

    const activeGroupData = groupExclusions.find(g => g.groupId === activeTab);
    // Team list needs to be extracted from somewhere. 
    // Currently GroupExclusions response doesn't include raw Team objects for the matrix header, 
    // only IDs in exclusions.
    // Wait, GroupWithDetails in generic types has teams.
    // The API `get_exclusions_by_group` return `GroupExclusions` which contains `team_exclusion_count`.
    // It does NOT contain the list of teams.
    // I need to fetch teams for the group to verify labels.
    // Or update the backend to Include teams in GroupExclusions.
    // Checking backend/schemas/exclusion.py might clarify what GroupExclusions contains.
    // If backend doesn't provide teams, I need to fetch teams separately.
    // For now, I'll assume I need to fetch teams here or use a helper. 
    // Let's implement team fetching inside this component for safety.

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">対戦除外設定</h1>
                <p className="text-gray-600 mt-1">
                    変則リーグで対戦しない組み合わせを設定します（各チーム2試合除外）
                </p>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex gap-3 text-blue-800 text-sm">
                <Info className="w-5 h-5 flex-shrink-0" />
                <div>
                    <p className="font-bold">設定ルール</p>
                    <ul className="list-disc list-inside mt-1 space-y-1">
                        <li>6チーム変則リーグでは、総当たり（5試合）から2試合を減らして3試合を行います。</li>
                        <li>「対戦しない」相手を各チーム2つ選んでください。</li>
                        <li>地元チーム同士の対戦を優先的に除外することが推奨されます。</li>
                    </ul>
                </div>
            </div>

            {/* タブ切り替え */}
            <div className="border-b border-gray-200">
                <nav className="flex -mb-px space-x-8">
                    {['A', 'B', 'C', 'D'].map((group) => (
                        <button
                            key={group}
                            onClick={() => setActiveTab(group)}
                            className={`
                whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
                ${activeTab === group
                                    ? 'border-primary-500 text-primary-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
              `}
                        >
                            {group}グループ
                        </button>
                    ))}
                </nav>
            </div>

            {/* マトリクス表示 */}
            {activeGroupData ? (
                <ExclusionMatrix
                    groupData={activeGroupData}
                    tournamentId={tournamentId}
                    onToggle={handleToggleExclusion}
                />
            ) : (
                <div className="text-center py-8 text-gray-500">
                    データがありません
                </div>
            )}
        </div>
    );
}

// マトリクスコンポーネント（チーム取得ロジック含む）
import api from '@/core/http'; // Use core http client to fetch teams

function ExclusionMatrix({ groupData, tournamentId, onToggle }: {
    groupData: GroupExclusions,
    tournamentId: number,
    onToggle: (g: GroupExclusions, t1: Team, t2: Team) => void
}) {
    const [teams, setTeams] = useState<Team[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchTeams = async () => {
            const res = await api.get<{ teams: Team[]; total: number }>(`/teams/?tournament_id=${tournamentId}&group_id=${groupData.groupId}`);
            setTeams(res.data.teams);
            setLoading(false);
        };
        fetchTeams();
    }, [groupData.groupId, tournamentId]);

    if (loading) return <div className="text-center py-4">読み込み中...</div>;
    if (teams.length === 0) return <div className="text-center py-4">チームが登録されていません</div>;

    return (
        <div className="card overflow-hidden">
            <div className="p-4 bg-gray-50 border-b border-gray-100 flex justify-between items-center">
                <h3 className="font-bold text-gray-700">{groupData.groupId}グループ 対戦除外マトリクス</h3>
                <div className={`text-sm px-3 py-1 rounded-full ${groupData.isComplete ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                    {groupData.isComplete ? '設定完了' : '設定未完了'}
                </div>
            </div>
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32 border-r">
                                チーム
                            </th>
                            {teams.map(team => (
                                <th key={team.id} className="px-2 py-3 text-center text-xs font-medium text-gray-500 tracking-wider w-24">
                                    <div className="writing-mode-vertical-rl transform rotate-180 mx-auto h-24">
                                        {team.name}
                                    </div>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {teams.map((teamRow, i) => (
                            <tr key={teamRow.id}>
                                <td className="px-4 py-3 text-sm font-medium text-gray-900 border-r bg-gray-50">
                                    <div className="flex items-center justify-between">
                                        <span>{teamRow.name}</span>
                                        <span className={`text-xs px-2 py-0.5 rounded ${(groupData.teamExclusionCount[teamRow.id] || 0) === 2
                                            ? 'bg-green-100 text-green-800'
                                            : 'bg-gray-100 text-gray-500'
                                            }`}>
                                            {groupData.teamExclusionCount[teamRow.id] || 0}/2
                                        </span>
                                    </div>
                                </td>
                                {teams.map((teamCol, j) => {
                                    if (i >= j) return <td key={teamCol.id} className="bg-gray-100 border-b border-white"></td>; // 下半分はグレーアウト

                                    const isExcluded = groupData.exclusions.some(
                                        ex =>
                                            (ex.team1Id === teamRow.id && ex.team2Id === teamCol.id) ||
                                            (ex.team1Id === teamCol.id && ex.team2Id === teamRow.id)
                                    );

                                    return (
                                        <td key={teamCol.id} className="px-2 py-3 text-center border-l border-gray-100 hover:bg-gray-50 cursor-pointer"
                                            onClick={() => onToggle(groupData, teamRow, teamCol)}>
                                            <div className={`w-6 h-6 mx-auto rounded border flex items-center justify-center transition-colors ${isExcluded
                                                ? 'bg-red-500 border-red-600 text-white'
                                                : 'bg-white border-gray-300 text-transparent hover:border-gray-400'
                                                }`}>
                                                {isExcluded && <Trash2 size={14} />}
                                            </div>
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default ExclusionSettings;
