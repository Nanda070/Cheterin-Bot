import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { PageHeader, Panel, PrimaryButton, controlClass } from '../components/ui'
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
    <div className="mx-auto max-w-2xl space-y-6 lookup-rise">
      <PageHeader title={t('dsa.title')} lead={t('dsa.lead')} />
      <p className="text-sm leading-relaxed text-muted">{t('dsa.skeleton')}</p>
      <p className="text-xs text-warning">{t('dsa.hiddenNav')}</p>

      <div className="lookup-search-ring flex flex-col gap-2 rounded-[16px] border border-border bg-surface p-2 sm:flex-row">
        <label className="sr-only" htmlFor="dsa-id">
          {t('dsa.idLabel')}
        </label>
        <input
          id="dsa-id"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t('dsa.placeholder')}
          className={`min-h-12 flex-1 border-0 bg-transparent ${controlClass}`}
        />
        <PrimaryButton
          onClick={() => {
            const value = input.trim()
            if (!isSnowflake(value)) return
            navigate(`/dsa/${value}`)
          }}
        >
          {t('dsa.open')}
        </PrimaryButton>
      </div>

      {routeId ? (
        <Panel className="p-5 sm:p-6">
          <p className="text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-muted">{t('dsa.idLabel')}</p>
          <p className="mt-1.5 font-mono text-lg">{routeId}</p>
          <p className="mt-4 text-sm leading-relaxed text-muted">{t('dsa.noData')}</p>
          <Link to={`/user/${routeId}`} className="mt-4 inline-block text-sm font-medium text-primary-hover hover:underline">
            {t('user.title')}
          </Link>
        </Panel>
      ) : null}

      <Panel className="p-5 sm:p-6">
        <h2 className="font-display text-lg font-semibold">{t('dsa.official')}</h2>
        <ul className="mt-3 space-y-2.5 text-sm">
          {OFFICIAL_LINKS.map((link) => (
            <li key={link.href}>
              <a href={link.href} target="_blank" rel="noreferrer" className="font-medium text-primary-hover hover:underline">
                {link.label}
              </a>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  )
}
