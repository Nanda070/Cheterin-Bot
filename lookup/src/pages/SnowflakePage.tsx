import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { DetailRow, ErrorBanner, PageHeader, Panel, PrimaryButton, controlClass } from '../components/ui'
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
    navigate(`/plugins/snowflake/${value}`)
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 lookup-rise">
      <PageHeader title={t('snowflake.title')} lead={t('snowflake.lead')} />

      <div className="lookup-search-ring flex flex-col gap-2 rounded-[16px] border border-border bg-surface p-2 sm:flex-row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t('snowflake.placeholder')}
          className={`min-h-12 flex-1 border-0 bg-transparent ${controlClass}`}
        />
        <PrimaryButton onClick={onDecode}>{t('snowflake.decode')}</PrimaryButton>
      </div>

      {input.trim() && !decoded ? <ErrorBanner message={t('snowflake.invalid')} /> : null}

      {decoded ? (
        <Panel className="p-5 sm:p-6">
          <dl>
            <DetailRow label={t('snowflake.utc')}>{decoded.createdAt.toUTCString()}</DetailRow>
            <DetailRow label={t('snowflake.unix')}>{decoded.timestampMs}</DetailRow>
            <DetailRow label={t('snowflake.worker')}>{decoded.workerId}</DetailRow>
            <DetailRow label={t('snowflake.process')}>{decoded.processId}</DetailRow>
            <DetailRow label={t('snowflake.increment')}>{decoded.increment}</DetailRow>
          </dl>
          <div className="mt-5 flex flex-wrap gap-2">
            <Link
              to={`/user/${input.trim()}`}
              className="rounded-[8px] border border-border px-3 py-1.5 text-sm transition-colors hover:bg-surface-hover"
            >
              {t('snowflake.openUser')}
            </Link>
            <Link
              to={`/bot/${input.trim()}`}
              className="rounded-[8px] border border-border px-3 py-1.5 text-sm transition-colors hover:bg-surface-hover"
            >
              {t('snowflake.openBot')}
            </Link>
          </div>
        </Panel>
      ) : null}
    </div>
  )
}
