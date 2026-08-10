import { HardDrives, Pulse } from '@phosphor-icons/react'
import { useCallback, useEffect, useState } from 'react'
import { fetchHostHealth, type HostHealth } from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { useT } from '../context/LanguageContext'

const REFRESH_MS = 10_000

function formatBytes(bytes: number | null | undefined, t: (key: string, vars?: Record<string, string | number>) => string): string {
  if (bytes == null || Number.isNaN(bytes)) return t('health.na')
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let value = bytes
  let i = 0
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024
    i += 1
  }
  const digits = value >= 10 || i === 0 ? 0 : 1
  return `${value.toFixed(digits)} ${units[i]}`
}

function formatUptime(seconds: number | null | undefined, t: (key: string, vars?: Record<string, string | number>) => string): string {
  if (seconds == null || seconds < 0) return t('health.na')
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (d > 0) return t('health.uptime.dh', { d, h })
  if (h > 0) return t('health.uptime.hm', { h, m })
  return t('health.uptime.m', { m })
}

function MetricBar({ percent, label }: { percent: number | null; label: string }) {
  const clamped = percent == null ? 0 : Math.max(0, Math.min(100, percent))
  const tone =
    percent == null ? 'bg-muted' : percent >= 90 ? 'bg-danger' : percent >= 75 ? 'bg-warning' : 'bg-primary'
  return (
    <div className="mt-2">
      <div className="mb-1 flex items-center justify-between text-xs text-muted">
        <span>{label}</span>
        <span>{percent == null ? '—' : `${percent.toFixed(1)}%`}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-surface-hover">
        <div className={`h-full rounded-full transition-all ${tone}`} style={{ width: `${clamped}%` }} />
      </div>
    </div>
  )
}

export function HealthPage() {
  const t = useT()
  const [data, setData] = useState<HostHealth | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setBusy(true)
    try {
      const next = await fetchHostHealth()
      setData(next)
      setError('')
    } catch (err) {
      setError(formatApiError(err, t, 'health.errorLoad'))
    } finally {
      setBusy(false)
    }
  }, [t])

  useEffect(() => {
    void load()
    const id = window.setInterval(() => void load(), REFRESH_MS)
    return () => window.clearInterval(id)
  }, [load])

  return (
    <div className="flex max-w-3xl flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Pulse size={22} className="text-primary" />
          {t('health.title')}
        </h1>
        <Button variant="secondary" onClick={() => void load()} disabled={busy}>
          {t('health.refresh')}
        </Button>
      </div>
      <p className="text-sm text-muted">{t('health.intro')}</p>

      {error && <p className="text-sm text-danger">{error}</p>}
      {!error && !data && <p className="text-sm text-muted">{t('common.loading')}</p>}

      {data && (
        <div className="grid gap-3 sm:grid-cols-2">
          <Card>
            <p className="text-xs uppercase tracking-wide text-muted">{t('health.ram')}</p>
            <p className="mt-1 text-sm text-foreground">
              {formatBytes(data.ram.used_bytes, t)} / {formatBytes(data.ram.total_bytes, t)}
            </p>
            <MetricBar percent={data.ram.percent} label={t('health.usage')} />
          </Card>

          <Card>
            <p className="flex items-center gap-1.5 text-xs uppercase tracking-wide text-muted">
              <HardDrives size={14} />
              {t('health.disk')}
            </p>
            <p className="mt-1 text-sm text-foreground">
              {formatBytes(data.disk.used_bytes, t)} / {formatBytes(data.disk.total_bytes, t)}
            </p>
            <MetricBar percent={data.disk.percent} label={t('health.usage')} />
          </Card>

          <Card>
            <p className="text-xs uppercase tracking-wide text-muted">{t('health.cpu')}</p>
            <p className="mt-1 text-sm text-foreground">
              {data.cpu_percent == null ? t('health.na') : `${data.cpu_percent.toFixed(1)}%`}
              {data.cpu_count != null && (
                <span className="text-muted"> · {t('health.cpuCount', { n: data.cpu_count })}</span>
              )}
            </p>
            {data.load_avg && (
              <p className="mt-2 text-xs text-muted">
                {t('health.loadAvg', {
                  a: data.load_avg[0].toFixed(2),
                  b: data.load_avg[1].toFixed(2),
                  c: data.load_avg[2].toFixed(2),
                })}
              </p>
            )}
          </Card>

          <Card>
            <p className="text-xs uppercase tracking-wide text-muted">{t('health.uptime')}</p>
            <p className="mt-1 text-sm text-foreground">{formatUptime(data.uptime_seconds, t)}</p>
            <p className="mt-2 text-xs text-muted">
              {data.hostname || t('health.na')}
              {data.platform ? ` · ${data.platform}` : ''}
            </p>
          </Card>

          <Card className="sm:col-span-2">
            <p className="text-xs uppercase tracking-wide text-muted">{t('health.process')}</p>
            <p className="mt-1 text-sm text-foreground">
              {data.process?.name || t('health.na')}
              {data.process?.pid != null && (
                <span className="text-muted"> · PID {data.process.pid}</span>
              )}
            </p>
            <p className="mt-2 text-xs text-muted">
              {t('health.processRss', { size: formatBytes(data.process?.rss_bytes, t) })}
              {data.python_version ? ` · Python ${data.python_version}` : ''}
            </p>
          </Card>
        </div>
      )}
    </div>
  )
}
