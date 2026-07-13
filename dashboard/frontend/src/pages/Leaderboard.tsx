import { Trophy } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { fetchPublicLeaderboard, type PublicLeaderboardEntry } from '../api/client'
import { PublicLayout } from '../components/PublicLayout'

const MEDAL = ['🥇', '🥈', '🥉']

export function LeaderboardPage() {
  const [entries, setEntries] = useState<PublicLeaderboardEntry[] | null>(null)
  const [guildName, setGuildName] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    fetchPublicLeaderboard()
      .then((data) => {
        setEntries(data.entries)
        setGuildName(data.guild_name)
      })
      .catch(() => setError('Рейтинг недоступен: система уровней или публичная страница отключены.'))
  }, [])

  return (
    <PublicLayout>
      <div className="mx-auto max-w-2xl">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Trophy size={22} weight="fill" className="text-warning" />
          Рейтинг участников{guildName ? ` — ${guildName}` : ''}
        </h1>
        <p className="mt-1 text-sm text-muted">Топ-100 по опыту: активность в чатах и голосовых каналах.</p>

        {error && <p className="mt-6 text-sm text-muted">{error}</p>}
        {!entries && !error && <p className="mt-6 text-sm text-muted">Загрузка…</p>}

        {entries && (
          <div className="animate-fade-in-up mt-6 overflow-hidden rounded-card border border-border bg-surface">
            {entries.length === 0 && <p className="p-4 text-sm text-muted">Рейтинг пока пуст.</p>}
            {entries.map((entry) => (
              <div
                key={entry.rank}
                className="flex items-center gap-3 border-b border-border px-4 py-2.5 last:border-b-0"
              >
                <span className="w-9 text-center text-sm font-semibold text-muted">
                  {MEDAL[entry.rank - 1] ?? `#${entry.rank}`}
                </span>
                {entry.avatar ? (
                  <img src={entry.avatar} alt="" className="h-8 w-8 rounded-full" />
                ) : (
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-muted text-xs font-semibold text-primary">
                    {entry.display.slice(0, 1).toUpperCase()}
                  </span>
                )}
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm text-foreground">{entry.display}</p>
                  <p className="text-xs text-muted">🔊 {entry.voice_time_text}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-primary">Ур. {entry.level}</p>
                  <p className="text-xs text-muted">{entry.xp.toLocaleString()} XP</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </PublicLayout>
  )
}
