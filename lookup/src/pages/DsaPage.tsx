import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useT } from '../context/LanguageContext'
import { isSnowflake } from '../lib/discord'

const OFFICIAL_LINKS = [
  {
    label: 'Discord Transparency Hub',
    href: 'https://discord.com/safety-library',
  },
  {
    label: 'EU DSA / Digital Services Act overview',
    href: 'https://digital-strategy.ec.europa.eu/en/policies/digital-services-act',
  },
]

export function DsaPage() {
  const { id: routeId = '' } = useParams()
  const t = useT()
  const navigate = useNavigate()
  const [input, setInput] = useState(routeId)

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header>
        <h1 className="text-3xl font-bold">{t('dsa.title')}</h1>
        <p className="mt-2 text-muted">{t('dsa.lead')}</p>
        <p className="mt-3 text-sm text-muted">{t('dsa.skeleton')}</p>
        <p className="mt-2 text-xs text-warning">{t('dsa.hiddenNav')}</p>
      </header>

      <div className="flex flex-col gap-2 sm:flex-row">
        <label className="sr-only" htmlFor="dsa-id">
          {t('dsa.idLabel')}
        </label>
        <input
          id="dsa-id"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t('dsa.placeholder')}
          className="min-h-11 flex-1 rounded-[10px] border border-border bg-surface px-3 outline-none focus:border-primary"
        />
        <button
          type="button"
          className="cursor-pointer rounded-[10px] bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-hover"
          onClick={() => {
            const value = input.trim()
            if (!isSnowflake(value)) return
            navigate(`/dsa/${value}`)
          }}
        >
          {t('dsa.open')}
        </button>
      </div>

      {routeId ? (
        <section className="rounded-[14px] border border-border bg-surface/80 p-5">
          <p className="text-sm text-muted">{t('dsa.idLabel')}</p>
          <p className="mt-1 font-mono text-lg">{routeId}</p>
          <p className="mt-4 text-sm leading-relaxed text-muted">{t('dsa.noData')}</p>
          <Link to={`/user/${routeId}`} className="mt-4 inline-block text-sm text-primary-hover hover:underline">
            {t('user.title')}
          </Link>
        </section>
      ) : null}

      <section>
        <h2 className="text-lg font-semibold">{t('dsa.official')}</h2>
        <ul className="mt-3 space-y-2 text-sm">
          {OFFICIAL_LINKS.map((link) => (
            <li key={link.href}>
              <a href={link.href} target="_blank" rel="noreferrer" className="text-primary-hover hover:underline">
                {link.label}
              </a>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
