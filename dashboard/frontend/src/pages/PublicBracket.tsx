import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { fetchPublicBracket, type BracketDetail } from '../api/client'

export function PublicBracketPage() {
  const { token } = useParams<{ token: string }>()
  const [bracket, setBracket] = useState<BracketDetail | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) return
    fetchPublicBracket(token)
      .then(setBracket)
      .catch(() => setError('Сетка не найдена.'))
  }, [token])

  if (error) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-background">
        <p className="text-sm text-danger">{error}</p>
      </div>
    )
  }

  if (!bracket) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-background">
        <p className="text-sm text-muted">Загрузка…</p>
      </div>
    )
  }

  return (
    <div className="min-h-dvh bg-background p-6">
      <h1 className="mb-6 text-lg font-semibold text-foreground">{bracket.title}</h1>
      <div className="flex gap-6 overflow-x-auto">
        {bracket.rounds.map((round, roundIndex) => (
          <div key={roundIndex} className="flex flex-col justify-around gap-4">
            <p className="text-xs font-medium uppercase tracking-wide text-muted">
              {roundIndex === bracket.rounds.length - 1 ? 'Финал' : `Раунд ${roundIndex + 1}`}
            </p>
            {round.map((match, matchIndex) => (
              <div
                key={matchIndex}
                className="w-48 rounded-card border border-border bg-surface p-2 shadow-[0_1px_0_0_rgba(255,255,255,0.04)_inset]"
              >
                <p className={`px-2 py-1 text-sm ${match.winner === 'a' ? 'font-semibold text-foreground' : 'text-muted'}`}>
                  {match.slot_a ?? '—'}
                </p>
                <p className={`px-2 py-1 text-sm ${match.winner === 'b' ? 'font-semibold text-foreground' : 'text-muted'}`}>
                  {match.slot_b ?? '—'}
                </p>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
