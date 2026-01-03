/**
 * 決勝トーナメントブラケット表示コンポーネント
 * 準決勝・3位決定戦・決勝を視覚的に表示
 * ドラッグ&ドロップでチーム入れ替え可能
 */
import { useState, useCallback } from 'react'
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import { restrictToWindowEdges } from '@dnd-kit/modifiers'
import { useSortable, SortableContext } from '@dnd-kit/sortable'
import { GripVertical, ArrowLeftRight } from 'lucide-react'
import type { MatchWithDetails } from '@/types'

interface FinalsBracketProps {
  matches: MatchWithDetails[]
  onMatchClick?: (match: MatchWithDetails) => void
  onUpdateBracket?: () => void
  onSwapTeams?: (matchId: number, homeTeamId: number, awayTeamId: number) => void
  isLoading?: boolean
}

// ドラッグ可能なチームスロットのID生成
function getSlotId(matchId: number, position: 'home' | 'away') {
  return `finals-${matchId}-${position}`
}

// スロットIDからmatchIdとpositionを取得
function parseSlotId(slotId: string): { matchId: number; position: 'home' | 'away' } | null {
  if (!slotId.startsWith('finals-')) return null
  const parts = slotId.replace('finals-', '').split('-')
  return {
    matchId: parseInt(parts[0]),
    position: parts[1] as 'home' | 'away',
  }
}

interface DraggableTeamProps {
  match: MatchWithDetails
  position: 'home' | 'away'
  isWinner?: boolean
  disabled?: boolean
}

/**
 * ドラッグ可能なチームスロット
 */
function DraggableTeam({ match, position, isWinner, disabled }: DraggableTeamProps) {
  const slotId = getSlotId(match.id, position)
  const team = position === 'home' ? match.homeTeam : match.awayTeam
  const teamId = position === 'home' ? match.homeTeamId : match.awayTeamId

  const {
    attributes,
    listeners,
    setNodeRef,
    isDragging,
  } = useSortable({ id: slotId, disabled })

  // transformを含めると、ドラッグ中にリストの並び替えアニメーションが発生して
  // 固定レイアウト（トーナメント表）が崩れるため、移動（transform）は無効化する
  const style = {
    // transform: CSS.Transform.toString(transform), 
    // transition,
    opacity: isDragging ? 0.3 : 1, // ドラッグ元は薄くするだけ
  }

  const teamName = team?.shortName || team?.name || `チームID: ${teamId}`

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`
        flex items-center justify-between p-2 rounded
        ${isWinner ? 'bg-green-50 font-bold' : ''}
        ${!disabled ? 'cursor-grab hover:bg-gray-100' : ''}
        ${isDragging ? 'ring-2 ring-primary-500 bg-primary-50' : ''}
      `}
      {...(disabled ? {} : { ...attributes, ...listeners })}
    >
      <div className="flex items-center gap-2 flex-1">
        {!disabled && <GripVertical className="w-4 h-4 text-gray-400" />}
        <span className="truncate">{teamName}</span>
        {isWinner && <span className="ml-2 text-green-600">◎</span>}
      </div>
    </div>
  )
}

interface MatchCardProps {
  match: MatchWithDetails | undefined
  title: string
  onClick?: () => void
  onSwapTeams?: (matchId: number, homeTeamId: number, awayTeamId: number) => void
  className?: string
  draggable?: boolean
}

/**
 * 試合カードコンポーネント
 */
