import { useState, useEffect } from 'react';
import { standingApi, type GroupStandings } from '@/features/standings';
import LoadingSpinner from '../../components/common/LoadingSpinner';

type StandingRow = GroupStandings['standings'][number];

export default function PublicStandings() {
    const [standings, setStandings] = useState<Record<string, StandingRow[]>>({});
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('A');

    useEffect(() => {
        const fetchStandings = async () => {
            try {
                setLoading(true);
                // Hardcoded tournament ID
                const data = await standingApi.getStandingsByGroup(1);

                // Transform Array to Map for easier access by tab
                const standingsMap: Record<string, StandingRow[]> = {};
                if (Array.isArray(data)) {
                    data.forEach((groupData) => {
                        if (groupData.groupId) {
                            standingsMap[groupData.groupId] = groupData.standings;
                        }
                    });
                }
                setStandings(standingsMap);
            } catch (error) {
                console.error("Failed to load standings", error);
            } finally {
                setLoading(false);
            }
        };
        fetchStandings();
    }, []);

    if (loading) return <div className="flex justify-center py-10"><LoadingSpinner /></div>;

    const currentGroupStandings = standings[activeTab] || [];

    return (
        <div className="space-y-4 pb-20">
            <h1 className="text-xl font-bold text-gray-800 px-1">予選リーグ順位表</h1>

            {/* Tabs */}
            <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
                {['A', 'B', 'C', 'D'].map(group => (
                    <button
                        key={group}
                        onClick={() => setActiveTab(group)}
                        className={`flex-1 py-1.5 text-sm font-bold rounded-md transition-all ${activeTab === group
                            ? 'bg-white text-red-600 shadow-sm'
                            : 'text-gray-500 hover:bg-gray-200'
                            }`}
                    >
                        Group {group}
                    </button>
                ))}
            </div>

            {/* Table */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50 text-gray-500 border-b border-gray-100">
                        <tr>
                            <th className="py-3 pl-3 text-left w-10">#</th>
                            <th className="py-3 text-left">Team</th>
                            <th className="py-3 text-center w-8">Pt</th>
                            <th className="py-3 text-center w-8">GD</th>
                            <th className="py-3 text-center w-8 text-gray-400 font-normal text-xs">Pld</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                        {currentGroupStandings.length === 0 ? (
                            <tr><td colSpan={5} className="text-center py-8 text-gray-400">データなし</td></tr>
                        ) : (
                            currentGroupStandings.map((row, index) => (
                                <tr key={index} className="hover:bg-red-50 transition-colors">
                                    <td className="py-3 pl-3 font-bold text-gray-400">
                                        {index + 1}
                                    </td>
                                    <td className="py-3 font-bold text-gray-800">
                                        {row.team?.name ?? `Team ${row.teamId}`}
                                    </td>
                                    <td className="py-3 text-center font-black text-gray-900 bg-gray-50">
                                        {row.points}
                                    </td>
                                    <td className="py-3 text-center font-medium text-gray-600">
                                        {row.goalDifference > 0 ? `+${row.goalDifference}` : row.goalDifference}
                                    </td>
                                    <td className="py-3 text-center text-gray-400 text-xs">
                                        {row.played}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            <p className="text-[10px] text-gray-400 px-2">
                ※ 順位決定ルール: 1.勝点 2.得失点 3.総得点 4.直接対決
            </p>
        </div>
    );
}
