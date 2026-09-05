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

export function CookiesPage() {
  const { lang, t } = useLanguage()

  return (
    <PublicLayout>
      <article
        key={`${lang}-cookies`}
        className="animate-fade-in-up mx-auto max-w-3xl rounded-card border border-border bg-surface p-6"
      >
        <h1 className="border-l-2 border-primary pl-3 text-lg font-semibold text-foreground">{t('cookies.title')}</h1>
        <p className="mt-1 pl-3.5 text-xs text-muted">{t('cookies.lastUpdated')}</p>

        <Section title={t('cookies.s1.title')}>
          <p>{t('cookies.s1.p1')}</p>
        </Section>

        <Section title={t('cookies.s2.title')}>
          <p>{t('cookies.s2.p1')}</p>
          <ul className="flex list-disc flex-col gap-1 pl-5">
            <li>{t('cookies.s2.li1')}</li>
            <li>{t('cookies.s2.li2')}</li>
            <li>{t('cookies.s2.li3')}</li>
          </ul>
          <p>{t('cookies.s2.p2')}</p>
        </Section>

        <Section title={t('cookies.s3.title')}>
          <p>{t('cookies.s3.p1')}</p>
        </Section>

        <Section title={t('cookies.s4.title')}>
          <p>{t('cookies.s4.p1')}</p>
        </Section>
      </article>
    </PublicLayout>
  )
}
