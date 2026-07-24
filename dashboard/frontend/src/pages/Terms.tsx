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

function Sub(props: { title: string; children: ReactNode }) {
  return (
    <>
      <h3 className="mt-3 font-medium text-foreground">{props.title}</h3>
      {props.children}
    </>
  )
}

function DefItem(props: { termKey: string; restKey: string; t: (key: string) => string }) {
  return (
    <li>
      <strong>{props.t(props.termKey)}</strong> {props.t(props.restKey)}
    </li>
  )
}

export function TermsPage() {
  const { lang, t } = useLanguage()

  return (
    <PublicLayout>
      <article
        key={`${lang}-terms`}
        className="animate-fade-in-up mx-auto max-w-3xl rounded-card border border-border bg-surface p-6"
      >
        <h1 className="border-l-2 border-primary pl-3 text-lg font-semibold text-foreground">{t('terms.title')}</h1>
        <p className="mt-1 pl-3.5 text-xs text-muted">{t('terms.lastUpdated')}</p>

        <Section title={t('terms.s1.title')}>
          <ul className="flex list-disc flex-col gap-1 pl-5">
            <DefItem termKey="terms.s1.li1.prefix" restKey="terms.s1.li1.rest" t={t} />
            <DefItem termKey="terms.s1.li2.prefix" restKey="terms.s1.li2.rest" t={t} />
            <DefItem termKey="terms.s1.li3.prefix" restKey="terms.s1.li3.rest" t={t} />
            <DefItem termKey="terms.s1.li4.prefix" restKey="terms.s1.li4.rest" t={t} />
            <DefItem termKey="terms.s1.li5.prefix" restKey="terms.s1.li5.rest" t={t} />
            <DefItem termKey="terms.s1.li6.prefix" restKey="terms.s1.li6.rest" t={t} />
            <DefItem termKey="terms.s1.li7.prefix" restKey="terms.s1.li7.rest" t={t} />
            <DefItem termKey="terms.s1.li8.prefix" restKey="terms.s1.li8.rest" t={t} />
          </ul>
        </Section>

        <Section title={t('terms.s2.title')}>
          <p>{t('terms.s2.p1')}</p>
          <p>{t('terms.s2.p2')}</p>
          <p>
            {t('terms.s2.p3.prefix')}{' '}
            <a
              href="https://discord.com/terms"
              target="_blank"
              rel="noreferrer"
              className="text-primary hover:underline"
            >
              {t('terms.s2.discordTerms')}
            </a>{' '}
            {t('terms.s2.p3.and')}{' '}
            <a
              href="https://discord.com/guidelines"
              target="_blank"
              rel="noreferrer"
              className="text-primary hover:underline"
            >
              {t('terms.s2.discordGuidelines')}
            </a>
            {t('terms.s2.p3.suffix')}
          </p>
        </Section>

        <Section title={t('terms.s3.title')}>
          <p>{t('terms.s3.p1')}</p>
          <ul className="flex list-disc flex-col gap-1 pl-5">
            <li>{t('terms.s3.li1')}</li>
            <li>{t('terms.s3.li2')}</li>
            <li>{t('terms.s3.li3')}</li>
            <li>{t('terms.s3.li4')}</li>
            <li>{t('terms.s3.li5')}</li>
            <li>{t('terms.s3.li6')}</li>
            <li>{t('terms.s3.li7')}</li>
            <li>{t('terms.s3.li8')}</li>
            <li>{t('terms.s3.li9')}</li>
            <li>{t('terms.s3.li10')}</li>
            <li>{t('terms.s3.li11')}</li>
            <li>{t('terms.s3.li12')}</li>
            <li>{t('terms.s3.li13')}</li>
            <li>{t('terms.s3.li14')}</li>
            <li>{t('terms.s3.li15')}</li>
            <li>{t('terms.s3.li16')}</li>
            <li>{t('terms.s3.li17')}</li>
          </ul>
          <p>{t('terms.s3.p2')}</p>
          <p>{t('terms.s3.p3')}</p>
          <p>{t('terms.s3.p4')}</p>
        </Section>

        <Section title={t('terms.s4.title')}>
          <p>{t('terms.s4.p1')}</p>
          <ul className="flex list-disc flex-col gap-1 pl-5">
            <li>{t('terms.s4.li1')}</li>
            <li>{t('terms.s4.li2')}</li>
            <li>{t('terms.s4.li3')}</li>
            <li>{t('terms.s4.li4')}</li>
            <li>{t('terms.s4.li5')}</li>
            <li>{t('terms.s4.li6')}</li>
          </ul>
          <p>{t('terms.s4.p2')}</p>
        </Section>

        <Section title={t('terms.s5.title')}>
          <Sub title={t('terms.s5.sub1.title')}>
            <p>{t('terms.s5.sub1.p1')}</p>
          </Sub>
          <Sub title={t('terms.s5.sub2.title')}>
            <p>{t('terms.s5.sub2.p1')}</p>
          </Sub>
          <Sub title={t('terms.s5.sub3.title')}>
            <p>{t('terms.s5.sub3.p1')}</p>
          </Sub>
          <Sub title={t('terms.s5.sub4.title')}>
            <p>{t('terms.s5.sub4.p1')}</p>
          </Sub>
        </Section>

        <Section title={t('terms.s6.title')}>
          <p>{t('terms.s6.p1')}</p>
          <p>
            {t('terms.s6.p2.prefix')}{' '}
            <strong>{t('terms.s6.p2.bold')}</strong> {t('terms.s6.p2.suffix')}
          </p>
          <p>{t('terms.s6.p3')}</p>
          <p>{t('terms.s6.p4')}</p>
          <p>{t('terms.s6.p5')}</p>
        </Section>

        <Section title={t('terms.s7.title')}>
          <p>{t('terms.s7.p1')}</p>
          <p>{t('terms.s7.p2')}</p>
          <p>{t('terms.s7.p3')}</p>
        </Section>

        <Section title={t('terms.s8.title')}>
          <p>{t('terms.s8.p1')}</p>
          <p>{t('terms.s8.p2')}</p>
          <p>{t('terms.s8.p3')}</p>
          <p>{t('terms.s8.p4')}</p>
        </Section>

        <Section title={t('terms.s9.title')}>
          <p>{t('terms.s9.p1')}</p>
          <p>{t('terms.s9.p2')}</p>
        </Section>

        <Section title={t('terms.s10.title')}>
          <p>{t('terms.s10.p1')}</p>
          <p>{t('terms.s10.p2')}</p>
        </Section>

        <Section title={t('terms.s11.title')}>
          <p>{t('terms.s11.p1')}</p>
          <p>{t('terms.s11.p2')}</p>
        </Section>

        <Section title={t('terms.s12.title')}>
          <p>{t('terms.s12.p1')}</p>
        </Section>
      </article>
    </PublicLayout>
  )
}
