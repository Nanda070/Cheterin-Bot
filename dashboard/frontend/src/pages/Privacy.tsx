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

function DataTable(props: { headers: [string, string, string]; rows: [string, string, string][] }) {
  const [colModule, colData, colRetention] = props.headers
  return (
    <div className="mt-2 overflow-x-auto">
      <table className="w-full min-w-130 border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-muted">
            <th className="py-2 pr-4 font-medium">{colModule}</th>
            <th className="py-2 pr-4 font-medium">{colData}</th>
            <th className="py-2 font-medium">{colRetention}</th>
          </tr>
        </thead>
        <tbody>
          {props.rows.map(([module, data, retention]) => (
            <tr key={module} className="border-b border-border align-top last:border-b-0">
              <td className="whitespace-nowrap py-2 pr-4 text-foreground">{module}</td>
              <td className="py-2 pr-4 text-muted">{data}</td>
              <td className="py-2 text-muted">{retention}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const TABLE_ROW_KEYS = [
  'tickets',
  'invites',
  'supply',
  'voiceRooms',
  'modlog',
  'verification',
  'rating',
  'voiceSessions',
  'audit',
  'streams',
  'events',
  'reactionRoles',
  'economy',
  'wordle',
  'polls',
  'sticky',
  'customCommands',
  'scheduledMessages',
  'timedRoles',
  'birthdays',
  'ownerAlerts',
  'games',
  'news',
  'config',
] as const

export function PrivacyPage() {
  const { lang, t } = useLanguage()

  const tableRows = TABLE_ROW_KEYS.map(
    (key) =>
      [
        t(`privacy.table.${key}.module`),
        t(`privacy.table.${key}.data`),
        t(`privacy.table.${key}.retention`),
      ] as [string, string, string],
  )

  return (
    <PublicLayout>
      <article
        key={`${lang}-privacy`}
        className="animate-fade-in-up mx-auto max-w-3xl rounded-card border border-border bg-surface p-6"
      >
        <h1 className="border-l-2 border-primary pl-3 text-lg font-semibold text-foreground">{t('privacy.title')}</h1>
        <p className="mt-1 pl-3.5 text-xs text-muted">{t('privacy.lastUpdated')}</p>

        <Section title={t('privacy.s1.title')}>
          <p>{t('privacy.s1.p1')}</p>
          <p>{t('privacy.s1.p2')}</p>
          <p>{t('privacy.s1.p3')}</p>
        </Section>

        <Section title={t('privacy.s2.title')}>
          <p>{t('privacy.s2.p1')}</p>
          <ul className="flex list-disc flex-col gap-1 pl-5">
            <li>{t('privacy.s2.li1')}</li>
            <li>{t('privacy.s2.li2')}</li>
            <li>{t('privacy.s2.li3')}</li>
            <li>
              {t('privacy.s2.li4.prefix')}{' '}
              <strong>{t('privacy.s2.li4.bold')}</strong> {t('privacy.s2.li4.suffix')}
            </li>
          </ul>
          <p>{t('privacy.s2.p2')}</p>
          <p>
            <strong>{t('privacy.s2.p3.bold')}</strong>
          </p>

          <p className="mt-2">{t('privacy.s2.p4')}</p>
          <DataTable
            headers={[
              t('privacy.table.colModule'),
              t('privacy.table.colData'),
              t('privacy.table.colRetention'),
            ]}
            rows={tableRows}
          />

          <p className="mt-2">
            2.3. <strong>{t('privacy.s2.p5.label')}</strong> {t('privacy.s2.p5.rest')}
          </p>
        </Section>

        <Section title={t('privacy.s3.title')}>
          <ul className="flex list-disc flex-col gap-1 pl-5">
            <li>{t('privacy.s3.li1')}</li>
            <li>{t('privacy.s3.li2')}</li>
            <li>{t('privacy.s3.li3')}</li>
            <li>{t('privacy.s3.li4')}</li>
            <li>{t('privacy.s3.li5')}</li>
          </ul>
        </Section>

        <Section title={t('privacy.s4.title')}>
          <ul className="flex list-disc flex-col gap-1 pl-5">
            <li>{t('privacy.s4.li1')}</li>
            <li>{t('privacy.s4.li2')}</li>
            <li>{t('privacy.s4.li3')}</li>
            <li>{t('privacy.s4.li4')}</li>
          </ul>
        </Section>

        <Section title={t('privacy.s5.title')}>
          <p>{t('privacy.s5.p1')}</p>
          <p>{t('privacy.s5.p2')}</p>
          <p>{t('privacy.s5.p3')}</p>
        </Section>

        <Section title={t('privacy.s6.title')}>
          <p>{t('privacy.s6.p1')}</p>
        </Section>

        <Section title={t('privacy.s7.title')}>
          <p>
            {t('privacy.s7.p1.prefix')}{' '}
            <a
              href="https://discord.com/privacy"
              target="_blank"
              rel="noreferrer"
              className="text-primary hover:underline"
            >
              {t('privacy.s7.discordPrivacyLink')}
            </a>
            .
          </p>
          <p>{t('privacy.s7.p2')}</p>
          <p>{t('privacy.s7.p3')}</p>
        </Section>

        <Section title={t('privacy.s8.title')}>
          <p>{t('privacy.s8.p1')}</p>
          <ul className="flex list-disc flex-col gap-1 pl-5">
            <li>{t('privacy.s8.li1')}</li>
            <li>{t('privacy.s8.li2')}</li>
            <li>{t('privacy.s8.li3')}</li>
            <li>{t('privacy.s8.li4')}</li>
            <li>{t('privacy.s8.li5')}</li>
            <li>{t('privacy.s8.li6')}</li>
            <li>{t('privacy.s8.li7')}</li>
            <li>{t('privacy.s8.li8')}</li>
          </ul>
          <p>
            8.2. <strong>{t('privacy.s8.p2.label')}</strong> {t('privacy.s8.p2.rest')}
          </p>
        </Section>

        <Section title={t('privacy.s9.title')}>
          <ul className="flex list-disc flex-col gap-1 pl-5">
            <li>{t('privacy.s9.li1')}</li>
            <li>{t('privacy.s9.li2')}</li>
            <li>{t('privacy.s9.li3')}</li>
            <li>{t('privacy.s9.li4')}</li>
          </ul>
        </Section>

        <Section title={t('privacy.s10.title')}>
          <p>{t('privacy.s10.p1')}</p>
        </Section>

        <Section title={t('privacy.s11.title')}>
          <p>{t('privacy.s11.p1')}</p>
        </Section>

        <Section title={t('privacy.s12.title')}>
          <p>{t('privacy.s12.p1')}</p>
        </Section>
      </article>
    </PublicLayout>
  )
}
