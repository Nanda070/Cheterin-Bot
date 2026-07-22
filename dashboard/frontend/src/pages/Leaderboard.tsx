import { Trophy } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { fetchPublicLeaderboard, type PublicLeaderboardEntry } from '../api/client'
import { PublicLayout } from '../components/PublicLayout'
import { useT } from '../context/LanguageContext'

const MEDAL = ['🥇', '🥈', '🥉']

export function LeaderboardPage() {
  const t = useT()
  const { guildId } = useParams<{ guildId?: string }>()
  const [entries, setEntries] = useState<PublicLeaderboardEntry[] | null>(null)
  const [guildName, setGuildName] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    setEntries(null)
    setError('')
    fetchPublicLeaderboard(guildId)
      .then((data) => {
        setEntries(data.entries)
        setGuildName(data.guild_name)
      })
      .catch(() => setError(t('leaderboard.error')))
  }, [t, guildId])

  return (
    <PublicLayout>
      <div className="mx-auto max-w-2xl">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Trophy size={22} weight="fill" className="text-warning" />
          {t('leaderboard.title')}
          {guildName ? t('leaderboard.guildSuffix', { name: guildName }) : ''}
        </h1>
        <p className="mt-1 text-sm text-muted">{t('leaderboard.subtitle')}</p>

        {error && <p className="mt-6 text-sm text-muted">{error}</p>}
        {!entries && !error && <p className="mt-6 text-sm text-muted">{t('leaderboard.loading')}</p>}

        {entries && (
          <div className="animate-fade-in-up mt-6 overflow-hidden rounded-card border border-border bg-surface">
            {entries.length === 0 && <p className="p-4 text-sm text-muted">{t('leaderboard.empty')}</p>}
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
                  <p className="text-sm font-semibold text-primary">
                    {t('leaderboard.levelShort', { level: entry.level })}
                  </p>
                  <p className="text-xs text-muted">{t('leaderboard.xp', { xp: entry.xp.toLocaleString() })}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </PublicLayout>
  )
}
