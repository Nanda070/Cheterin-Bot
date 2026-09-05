import { BADGE_CATALOG } from '../lib/permissions'
import { PageHeader, Panel } from '../components/ui'
import { useLanguage, useT } from '../context/LanguageContext'

export function BadgesPage() {
  const t = useT()
  const { lang } = useLanguage()

  return (
    <div className="space-y-7 lookup-rise">
      <PageHeader title={t('badges.title')} lead={t('badges.lead')} />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {BADGE_CATALOG.map((badge) => (
          <Panel key={badge.key} className="lookup-card-lift p-4 sm:p-5">
            <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-[10px] bg-primary-muted font-display text-xs font-bold text-primary-hover">
              {badge.key.slice(0, 2).toUpperCase()}
            </div>
            <h2 className="font-display font-semibold">{lang === 'ru' ? badge.nameRu : badge.nameEn}</h2>
            <p className="mt-2 font-mono text-xs text-muted">
              {t('badges.bit')}: {badge.bit} (1 &lt;&lt; {Math.log2(badge.bit)})
            </p>
          </Panel>
        ))}
      </div>
    </div>
  )
}
