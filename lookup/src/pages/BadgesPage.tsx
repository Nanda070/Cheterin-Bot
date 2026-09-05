import { BADGE_CATALOG } from '../lib/permissions'
import { useLanguage, useT } from '../context/LanguageContext'

export function BadgesPage() {
  const t = useT()
  const { lang } = useLanguage()

  return (
    <div className="space-y-6">
      <header className="max-w-3xl">
        <h1 className="text-3xl font-bold">{t('badges.title')}</h1>
        <p className="mt-2 text-muted">{t('badges.lead')}</p>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {BADGE_CATALOG.map((badge) => (
          <article key={badge.key} className="rounded-[14px] border border-border bg-surface/80 p-4">
            <h2 className="font-medium">{lang === 'ru' ? badge.nameRu : badge.nameEn}</h2>
            <p className="mt-2 text-xs text-muted">
              {t('badges.bit')}: {badge.bit} (1 &lt;&lt; {Math.log2(badge.bit)})
            </p>
          </article>
        ))}
      </div>
    </div>
  )
}
