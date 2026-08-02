import { ChartLine } from '@phosphor-icons/react'
import { useEffect, useMemo, useState } from 'react'
import { fetchVoiceStats, type VoiceStats } from '../api/client'
import { Card } from '../components/ui/Card'
import { useT } from '../context/LanguageContext'
import { formatDuration } from '../utils/formatDuration'

const PERIODS = [7, 30, 90]

const WEEKDAY_KEYS = [
  'voiceStats.weekday.mon',
  'voiceStats.weekday.tue',
  'voiceStats.weekday.wed',
  'voiceStats.weekday.thu',
  'voiceStats.weekday.fri',
  'voiceStats.weekday.sat',
  'voiceStats.weekday.sun',
] as const

function BarChart({
  values,
  labels,
  tooltip,
}: {
  values: number[]
  labels: string[]
  tooltip: (label: string, minutes: number) => string
}) {
  const max = Math.max(1, ...values)
  return (
    <div className="flex h-36 items-end gap-1">
      {values.map((v, i) => (
        <div key={i} className="group relative flex flex-1 flex-col items-center gap-1">
          <div
            className="w-full rounded-t bg-primary/70 transition-colors group-hover:bg-primary"
            style={{ height: `${Math.max(2, (v / max) * 120)}px` }}
            title={tooltip(labels[i], v)}
          />
          <span className="text-[10px] text-muted">{labels[i]}</span>
        </div>
      ))}
    </div>
  )
}

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <Card className="flex flex-col gap-1">
      <span className="text-xs uppercase tracking-wide text-muted">{label}</span>
      <span className="text-xl font-semibold text-foreground">{value}</span>
    </Card>
  )
}

export function VoiceStatsPage() {
  const t = useT()
  const [days, setDays] = useState(30)
  const [stats, setStats] = useState<VoiceStats | null>(null)
  const [error, setError] = useState('')

  const weekdays = useMemo(() => WEEKDAY_KEYS.map((key) => t(key)), [t])

  useEffect(() => {
    setStats(null)
    fetchVoiceStats(days)
      .then(setStats)
      .catch(() => setError(t('voiceStats.errorLoad')))
  }, [days, t])

  return (
    <div className="flex max-w-4xl flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <ChartLine size={22} className="text-primary" />
          {t('voiceStats.title')}
        </h1>
        <div className="flex gap-1 rounded-control border border-border bg-surface p-1">
          {PERIODS.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setDays(p)}
              className={`rounded-control px-3 py-1 text-sm transition-colors ${
                days === p ? 'bg-primary-muted text-foreground' : 'text-muted hover:text-foreground'
              }`}
            >
              {t('voiceStats.periodDays', { n: p })}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}
      {!stats && !error && <p className="text-sm text-muted">{t('common.loading')}</p>}

      {stats && (
        <>
          <div className="grid gap-3 sm:grid-cols-3">
            <StatTile
              label={t('voiceStats.totalTime')}
              value={formatDuration(stats.total_seconds, t)}
            />
            <StatTile label={t('voiceStats.sessions')} value={String(stats.session_count)} />
            <StatTile label={t('voiceStats.peakConcurrent')} value={String(stats.peak_concurrent)} />
          </div>

          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">
              {t('voiceStats.byHour', { tz: stats.timezone || 'UTC' })}
            </h2>
            <BarChart
              values={stats.by_hour_minutes}
              labels={stats.by_hour_minutes.map((_, i) => String(i))}
              tooltip={(label, minutes) => t('voiceStats.barTooltip', { label, minutes })}
            />
          </Card>

          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">{t('voiceStats.byWeekday')}</h2>
            <BarChart
              values={stats.by_weekday_minutes}
              labels={weekdays}
              tooltip={(label, minutes) => t('voiceStats.barTooltip', { label, minutes })}
            />
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            <Card className="flex flex-col gap-2">
              <h2 className="font-semibold text-foreground">{t('voiceStats.topChannels')}</h2>
              {stats.top_channels.length === 0 && (
                <p className="text-sm text-muted">{t('voiceStats.noData')}</p>
              )}
              {stats.top_channels.map((c, i) => (
                <div key={i} className="flex items-center justify-between border-t border-border pt-2 first:border-t-0 first:pt-0">
                  <span className="truncate text-sm text-foreground">
                    {i + 1}. {c.name}
                  </span>
                  <span className="shrink-0 text-sm text-muted">{formatDuration(c.seconds, t)}</span>
                </div>
              ))}
            </Card>

            <Card className="flex flex-col gap-2">
              <h2 className="font-semibold text-foreground">{t('voiceStats.topUsers')}</h2>
              {stats.top_users.length === 0 && (
                <p className="text-sm text-muted">{t('voiceStats.noData')}</p>
              )}
              {stats.top_users.map((u, i) => (
                <div key={u.user_id} className="flex items-center gap-2 border-t border-border pt-2 first:border-t-0 first:pt-0">
                  <span className="w-5 text-sm text-muted">{i + 1}.</span>
                  {u.avatar ? (
                    <img src={u.avatar} alt="" className="h-6 w-6 rounded-full" />
                  ) : (
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary-muted text-[10px] font-semibold text-primary">
                      {u.display.slice(0, 1).toUpperCase()}
                    </span>
                  )}
                  <span className="min-w-0 flex-1 truncate text-sm text-foreground">{u.display}</span>
                  <span className="shrink-0 text-sm text-muted">{formatDuration(u.seconds, t)}</span>
                </div>
              ))}
            </Card>
          </div>
        </>
      )}
    </div>
  )
}
