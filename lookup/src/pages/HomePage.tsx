import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useT } from '../context/LanguageContext'
import { isSnowflake, normalizeInviteCode } from '../lib/discord'

type Mode = 'user' | 'bot' | 'server'

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
    <div className="space-y-14">
      <section className="mx-auto max-w-3xl text-center">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">{t('home.title')}</h1>
        <p className="mx-auto mt-4 max-w-2xl text-base leading-relaxed text-muted sm:text-lg">{t('home.subtitle')}</p>

        <form onSubmit={onSubmit} className="mt-8 space-y-4 text-left">
          <div className="flex flex-wrap justify-center gap-2">
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
                    : 'border border-border bg-surface text-muted hover:bg-surface-hover hover:text-foreground'
                }`}
                aria-pressed={mode === m}
              >
                {t(`home.mode.${m}`)}
              </button>
            ))}
          </div>

          <div className="lookup-search-ring flex flex-col gap-2 rounded-[16px] border-2 border-border bg-surface p-2 sm:flex-row sm:items-stretch">
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
              className="min-h-12 flex-1 rounded-[12px] bg-transparent px-4 text-base text-foreground outline-none placeholder:text-muted"
            />
            <button
              type="submit"
              className="cursor-pointer rounded-[12px] bg-primary px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-primary-hover"
            >
              {t('home.submit')}
            </button>
          </div>

          <p className="text-center text-sm text-muted">{t(`home.hint.${mode}`)}</p>
          {error ? (
            <p role="alert" className="text-center text-sm text-danger">
              {error}
            </p>
          ) : null}
        </form>
      </section>

      <section>
        <h2 className="text-lg font-semibold">{t('home.modes.title')}</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {modes.map((m) => (
            <article key={m} className="rounded-[14px] border border-border bg-surface/80 p-5">
              <h3 className="font-medium text-foreground">{t(`home.modes.${m}.title`)}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{t(`home.modes.${m}.body`)}</p>
            </article>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold">{t('home.tools.title')}</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {(
            [
              ['/snowflake', 'snowflake'],
              ['/permissions', 'permissions'],
              ['/avatars', 'avatars'],
              ['/badges', 'badges'],
              ['/plugins', 'plugins'],
            ] as const
          ).map(([to, key]) => (
            <Link
              key={to}
              to={to}
              className="rounded-[14px] border border-border bg-surface/80 p-4 transition-colors hover:border-primary/50 hover:bg-surface-hover"
            >
              <p className="font-medium">{t(`home.tools.${key}`)}</p>
              <p className="mt-1 text-sm text-muted">{t(`home.tools.${key}.desc`)}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
