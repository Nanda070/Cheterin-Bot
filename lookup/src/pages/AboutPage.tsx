import { Link } from 'react-router-dom'
import { useT } from '../context/LanguageContext'

export function AboutPage() {
  const t = useT()

  const sections = ['s1', 's2', 's3', 's4'] as const

  return (
    <article className="mx-auto max-w-3xl space-y-8">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">{t('about.title')}</h1>
        <p className="mt-4 text-base leading-relaxed text-muted">{t('about.lead')}</p>
      </header>

      {sections.map((key) => (
        <section key={key} className="rounded-[14px] border border-border bg-surface/70 p-5">
          <h2 className="text-lg font-semibold">{t(`about.${key}.title`)}</h2>
          <p className="mt-2 text-sm leading-relaxed text-muted">{t(`about.${key}.body`)}</p>
        </section>
      ))}

      <Link
        to="/"
        className="inline-flex rounded-[10px] bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-hover"
      >
        {t('about.cta')}
      </Link>
    </article>
  )
}
