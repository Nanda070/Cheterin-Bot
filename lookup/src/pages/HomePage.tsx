import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LookupIcon } from '../components/LookupIcon'
import { PrimaryButton } from '../components/ui'
import { useT } from '../context/LanguageContext'
import { isSnowflake, normalizeInviteCode } from '../lib/discord'

type Mode = 'user' | 'bot' | 'server'

const TOOLS = [
  ['/snowflake', 'snowflake'],
  ['/permissions', 'permissions'],
  ['/avatars', 'avatars'],
  ['/badges', 'badges'],
  ['/plugins', 'plugins'],
] as const

export function HomePage() {
  const t = useT()
  const navigate = useNavigate()
  const [mode, setMode] = useState<Mode>('user')
  const [query, setQuery] = useState('')
  const [error, setError] = useState<string | null>(null)

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
    navigate(`/${mode}/${value}`)
  }

  const modes: Mode[] = ['user', 'bot', 'server']

  return (
    <div className="space-y-16 sm:space-y-20">
      <section className="lookup-hero-in mx-auto max-w-3xl text-center">
        <div className="mb-4 flex items-center justify-center gap-2">
          <LookupIcon size={22} className="text-primary" />
          <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-primary-hover">
            Lookup
          </p>
        </div>
        <h1 className="font-display text-[2.1rem] font-bold leading-[1.12] tracking-tight sm:text-5xl md:text-[3.25rem]">
          {t('home.title')}
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-base leading-relaxed text-muted sm:text-lg">{t('home.subtitle')}</p>

        <form onSubmit={onSubmit} className="mt-9 space-y-4 text-left">
          <div className="lookup-mode-track mx-auto justify-center">
            {modes.map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => {
                  setMode(m)
                  setError(null)
                }}
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
      </section>

      <section className="lookup-rise lookup-rise-delay-1">
        <div className="mb-5 flex items-end justify-between gap-4">
          <h2 className="font-display text-xl font-semibold tracking-tight sm:text-2xl">{t('home.modes.title')}</h2>
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          {modes.map((m, index) => (
            <article
              key={m}
              className={`lookup-panel lookup-card-lift p-5 ${index === 0 ? '' : ''}`}
            >
              <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-[10px] bg-primary-muted font-display text-sm font-bold text-primary-hover">
                {index + 1}
              </div>
              <h3 className="font-display text-base font-semibold text-foreground">{t(`home.modes.${m}.title`)}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{t(`home.modes.${m}.body`)}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="lookup-rise lookup-rise-delay-2">
        <div className="mb-5 flex items-end justify-between gap-4">
          <h2 className="font-display text-xl font-semibold tracking-tight sm:text-2xl">{t('home.tools.title')}</h2>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {TOOLS.map(([to, key]) => (
            <Link
              key={to}
              to={to}
              className="lookup-panel lookup-card-lift group flex flex-col p-5"
            >
              <p className="font-display text-base font-semibold transition-colors group-hover:text-primary-hover">
                {t(`home.tools.${key}`)}
              </p>
              <p className="mt-2 flex-1 text-sm leading-relaxed text-muted">{t(`home.tools.${key}.desc`)}</p>
              <span className="mt-4 text-xs font-semibold uppercase tracking-[0.14em] text-muted group-hover:text-primary-hover">
                →
              </span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
