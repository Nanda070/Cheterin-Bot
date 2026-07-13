import type { BracketDetail, BracketMatch } from '../api/client'

export type PickHandler = (segment: 'W' | 'L' | 'F', roundIndex: number, matchIndex: number, winner: 'a' | 'b' | 'draw' | null) => void

function MatchCard({
  match,
  onPickA,
  onPickB,
}: {
  match: BracketMatch
  onPickA?: () => void
  onPickB?: () => void
}) {
  const ready = match.slot_a !== null && match.slot_b !== null
  const interactive = Boolean(ready && (onPickA || onPickB))
  const slotClass = (side: 'a' | 'b') =>
    `block w-full rounded-control px-2 py-1 text-left text-sm ${
      match.winner === side ? 'font-semibold text-foreground' : 'text-muted'
    } ${interactive ? 'cursor-pointer hover:bg-surface-hover' : ''}`

  return (
    <div className="w-48 rounded-card border border-border bg-surface p-2">
      {interactive ? (
        <>
          <button type="button" onClick={onPickA} className={slotClass('a')}>
            {match.slot_a ?? '—'}
          </button>
          <button type="button" onClick={onPickB} className={slotClass('b')}>
            {match.slot_b ?? '—'}
          </button>
        </>
      ) : (
        <>
          <p className={slotClass('a')}>{match.slot_a ?? '—'}</p>
          <p className={slotClass('b')}>{match.slot_b ?? '—'}</p>
        </>
      )}
    </div>
  )
}

function EliminationColumns({
  rounds,
  segment,
  finalLabel,
  onPick,
}: {
  rounds: BracketMatch[][]
  segment: 'W' | 'L'
  finalLabel: string
  onPick?: PickHandler
}) {
  return (
    <div className="flex gap-6 overflow-x-auto pb-2">
      {rounds.map((round, roundIndex) => (
        <div key={roundIndex} className="flex flex-col justify-around gap-4">
          <p className="text-xs font-medium uppercase tracking-wide text-muted">
            {roundIndex === rounds.length - 1 ? finalLabel : `Раунд ${roundIndex + 1}`}
          </p>
          {round.map((match, matchIndex) => (
            <MatchCard
              key={matchIndex}
              match={match}
              onPickA={onPick ? () => onPick(segment, roundIndex, matchIndex, 'a') : undefined}
              onPickB={onPick ? () => onPick(segment, roundIndex, matchIndex, 'b') : undefined}
            />
          ))}
        </div>
      ))}
    </div>
  )
}

function StandingsTable({ standings }: { standings: NonNullable<BracketDetail['standings']> }) {
  return (
    <div className="overflow-x-auto rounded-card border border-border bg-surface">
      <table className="w-full min-w-100 border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-muted">
            <th className="px-3 py-2 font-medium">#</th>
            <th className="px-3 py-2 font-medium">Участник</th>
            <th className="px-3 py-2 text-center font-medium">И</th>
            <th className="px-3 py-2 text-center font-medium">В</th>
            <th className="px-3 py-2 text-center font-medium">Н</th>
            <th className="px-3 py-2 text-center font-medium">П</th>
            <th className="px-3 py-2 text-center font-medium">Очки</th>
          </tr>
        </thead>
        <tbody>
          {standings.map((row, i) => (
            <tr key={row.entry} className="border-b border-border last:border-b-0">
              <td className="px-3 py-2 text-muted">{i + 1}</td>
              <td className="px-3 py-2 font-medium text-foreground">{row.entry}</td>
              <td className="px-3 py-2 text-center text-muted">{row.played}</td>
              <td className="px-3 py-2 text-center text-success">{row.wins}</td>
              <td className="px-3 py-2 text-center text-muted">{row.draws}</td>
              <td className="px-3 py-2 text-center text-danger">{row.losses}</td>
              <td className="px-3 py-2 text-center font-semibold text-primary">{row.points}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function RoundRobinView({ bracket, onPick }: { bracket: BracketDetail; onPick?: PickHandler }) {
  const rounds = bracket.rr_rounds ?? []
  return (
    <div className="flex flex-col gap-5">
      {bracket.standings && <StandingsTable standings={bracket.standings} />}
      <div className="grid gap-4 md:grid-cols-2">
        {rounds.map((round, roundIndex) => (
          <div key={roundIndex} className="rounded-card border border-border bg-surface p-3">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">Тур {roundIndex + 1}</p>
            <div className="flex flex-col gap-2">
              {round.map((match, matchIndex) => (
                <div key={matchIndex} className="flex items-center gap-2">
                  <span
                    className={`flex-1 truncate text-right text-sm ${
                      match.winner === 'a' ? 'font-semibold text-foreground' : 'text-muted'
                    }`}
                  >
                    {match.slot_a}
                  </span>
                  {onPick ? (
                    <div className="flex shrink-0 gap-1">
                      {(['a', 'draw', 'b'] as const).map((option) => (
                        <button
                          key={option}
                          type="button"
                          onClick={() => onPick('W', roundIndex, matchIndex, match.winner === option ? null : option)}
                          className={`rounded-control border px-1.5 py-0.5 text-[11px] transition-colors ${
                            match.winner === option
                              ? 'border-primary/60 bg-primary-muted text-foreground'
                              : 'border-border text-muted hover:text-foreground'
                          }`}
                          title={option === 'a' ? 'Победа левого' : option === 'b' ? 'Победа правого' : 'Ничья'}
                        >
                          {option === 'a' ? '1' : option === 'b' ? '2' : 'X'}
                        </button>
                      ))}
                    </div>
                  ) : (
                    <span className="shrink-0 rounded-control border border-border px-1.5 py-0.5 text-[11px] text-muted">
                      {match.winner === 'a' ? '1:0' : match.winner === 'b' ? '0:1' : match.winner === 'draw' ? 'X' : '—'}
                    </span>
                  )}
                  <span
                    className={`flex-1 truncate text-sm ${
                      match.winner === 'b' ? 'font-semibold text-foreground' : 'text-muted'
                    }`}
                  >
                    {match.slot_b}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export function BracketView({ bracket, onPick }: { bracket: BracketDetail; onPick?: PickHandler }) {
  if (bracket.format === 'round_robin') {
    return <RoundRobinView bracket={bracket} onPick={onPick} />
  }

  if (bracket.format === 'double_elim' && bracket.de) {
    const de = bracket.de
    return (
      <div className="flex flex-col gap-6">
        <div>
          <h2 className="mb-3 text-sm font-semibold text-foreground">Верхняя сетка</h2>
          <EliminationColumns rounds={de.winners} segment="W" finalLabel="Финал верхней" onPick={onPick} />
        </div>
        {de.losers.length > 0 && (
          <div>
            <h2 className="mb-3 text-sm font-semibold text-foreground">Нижняя сетка</h2>
            <EliminationColumns rounds={de.losers} segment="L" finalLabel="Финал нижней" onPick={onPick} />
          </div>
        )}
        <div>
          <h2 className="mb-3 text-sm font-semibold text-foreground">Гранд-финал</h2>
          <MatchCard
            match={de.final}
            onPickA={onPick ? () => onPick('F', 0, 0, 'a') : undefined}
            onPickB={onPick ? () => onPick('F', 0, 0, 'b') : undefined}
          />
        </div>
      </div>
    )
  }

  return <EliminationColumns rounds={bracket.rounds} segment="W" finalLabel="Финал" onPick={onPick} />
}
