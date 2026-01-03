
import { useState, useEffect } from 'react';
import { matchApi } from '@/features/matches';
import { MatchWithDetails } from '@shared/types';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import { MapPin, Clock } from 'lucide-react';

export default function PublicMatchList() {
    const [matches, setMatches] = useState<MatchWithDetails[]>([]);
    const [loading, setLoading] = useState(true);

    // Hardcoded for now, same as other pages
    const tournamentId = 1;

    useEffect(() => {
        const fetchMatches = async () => {
            try {
                setLoading(true);
                const data = await matchApi.getMatches({
                    tournament_id: tournamentId,
                    limit: 100
                });
                // Sort by time descending (newest first)
                const sorted = data.matches.sort((a, b) => {
                    // If completed, put at bottom? No, simpler to just listen strictly to time
                    // actually for "Feed", maybe ongoing first, then finished (desc), then upcoming (asc)
                    // For simplicity: Date ASC, Time ASC
                    const aTime = `${a.matchDate} ${a.matchTime}`;
                    const bTime = `${b.matchDate} ${b.matchTime}`;
                    return new Date(aTime).getTime() - new Date(bTime).getTime();
                });
                setMatches(sorted);
            } catch (error) {
                console.error("Failed to load matches", error);
            } finally {
                setLoading(false);
            }
        };
        fetchMatches();
    }, [tournamentId]);

    if (loading) return <div className="flex justify-center py-10"><LoadingSpinner /></div>;

    // Group by Date for cleaner UI
    const groupedMatches = matches.reduce((acc, match) => {
        const dateStr = match.matchDate || '';
        const date = format(new Date(dateStr), 'M月d日(E)', { locale: ja });
        if (!acc[date]) acc[date] = [];
        acc[date].push(match);
        return acc;
    }, {} as Record<string, MatchWithDetails[]>);

    return (
        <div className="space-y-6 pb-20">
            {Object.entries(groupedMatches).map(([date, dayMatches]) => (
                <div key={date}>
                    <h2 className="text-sm font-bold text-gray-500 mb-3 px-1 sticky top-0 bg-gray-50 py-2 z-10">
                        {date}
                    </h2>
                    <div className="space-y-3">
                        {dayMatches.map(match => (
                            <PublicMatchCard key={match.id} match={match} />
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
}

function PublicMatchCard({ match }: { match: MatchWithDetails }) {
    const isFinished = match.status === 'completed';
    const isLive = match.status === 'in_progress';

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            {/* Header: Time & Venue */}
            <div className="bg-gray-50 px-4 py-2 flex justify-between items-center text-xs text-gray-500">
                <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {match.matchTime || '--:--'}
                    {isLive && <span className="ml-2 text-red-600 font-bold animate-pulse">● LIVE</span>}
                    {isFinished && <span className="ml-2 font-medium text-gray-400">終了</span>}
                </div>
                <div className="flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    {match.venue?.name || '未定'}
                </div>
            </div>

            {/* Score Board */}
            <div className="p-4">
                <div className="flex items-center justify-between">
                    {/* Home Team */}
                    <div className="flex-1 flex flex-col items-center gap-1">
                        <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center font-bold text-gray-700 text-xs">
                            {match.homeTeam?.name.slice(0, 1)}
                        </div>
                        <span className="font-bold text-sm text-center leading-tight">
                            {match.homeTeam?.name}
                        </span>
                    </div>

                    {/* Score */}
                    <div className="px-4 flex flex-col items-center">
                        <div className="text-3xl font-black font-mono tracking-widest text-gray-800">
                            {isFinished || isLive ? (
                                <>
                                    {match.homeScoreTotal ?? '-'} <span className="text-gray-300 text-xl">-</span> {match.awayScoreTotal ?? '-'}
                                </>
                            ) : (
                                <span className="text-xl text-gray-400">vs</span>
                            )}
                        </div>
                        {(match.homePK != null || match.awayPK != null) && (
                            <span className="text-xs text-gray-500 mt-1">
                                (PK: {match.homePK}-{match.awayPK})
                            </span>
                        )}
                    </div>

                    {/* Away Team */}
                    <div className="flex-1 flex flex-col items-center gap-1">
                        <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center font-bold text-gray-700 text-xs">
                            {match.awayTeam?.name.slice(0, 1)}
                        </div>
                        <span className="font-bold text-sm text-center leading-tight">
                            {match.awayTeam?.name}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}
