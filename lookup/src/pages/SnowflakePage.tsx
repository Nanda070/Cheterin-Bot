import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { DetailRow, ErrorBanner } from '../components/ui'
import { useT } from '../context/LanguageContext'
import { decodeSnowflake, isSnowflake } from '../lib/discord'

export function SnowflakePage() {
  const { id: routeId = '' } = useParams()
  const t = useT()
  const navigate = useNavigate()
  const [input, setInput] = useState(routeId)
  const decoded = useMemo(() => (isSnowflake(input.trim()) ? decodeSnowflake(input.trim()) : null), [input])

  const onDecode = () => {
    const value = input.trim()
    if (!isSnowflake(value)) return
    navigate(`/snowflake/${value}`)
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header>
        <h1 className="text-3xl font-bold">{t('snowflake.title')}</h1>
        <p className="mt-2 text-muted">{t('snowflake.lead')}</p>
      </header>

      <div className="flex flex-col gap-2 sm:flex-row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t('snowflake.placeholder')}
          className="min-h-11 flex-1 rounded-[10px] border border-border bg-surface px-3 outline-none focus:border-primary"
        />
        <button
          type="button"
          onClick={onDecode}
          className="cursor-pointer rounded-[10px] bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-hover"
        >
          {t('snowflake.decode')}
        </button>
      </div>

      {input.trim() && !decoded ? <ErrorBanner message={t('snowflake.invalid')} /> : null}

      {decoded ? (
        <section className="rounded-[14px] border border-border bg-surface/80 p-5">
          <dl>
            <DetailRow label={t('snowflake.utc')}>{decoded.createdAt.toUTCString()}</DetailRow>
            <DetailRow label={t('snowflake.unix')}>{decoded.timestampMs}</DetailRow>
            <DetailRow label={t('snowflake.worker')}>{decoded.workerId}</DetailRow>
            <DetailRow label={t('snowflake.process')}>{decoded.processId}</DetailRow>
            <DetailRow label={t('snowflake.increment')}>{decoded.increment}</DetailRow>
          </dl>
          <div className="mt-4 flex flex-wrap gap-2">
            <Link
              to={`/user/${input.trim()}`}
              className="rounded-[8px] border border-border px-3 py-1.5 text-sm hover:bg-surface-hover"
            >
              {t('snowflake.openUser')}
            </Link>
            <Link
              to={`/bot/${input.trim()}`}
              className="rounded-[8px] border border-border px-3 py-1.5 text-sm hover:bg-surface-hover"
            >
              {t('snowflake.openBot')}
            </Link>
          </div>
        </section>
      ) : null}
    </div>
  )
}