function MatchCard({ match, title, onClick, onSwapTeams, className = '', draggable = false }: MatchCardProps) {
  if (!match) {
    return (
      <div className={`bg-gray-100 rounded-lg p-4 ${className}`}>
        <div className="text-sm text-gray-500 mb-2">{title}</div>
        <div className="text-center text-gray-400 py-4">未設定</div>
      </div>
    )
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'in_progress':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed':
        return '終了'
      case 'in_progress':
        return '試合中'
      case 'scheduled':
        return '予定'
      default:
        return status
    }
  }

  const isCompleted = match.status === 'completed'
  const homeWon = isCompleted && match.result === 'home_win'
  const awayWon = isCompleted && match.result === 'away_win'
  const canDrag = draggable && !isCompleted

  const handleInternalSwap = () => {
    if (onSwapTeams && match.homeTeamId && match.awayTeamId && !isCompleted) {
      onSwapTeams(match.id, match.awayTeamId, match.homeTeamId)
    }
  }

  // SortableContextは親コンポーネント(FinalsBracket)で一括管理しているため、
  // ここでのネストしたSortableContextは削除し、単にDraggableTeamをレンダリングする

  return (
    <div
      className={`bg-white rounded-lg shadow border-2 border-gray-200 p-4 cursor-pointer hover:border-primary-300 transition-colors ${className}`}
      onClick={onClick}
    >
      <div className="flex justify-between items-center mb-3">
        <div className="text-sm font-medium text-gray-700">{title}</div>
        <div className="flex items-center gap-2">
          {canDrag && onSwapTeams && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleInternalSwap()
              }}
              className="p-1 rounded hover:bg-gray-100 text-gray-500"
              title="ホーム/アウェイ入れ替え"
            >
              <ArrowLeftRight className="w-4 h-4" />
            </button>
          )}
          <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(match.status)}`}>
            {getStatusLabel(match.status)}
          </span>
        </div>
      </div>

      <div className="space-y-2">
        {/* ホームチーム */}
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <DraggableTeam
              match={match}
              position="home"
              isWinner={homeWon}
              disabled={!canDrag}
            />
          </div>
          {isCompleted && (
            <div className="text-lg font-bold ml-4">
              {match.homeScoreTotal ?? '-'}
              {match.hasPenaltyShootout && match.homePK !== null && (
                <span className="text-sm text-gray-500 ml-1">({match.homePK})</span>
              )}
            </div>
          )}
        </div>

        {/* アウェイチーム */}
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <DraggableTeam
              match={match}
              position="away"
              isWinner={awayWon}
              disabled={!canDrag}
            />
          </div>
          {isCompleted && (
            <div className="text-lg font-bold ml-4">
              {match.awayScoreTotal ?? '-'}
              {match.hasPenaltyShootout && match.awayPK !== null && (
                <span className="text-sm text-gray-500 ml-1">({match.awayPK})</span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 試合時刻・会場 */}
      <div className="mt-3 text-xs text-gray-500 flex justify-between">
        <span>{match.matchTime?.substring(0, 5) || '--:--'}</span>
        <span>{match.venue?.name || '会場未定'}</span>
      </div>

      {/* PK表記 */}
      {match.hasPenaltyShootout && (
        <div className="mt-2 text-xs text-center text-orange-600 font-medium">
          PK戦
        </div>
      )}

      {/* ドラッグ可能表示 */}
      {canDrag && (
        <div className="mt-2 text-xs text-center text-gray-400">
          チームをドラッグして入れ替え可能
        </div>
      )}
    </div>
  )
}

/**
 * 決勝トーナメントブラケット
 */
export default function FinalsBracket({
  matches,
  onMatchClick,
  onUpdateBracket,
  onSwapTeams,
  isLoading = false,
}: FinalsBracketProps) {
  const [activeId, setActiveId] = useState<string | null>(null)

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  )

  // 試合をステージで分類
  const semifinals = matches.filter((m) => m.stage === 'semifinal').sort((a, b) => a.matchOrder - b.matchOrder)
  const thirdPlace = matches.find((m) => m.stage === 'third_place')
  const final = matches.find((m) => m.stage === 'final')

  const semifinal1 = semifinals[0]
  const semifinal2 = semifinals[1]

  // 準決勝が両方完了しているか
  const bothSemifinalsCompleted =
    semifinal1?.status === 'completed' &&
    semifinal2?.status === 'completed' &&
    semifinal1?.result &&
    semifinal2?.result

  const handleMatchClick = (match: MatchWithDetails | undefined) => {
    if (match) {
      onMatchClick?.(match)
    }
  }

  // ドラッグ開始
  const handleDragStart = useCallback((event: DragStartEvent) => {
    setActiveId(event.active.id as string)
  }, [])

  // ドラッグ終了
  const handleDragEnd = useCallback((event: DragEndEvent) => {
    const { active, over } = event
    setActiveId(null)

    if (!over || active.id === over.id || !onSwapTeams) return

    const activeSlot = parseSlotId(active.id as string)
    const overSlot = parseSlotId(over.id as string)

    if (!activeSlot || !overSlot) return

    // 同じ試合内での入れ替え
    if (activeSlot.matchId === overSlot.matchId) {
      const match = matches.find(m => m.id === activeSlot.matchId)
      if (match && match.homeTeamId && match.awayTeamId && match.status !== 'completed') {
        onSwapTeams(match.id, match.awayTeamId, match.homeTeamId)
      }
      return
    }

    // 異なる試合間でのチーム交換
    const match1 = matches.find(m => m.id === activeSlot.matchId)
    const match2 = matches.find(m => m.id === overSlot.matchId)

    if (match1 && match2 && match1.status !== 'completed' && match2.status !== 'completed') {
      const team1Id = activeSlot.position === 'home' ? match1.homeTeamId : match1.awayTeamId
      const team2Id = overSlot.position === 'home' ? match2.homeTeamId : match2.awayTeamId

      if (team1Id && team2Id) {
        const newMatch1Home = activeSlot.position === 'home' ? team2Id : match1.homeTeamId
        const newMatch1Away = activeSlot.position === 'away' ? team2Id : match1.awayTeamId
        const newMatch2Home = overSlot.position === 'home' ? team1Id : match2.homeTeamId
        const newMatch2Away = overSlot.position === 'away' ? team1Id : match2.awayTeamId

        if (newMatch1Home && newMatch1Away) {
          onSwapTeams(match1.id, newMatch1Home, newMatch1Away)
        }
        if (newMatch2Home && newMatch2Away) {
          onSwapTeams(match2.id, newMatch2Home, newMatch2Away)
        }
      }
    }
  }, [matches, onSwapTeams])

  // ドラッグ中のチーム名を取得
  const getActiveTeamName = () => {
    if (!activeId) return null
    const slot = parseSlotId(activeId)
    if (!slot) return null
    const match = matches.find(m => m.id === slot.matchId)
    if (!match) return null
    const team = slot.position === 'home' ? match.homeTeam : match.awayTeam
    return team?.shortName || team?.name || 'チーム'
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
        <span className="ml-3 text-gray-600">読み込み中...</span>
      </div>
    )
  }

  if (matches.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 text-lg mb-4">
          決勝トーナメントが生成されていません
        </div>
        <p className="text-gray-500 text-sm">
          予選リーグ終了後、「決勝T自動生成」ボタンで組み合わせを生成してください
        </p>
      </div>
    )
  }

  // 全ての未完了試合のソート可能ID
  const allSortableIds = matches
    .filter(m => m.status !== 'completed')
    .flatMap(m => [getSlotId(m.id, 'home'), getSlotId(m.id, 'away')])

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      modifiers={[restrictToWindowEdges]}
    >
      <SortableContext items={allSortableIds}>
        <div className="space-y-6">
          {/* 組み合わせ更新ボタン */}
          {bothSemifinalsCompleted && onUpdateBracket && (
            <div className="flex justify-center">
              <button
                onClick={onUpdateBracket}
                className="btn-primary flex items-center gap-2"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                組み合わせを更新（準決勝結果を反映）
              </button>
            </div>
          )}

          {/* トーナメントブラケット */}
          <div className="relative">
            {/* デスクトップレイアウト */}
            <div className="hidden lg:grid lg:grid-cols-5 lg:gap-6 lg:items-center">
              {/* 準決勝列 */}
              <div className="space-y-8 col-span-1">
                <MatchCard
                  match={semifinal1}
                  title="準決勝1"
                  onClick={() => handleMatchClick(semifinal1)}
                  onSwapTeams={onSwapTeams}
                  draggable={!!onSwapTeams}
                />
                <MatchCard
                  match={semifinal2}
                  title="準決勝2"
                  onClick={() => handleMatchClick(semifinal2)}
                  onSwapTeams={onSwapTeams}
                  draggable={!!onSwapTeams}
                />
              </div>

              {/* 接続線（準決勝→決勝） */}
              <div className="col-span-1 flex flex-col items-center justify-center h-full">
                <div className="w-full border-t-2 border-gray-300"></div>
                <div className="h-24 border-r-2 border-gray-300"></div>
                <div className="w-full border-t-2 border-gray-300"></div>
              </div>

              {/* 決勝・3位決定戦列 */}
              <div className="col-span-2 space-y-4">
                <MatchCard
                  match={final}
                  title="決勝"
                  onClick={() => handleMatchClick(final)}
                  onSwapTeams={onSwapTeams}
                  draggable={!!onSwapTeams}
                  className="border-yellow-400 border-2"
                />
                <MatchCard
                  match={thirdPlace}
                  title="3位決定戦"
                  onClick={() => handleMatchClick(thirdPlace)}
                  onSwapTeams={onSwapTeams}
                  draggable={!!onSwapTeams}
                />
              </div>

              {/* 優勝チーム表示 */}
              <div className="col-span-1 flex flex-col items-center justify-center">
                {final?.status === 'completed' && final.result && (
                  <div className="text-center">
                    <div className="text-yellow-600 mb-2">
                      <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="text-lg font-bold text-gray-900">優勝</div>
                    <div className="text-xl font-bold text-primary-600 mt-1">
                      {final.result === 'home_win'
                        ? final.homeTeam?.name
                        : final.awayTeam?.name}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* モバイルレイアウト */}
            <div className="lg:hidden space-y-4">
              <div className="bg-yellow-50 rounded-lg p-4">
                <div className="text-center text-sm font-medium text-yellow-800 mb-3">
                  決勝
                </div>
                <MatchCard
                  match={final}
                  title="決勝"
                  onClick={() => handleMatchClick(final)}
                  onSwapTeams={onSwapTeams}
                  draggable={!!onSwapTeams}
                  className="border-yellow-400"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <MatchCard
                  match={semifinal1}
                  title="準決勝1"
                  onClick={() => handleMatchClick(semifinal1)}
                  onSwapTeams={onSwapTeams}
                  draggable={!!onSwapTeams}
                />
                <MatchCard
                  match={semifinal2}
                  title="準決勝2"
                  onClick={() => handleMatchClick(semifinal2)}
                  onSwapTeams={onSwapTeams}
                  draggable={!!onSwapTeams}
                />
              </div>

              <MatchCard
                match={thirdPlace}
                title="3位決定戦"
                onClick={() => handleMatchClick(thirdPlace)}
                onSwapTeams={onSwapTeams}
                draggable={!!onSwapTeams}
              />
            </div>
          </div>

          {/* 凡例 */}
          <div className="flex flex-wrap gap-4 justify-center text-sm text-gray-600 mt-6 pt-6 border-t">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-green-100 rounded"></span>
              <span>終了</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-yellow-100 rounded"></span>
              <span>試合中</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-gray-100 rounded"></span>
              <span>予定</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-green-600">◎</span>
              <span>勝者</span>
            </div>
            {onSwapTeams && (
              <div className="flex items-center gap-2">
                <GripVertical className="w-4 h-4 text-gray-400" />
                <span>ドラッグで入れ替え</span>
              </div>
            )}
          </div>
        </div>
      </SortableContext>

      <DragOverlay dropAnimation={null}>
        {activeId && (
          <div className="bg-primary-100 border-2 border-primary-500 rounded p-3 shadow-lg cursor-grabbing">
            <span className="font-medium">{getActiveTeamName()}</span>
          </div>
        )}
      </DragOverlay>
    </DndContext>
  )
}
