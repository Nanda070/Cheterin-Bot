import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { lookupFetch } from '../api/client'
import { DsaResultsPanel, type DsaResponse } from '../components/DsaResultsPanel'
import { LookupIcon } from '../components/LookupIcon'
import { ErrorBanner, LoadingBlock, PrimaryButton } from '../components/ui'
import { useT } from '../context/LanguageContext'
import { isSnowflake, normalizeInviteCode } from '../lib/discord'
import { useLookupErrorMessage } from '../lib/useLookup'

type Mode = 'user' | 'bot' | 'server' | 'dsa'

const MODES: Mode[] = ['user', 'bot', 'server', 'dsa']

function parseMode(raw: string | null): Mode {
  if (raw === 'bot' || raw === 'server' || raw === 'dsa' || raw === 'user') return raw
  return 'user'
}

export function HomePage() {
  const t = useT()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [mode, setMode] = useState<Mode>(() => parseMode(searchParams.get('mode')))
  const [query, setQuery] = useState(() => searchParams.get('id') ?? '')
  const [error, setError] = useState<string | null>(null)
  const [dsaData, setDsaData] = useState<DsaResponse | null>(null)
  const [dsaLoading, setDsaLoading] = useState(false)
  const [dsaError, setDsaError] = useState<unknown>(null)
  const dsaLookupErr = useLookupErrorMessage(dsaError)
  const dsaErrMsg =
    dsaError instanceof Error && dsaError.message === 'invalid' ? t('common.invalidId') : dsaLookupErr

  useEffect(() => {
    const nextMode = parseMode(searchParams.get('mode'))
    setMode(nextMode)
    const id = searchParams.get('id') ?? ''
    if (nextMode === 'dsa') {
      setQuery(id)
    }
  }, [searchParams])

  useEffect(() => {
    if (mode !== 'dsa') {
      setDsaData(null)
      setDsaError(null)
      setDsaLoading(false)
      return
    }
    const id = (searchParams.get('id') ?? '').trim()
    if (!id) {
      setDsaData(null)
      setDsaError(null)
      setDsaLoading(false)
      return
    }
    if (!isSnowflake(id)) {
      setDsaError(new Error('invalid'))
      setDsaData(null)
      setDsaLoading(false)
      return
    }
    setDsaLoading(true)
    setDsaError(null)
    void lookupFetch<DsaResponse>(`/dsa/${id}`)
      .then(setDsaData)
      .catch(setDsaError)
      .finally(() => setDsaLoading(false))
  }, [mode, searchParams])

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    const value = query.trim()
    if (!value) {
      setError(t('home.error.empty'))
      return
    }

    if (mode === 'server') {
      const code = normalizeInviteCode(value)
      if (!code) {
        setError(t('home.error.invite'))
        return
      }
      setError(null)
      navigate(`/server/${encodeURIComponent(code)}`)
      return
    }

    if (!isSnowflake(value)) {
      setError(t('home.error.snowflake'))
      return
    }

    setError(null)

    if (mode === 'dsa') {
      setSearchParams({ mode: 'dsa', id: value })
      return
    }

    navigate(`/${mode}/${value}`)
  }

  const selectMode = (m: Mode) => {
    setMode(m)
    setError(null)
    setDsaError(null)
    if (m === 'dsa') {
      const next: Record<string, string> = { mode: 'dsa' }
      const id = query.trim()
      if (isSnowflake(id)) next.id = id
      setSearchParams(next)
    } else if (searchParams.get('mode') || searchParams.get('id')) {
      setSearchParams({})
    }
  }

  return (
    <div className="space-y-16 sm:space-y-20">
      <section className="lookup-hero-in mx-auto max-w-3xl text-center">
        <p className="mb-3 text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-primary-hover">
          {t('home.eyebrow')}
        </p>
        <div className="mb-5 flex items-center justify-center">
          <LookupIcon size={28} className="text-primary" />
        </div>
        <h1 className="font-display text-[2.1rem] font-bold leading-[1.12] tracking-tight sm:text-5xl md:text-[3.25rem]">
          {t('home.title')}
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-base leading-relaxed text-muted sm:text-lg">{t('home.subtitle')}</p>

        <form onSubmit={onSubmit} className="mt-9 space-y-4 text-left">
          <div className="lookup-mode-track mx-auto justify-center">
            {MODES.map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => selectMode(m)}
                className={`cursor-pointer rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                  mode === m
                    ? 'bg-primary text-white'
                    : 'text-muted hover:bg-surface-hover hover:text-foreground'
                }`}
                aria-pressed={mode === m}
              >
                {t(`home.mode.${m}`)}
              </button>
            ))}
          </div>

          <div className="lookup-search-ring flex flex-col gap-2 rounded-[18px] border border-border bg-surface p-2 sm:flex-row sm:items-stretch">
            <label className="sr-only" htmlFor="lookup-query">
              {t(`home.placeholder.${mode}`)}
            </label>
            <input
              id="lookup-query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t(`home.placeholder.${mode}`)}
              autoComplete="off"
              spellCheck={false}
              className="min-h-12 flex-1 rounded-[12px] bg-transparent px-4 text-base text-foreground outline-none placeholder:text-muted sm:min-h-14"
            />
            <PrimaryButton type="submit" className="sm:min-w-[7.5rem]">
              {t('home.submit')}
            </PrimaryButton>
          </div>

          <p className="text-center text-sm text-muted">{t(`home.hint.${mode}`)}</p>
          {error ? (
            <p role="alert" className="text-center text-sm text-danger">
              {error}
            </p>
          ) : null}
        </form>

        {mode === 'dsa' ? (
          <div className="mt-8 space-y-4">
            <p className="text-left text-sm leading-relaxed text-muted">{t('dsa.sourceNote')}</p>
            {dsaLoading ? <LoadingBlock rows={4} /> : null}
            {!dsaLoading && dsaError ? <ErrorBanner message={dsaErrMsg} /> : null}
            {!dsaLoading && !dsaError && dsaData ? <DsaResultsPanel data={dsaData} /> : null}
          </div>
        ) : null}
      </section>

      <section className="lookup-rise lookup-rise-delay-1">
        <div className="mb-5 flex items-end justify-between gap-4">
          <h2 className="font-display text-xl font-semibold tracking-tight sm:text-2xl">{t('home.modes.title')}</h2>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {MODES.map((m, index) => (
            <article key={m} className="lookup-panel lookup-card-lift p-5">
              <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-[10px] bg-primary-muted font-display text-sm font-bold text-primary-hover">
                {index + 1}
              </div>
              <h3 className="font-display text-base font-semibold text-foreground">{t(`home.modes.${m}.title`)}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{t(`home.modes.${m}.body`)}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}
