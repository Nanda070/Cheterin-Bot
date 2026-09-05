import { Link } from 'react-router-dom'
import { PageHeader, Panel } from '../components/ui'
import { useT } from '../context/LanguageContext'

export function AboutPage() {
  const t = useT()

  const sections = ['s1', 's2', 's3', 's4'] as const

  return (
    <article className="mx-auto max-w-3xl space-y-8 lookup-rise">
      <PageHeader title={t('about.title')} lead={t('about.lead')} eyebrow="Lookup" />

      <div className="grid gap-3">
        {sections.map((key, index) => (
          <Panel key={key} className="p-5 sm:p-6">
            <div className="flex gap-4">
              <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-[8px] bg-primary-muted font-display text-xs font-bold text-primary-hover">
                {index + 1}
              </span>
              <div>
                <h2 className="font-display text-lg font-semibold">{t(`about.${key}.title`)}</h2>
                <p className="mt-2 text-sm leading-relaxed text-muted">{t(`about.${key}.body`)}</p>
              </div>
            </div>
          </Panel>
        ))}
      </div>

      <Link
        to="/"
        className="inline-flex cursor-pointer rounded-[12px] bg-primary px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-primary-hover"
      >
        {t('about.cta')}
      </Link>
    </article>
  )
}
