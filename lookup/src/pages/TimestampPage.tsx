import { useMemo, useState, type FormEvent } from 'react'
import { CopyButton, PageHeader, Panel, PrimaryButton, SectionTitle, controlClass } from '../components/ui'
import { useT } from '../context/LanguageContext'
import { decodeSnowflake, isSnowflake } from '../lib/discord'

const STYLES = [
  { key: 't', labelKey: 'timestamp.style.t' },
  { key: 'T', labelKey: 'timestamp.style.T' },
  { key: 'd', labelKey: 'timestamp.style.d' },
  { key: 'D', labelKey: 'timestamp.style.D' },
  { key: 'f', labelKey: 'timestamp.style.f' },
  { key: 'F', labelKey: 'timestamp.style.F' },
  { key: 'R', labelKey: 'timestamp.style.R' },
] as const

function toUnixSeconds(date: Date): number {
  return Math.floor(date.getTime() / 1000)
}

function toDatetimeLocalValue(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export function TimestampPage() {
  const t = useT()
  const now = useMemo(() => new Date(), [])
  const [mode, setMode] = useState<'date' | 'snowflake'>('date')
  const [datetime, setDatetime] = useState(toDatetimeLocalValue(now))
  const [snowflake, setSnowflake] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [unix, setUnix] = useState<number | null>(() => toUnixSeconds(now))

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (mode === 'date') {
      const d = new Date(datetime)
      if (Number.isNaN(d.getTime())) {
        setError(t('timestamp.error.date'))
        setUnix(null)
        return
      }
      setError(null)
      setUnix(toUnixSeconds(d))
      return
    }
    const id = snowflake.trim()
    if (!isSnowflake(id)) {
      setError(t('common.invalidId'))
      setUnix(null)
      return
    }
    const decoded = decodeSnowflake(id)
    if (!decoded) {
      setError(t('common.invalidId'))
      setUnix(null)
      return
    }
    setError(null)
    setUnix(Math.floor(decoded.timestampMs / 1000))
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 lookup-rise">
      <PageHeader title={t('timestamp.title')} lead={t('timestamp.lead')} />

      <form onSubmit={onSubmit} className="space-y-4">
        <div className="lookup-mode-track inline-flex">
          {(['date', 'snowflake'] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => {
                setMode(m)
                setError(null)
              }}
              className={`cursor-pointer rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                mode === m ? 'bg-primary text-white' : 'text-muted hover:bg-surface-hover hover:text-foreground'
              }`}
              aria-pressed={mode === m}
            >
              {t(`timestamp.mode.${m}`)}
            </button>
          ))}
        </div>

        <Panel className="grid gap-4 p-5 sm:grid-cols-[1fr_auto] sm:items-end sm:p-6">
          {mode === 'date' ? (
            <label className="text-sm sm:col-span-1">
              <span className="text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-muted">
                {t('timestamp.datetime')}
              </span>
              <input
                type="datetime-local"
                value={datetime}
                onChange={(e) => setDatetime(e.target.value)}
                className={`mt-1.5 ${controlClass}`}
              />
            </label>
          ) : (
            <label className="text-sm sm:col-span-1">
              <span className="text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-muted">
                {t('timestamp.snowflake')}
              </span>
              <input
                value={snowflake}
                onChange={(e) => setSnowflake(e.target.value)}
                placeholder={t('timestamp.snowflakePlaceholder')}
                className={`mt-1.5 font-mono ${controlClass}`}
              />
            </label>
          )}
          <PrimaryButton type="submit">{t('timestamp.generate')}</PrimaryButton>
        </Panel>
      </form>

      {error ? (
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
      ) : null}

      {unix != null ? (
        <Panel className="space-y-4 p-5 sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <SectionTitle>{t('timestamp.unix')}</SectionTitle>
            <CopyButton value={String(unix)} />
          </div>
          <p className="font-mono text-lg text-foreground">{unix}</p>
          <p className="text-sm text-muted">{new Date(unix * 1000).toISOString()}</p>

          <SectionTitle>{t('timestamp.markdown')}</SectionTitle>
          <ul className="mt-2 space-y-2">
            {STYLES.map((style) => {
              const md = `<t:${unix}:${style.key}>`
              return (
                <li
                  key={style.key}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-[12px] border border-border bg-background-deep/50 px-3 py-2.5"
                >
                  <div className="min-w-0">
                    <p className="text-xs uppercase tracking-[0.12em] text-muted">{t(style.labelKey)}</p>
                    <p className="mt-0.5 break-all font-mono text-sm text-foreground">{md}</p>
                  </div>
                  <CopyButton value={md} />
                </li>
              )
            })}
          </ul>
        </Panel>
      ) : null}
    </div>
  )
}
