import type { ReactNode } from 'react'
import { PublicLayout } from '../components/PublicLayout'
import { useLanguage } from '../context/LanguageContext'

function Section(props: { title: string; children: ReactNode }) {
  return (
    <section className="mt-6 first:mt-0">
      <h2 className="text-base font-semibold text-foreground">{props.title}</h2>
      <div className="mt-2 flex flex-col gap-2 text-sm leading-relaxed text-muted">{props.children}</div>
    </section>
  )
}

export function DisclaimerPage() {
  const { lang, t } = useLanguage()

  return (
    <PublicLayout>
      <article
        key={`${lang}-disclaimer`}
        className="animate-fade-in-up mx-auto max-w-3xl rounded-card border border-border bg-surface p-6"
      >
        <h1 className="border-l-2 border-primary pl-3 text-lg font-semibold text-foreground">{t('disclaimer.title')}</h1>
        <p className="mt-1 pl-3.5 text-xs text-muted">{t('disclaimer.lastUpdated')}</p>

        <Section title={t('disclaimer.s1.title')}>
          <p>{t('disclaimer.s1.p1')}</p>
        </Section>

        <Section title={t('disclaimer.s2.title')}>
          <p>{t('disclaimer.s2.p1')}</p>
          <p>{t('disclaimer.s2.p2')}</p>
        </Section>

        <Section title={t('disclaimer.s3.title')}>
          <p>{t('disclaimer.s3.p1')}</p>
        </Section>

        <Section title={t('disclaimer.s4.title')}>
          <p>{t('disclaimer.s4.p1')}</p>
        </Section>
      </article>
    </PublicLayout>
  )
}
