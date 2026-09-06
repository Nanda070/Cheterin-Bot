import { Link } from 'react-router-dom'
import { CopyButton, Panel, SectionTitle } from './ui'
import { useT } from '../context/LanguageContext'

export type DsaStatement = {
  uuid: string
  permalink: string | null
  platform_uid: string
  entity_kind: string
  decision_account_label: string | null
  decision_visibility_labels: string[]
  category_label: string | null
  incompatible_content_ground: string | null
  decision_facts: string | null
  application_date: string | null
  created_at: string | null
  automated_decision_label: string | null
}

export type DsaResponse = {
  id: string
  found: boolean
  count: number
  statements: DsaStatement[]
  disclaimer: string
  source: {
    name: string
    search_url: string
    retention_note: string
  }
}

const OFFICIAL_LINKS = [
  { labelKey: 'dsa.link.database', href: 'https://transparency.dsa.ec.europa.eu/statement-search' },
  { labelKey: 'dsa.link.hub', href: 'https://discord.com/safety-library' },
  { labelKey: 'dsa.link.eu', href: 'https://digital-strategy.ec.europa.eu/en/policies/digital-services-act' },
] as const

export function DsaResultsPanel({ data }: { data: DsaResponse }) {
  const t = useT()

  return (
    <div className="space-y-4 text-left">
      <Panel className="space-y-4 p-5 sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-muted">{t('dsa.idLabel')}</p>
            <p className="mt-1 font-mono text-lg text-foreground">{data.id}</p>
          </div>
          <CopyButton value={data.id} />
        </div>

        {data.found ? (
          <p className="text-sm text-foreground">{t('dsa.found', { count: String(data.count) })}</p>
        ) : (
          <p className="text-sm leading-relaxed text-muted">{t('dsa.noData')}</p>
        )}

        <p className="text-xs leading-relaxed text-muted">{data.disclaimer}</p>

        {data.statements.map((stmt) => (
          <article key={stmt.uuid} className="rounded-[12px] border border-border bg-background-deep/60 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-primary/35 bg-primary-muted px-2.5 py-0.5 text-[0.7rem] font-medium text-primary-hover">
                {stmt.entity_kind === 'account' ? t('dsa.kind.account') : t('dsa.kind.content')}
              </span>
              {stmt.decision_account_label ? (
                <span className="text-sm font-semibold text-foreground">{stmt.decision_account_label}</span>
              ) : null}
            </div>
            {stmt.category_label ? <p className="mt-2 text-sm text-foreground">{stmt.category_label}</p> : null}
            {stmt.incompatible_content_ground ? (
              <p className="mt-1 text-sm text-muted">{stmt.incompatible_content_ground}</p>
            ) : null}
            {stmt.decision_facts ? <p className="mt-2 text-sm leading-relaxed text-muted">{stmt.decision_facts}</p> : null}
            <dl className="mt-3 grid gap-1 text-xs text-muted sm:grid-cols-2">
              {stmt.application_date ? (
                <div>
                  <dt className="uppercase tracking-[0.12em]">{t('dsa.applicationDate')}</dt>
                  <dd className="mt-0.5 text-foreground">{stmt.application_date}</dd>
                </div>
              ) : null}
              {stmt.automated_decision_label ? (
                <div>
                  <dt className="uppercase tracking-[0.12em]">{t('dsa.automated')}</dt>
                  <dd className="mt-0.5 text-foreground">{stmt.automated_decision_label}</dd>
                </div>
              ) : null}
            </dl>
            {stmt.permalink ? (
              <a
                href={stmt.permalink}
                target="_blank"
                rel="noreferrer"
                className="mt-3 inline-flex text-sm font-medium text-primary-hover hover:underline"
              >
                {t('dsa.permalink')} →
              </a>
            ) : null}
          </article>
        ))}

        <Link to={`/user/${data.id}`} className="inline-flex text-sm font-medium text-primary-hover hover:underline">
          {t('dsa.openUser')}
        </Link>
      </Panel>

      <Panel className="p-5 sm:p-6">
        <SectionTitle>{t('dsa.official')}</SectionTitle>
        <ul className="mt-3 space-y-2.5 text-sm">
          {OFFICIAL_LINKS.map((link) => (
            <li key={link.href}>
              <a href={link.href} target="_blank" rel="noreferrer" className="font-medium text-primary-hover hover:underline">
                {t(link.labelKey)}
              </a>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  )
}
