import { ArrowSquareOut, DiscordLogo, GithubLogo, Sparkle } from '@phosphor-icons/react'
import type { CSSProperties, ReactNode } from 'react'
import { PublicLayout } from '../components/PublicLayout'
import { useLanguage } from '../context/LanguageContext'

const SUPPORT_INVITE = 'https://discord.gg/cheterin'
const GITHUB_PROFILE = 'https://github.com/nanda070'
const GITHUB_ORG = 'https://github.com/orgs/ChetTeam'
const TELEGRAM_NANDA = 'https://t.me/nanda070'
const SERVER_BANNER = '/credits/404-banner.png'

const SERVER_OVERLAY: CSSProperties = {
  background:
    'linear-gradient(105deg, rgba(8,10,14,0.92) 0%, rgba(8,10,14,0.78) 42%, rgba(8,10,14,0.55) 68%, rgba(8,10,14,0.72) 100%), linear-gradient(180deg, rgba(6,8,12,0.55) 0%, rgba(6,8,12,0.35) 40%, rgba(6,8,12,0.75) 100%)',
}

type TeamMember = {
  nameKey: string
  roleKey: string
  discord?: string
  telegram?: string
}

const TEAM: TeamMember[] = [
  {
    nameKey: 'credits.team.nanda.name',
    roleKey: 'credits.team.nanda.role',
    discord: 'nandak070',
    telegram: TELEGRAM_NANDA,
  },
  {
    nameKey: 'credits.team.cheterin.name',
    roleKey: 'credits.team.cheterin.role',
    discord: 'cheterin',
  },
  {
    nameKey: 'credits.team.mark.name',
    roleKey: 'credits.team.mark.role',
    discord: 'schizophrenogenic',
  },
]

type Project = {
  titleKey: string
  bodyKey: string
  href: string
}

const ASTRA_PROJECTS: Project[] = [
  {
    titleKey: 'credits.projects.astrabuild.title',
    bodyKey: 'credits.projects.astrabuild.body',
    href: 'https://github.com/Nanda070/AstraBuild',
  },
  {
    titleKey: 'credits.projects.astraop.title',
    bodyKey: 'credits.projects.astraop.body',
    href: 'https://github.com/Nanda070/AstraOP',
  },
  {
    titleKey: 'credits.projects.astraip.title',
    bodyKey: 'credits.projects.astraip.body',
    href: 'https://github.com/Nanda070/AstraIP',
  },
]

const OTHER_PROJECTS: Project[] = [
  {
    titleKey: 'credits.projects.rpstate.title',
    bodyKey: 'credits.projects.rpstate.body',
    href: 'https://github.com/Nanda070/RP-State',
  },
  {
    titleKey: 'credits.projects.idus.title',
    bodyKey: 'credits.projects.idus.body',
    href: 'https://github.com/Nanda070/IDUS',
  },
]

function SectionHeading(props: { eyebrow?: string; title: string; children?: ReactNode }) {
  return (
    <div className="max-w-2xl">
      {props.eyebrow && (
        <p className="text-sm font-medium uppercase tracking-[0.14em] text-primary">{props.eyebrow}</p>
      )}
      <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">{props.title}</h2>
      {props.children}
    </div>
  )
}

function ExtLink(props: {
  href: string
  className?: string
  style?: CSSProperties
  children: ReactNode
}) {
  return (
    <a
      href={props.href}
      target="_blank"
      rel="noopener noreferrer"
      className={props.className}
      style={props.style}
    >
      {props.children}
    </a>
  )
}

function ProjectCard(props: { project: Project; t: (key: string) => string; delayMs: number }) {
  const { project, t, delayMs } = props
  return (
    <ExtLink
      href={project.href}
      className="group animate-fade-in-up flex flex-col rounded-card border border-border bg-surface p-5 transition-colors hover:border-primary/40 hover:bg-surface-hover"
      style={{ animationDelay: `${delayMs}ms` }}
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-base font-semibold text-foreground">{t(project.titleKey)}</h3>
        <GithubLogo
          size={18}
          weight="fill"
          className="mt-0.5 shrink-0 text-muted transition-colors group-hover:text-primary"
          aria-hidden
        />
      </div>
      <p className="mt-2 flex-1 text-sm leading-relaxed text-muted">{t(project.bodyKey)}</p>
      <span className="mt-4 inline-flex items-center gap-1.5 text-xs font-medium text-primary opacity-90 transition-opacity group-hover:opacity-100">
        {t('credits.projects.openRepo')}
        <ArrowSquareOut size={14} aria-hidden />
      </span>
    </ExtLink>
  )
}

export function CreditsPage() {
  const { lang, t } = useLanguage()

  return (
    <PublicLayout>
      <article key={`${lang}-credits`} className="mx-auto max-w-3xl">
        {/* Hero — one composition, no cards */}
        <header className="landing-hero-in relative overflow-hidden rounded-card border border-border">
          <div
            className="pointer-events-none absolute inset-0 opacity-90"
            style={{
              background:
                'radial-gradient(ellipse 70% 55% at 78% 18%, rgba(196,60,78,0.28), transparent 55%), linear-gradient(165deg, #5c0f1e 0%, #3a0a14 55%, #131722 100%)',
            }}
            aria-hidden
          />
          <div className="relative px-6 py-10 sm:px-8 sm:py-12">
            <p className="flex items-center gap-2 text-sm font-medium uppercase tracking-[0.14em] text-white/70">
              <Sparkle size={16} weight="fill" className="text-white/90" aria-hidden />
              {t('credits.eyebrow')}
            </p>
            <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
              {t('credits.title')}
            </h1>
            <p className="mt-4 max-w-xl text-base leading-relaxed text-white/80 sm:text-lg">
              {t('credits.hero.lead')}
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <ExtLink
                href={GITHUB_PROFILE}
                className="inline-flex items-center gap-2 rounded-control border border-white/25 bg-black/20 px-3.5 py-2 text-sm font-medium text-white transition hover:bg-white/10"
              >
                <GithubLogo size={18} weight="fill" aria-hidden />
                {t('credits.hero.github')}
              </ExtLink>
              <ExtLink
                href={GITHUB_ORG}
                className="inline-flex items-center gap-2 rounded-control border border-white/25 bg-black/20 px-3.5 py-2 text-sm font-medium text-white transition hover:bg-white/10"
              >
                <GithubLogo size={18} weight="fill" aria-hidden />
                {t('credits.hero.org')}
              </ExtLink>
            </div>
          </div>
        </header>

        {/* History */}
        <section className="landing-section-in mt-14">
          <SectionHeading title={t('credits.history.title')} />
          <div className="mt-4 flex flex-col gap-3 text-sm leading-relaxed text-muted sm:text-base">
            <p>{t('credits.history.p1')}</p>
            <p>{t('credits.history.p2')}</p>
          </div>
        </section>

        {/* Home server — first-style card + Pepe banner BG */}
        <section className="landing-section-in mt-14">
          <div className="relative overflow-hidden rounded-card border border-border">
            <div
              className="pointer-events-none absolute inset-0 bg-cover bg-center bg-no-repeat"
              style={{ backgroundImage: `url(${SERVER_BANNER})` }}
              aria-hidden
            />
            <div className="pointer-events-none absolute inset-0" style={SERVER_OVERLAY} aria-hidden />
            <div className="relative p-6 text-white sm:p-7">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-xl font-semibold tracking-tight sm:text-2xl">
                  {t('credits.server.title')}
                </h2>
                <span className="rounded-control bg-white/15 px-2 py-0.5 text-xs font-medium text-white/90">
                  {t('credits.server.badge')}
                </span>
              </div>
              <div className="mt-4 space-y-3 text-sm leading-relaxed text-white/80 sm:text-base">
                <p>{t('credits.server.body')}</p>
                <p>{t('credits.server.body2')}</p>
                <p>{t('credits.server.body3')}</p>
              </div>
              <ExtLink
                href={SUPPORT_INVITE}
                className="mt-5 inline-flex items-center gap-2 rounded-control bg-primary px-3.5 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-hover"
              >
                <DiscordLogo size={18} weight="fill" aria-hidden />
                {t('credits.server.join')}
              </ExtLink>
            </div>
          </div>
        </section>

        {/* Team */}
        <section className="mt-14">
          <SectionHeading title={t('credits.team.title')} />
          <ul className="mt-6 grid gap-3 sm:grid-cols-3">
            {TEAM.map((member, index) => (
              <li
                key={member.nameKey}
                className="animate-fade-in-up flex flex-col rounded-card border border-border bg-surface p-5"
                style={{ animationDelay: `${index * 70}ms` }}
              >
                <p className="text-xs font-medium uppercase tracking-[0.1em] text-primary">
                  {t(member.roleKey)}
                </p>
                <p className="mt-2 text-lg font-semibold text-foreground">{t(member.nameKey)}</p>
                <div className="mt-3 flex flex-col gap-1.5 text-sm text-muted">
                  {member.discord && (
                    <span>
                      <span className="text-muted/80">{t('credits.team.discord')}: </span>
                      <span className="text-foreground/90">{member.discord}</span>
                    </span>
                  )}
                  {member.telegram && (
                    <ExtLink href={member.telegram} className="text-primary hover:text-primary-hover">
                      {t('credits.team.telegram')}
                    </ExtLink>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </section>

        {/* Other projects */}
        <section className="mt-16 pb-4">
          <SectionHeading eyebrow={t('credits.eyebrow')} title={t('credits.projects.title')}>
            <p className="mt-2 text-sm leading-relaxed text-muted sm:text-base">{t('credits.projects.intro')}</p>
          </SectionHeading>

          <p className="mt-8 text-xs font-semibold uppercase tracking-[0.12em] text-muted">
            {t('credits.projects.series.astra')}
          </p>
          <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {ASTRA_PROJECTS.map((project, i) => (
              <ProjectCard key={project.href} project={project} t={t} delayMs={i * 60} />
            ))}
          </div>

          <p className="mt-10 text-xs font-semibold uppercase tracking-[0.12em] text-muted">
            {t('credits.projects.series.bots')}
          </p>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {OTHER_PROJECTS.map((project, i) => (
              <ProjectCard key={project.href} project={project} t={t} delayMs={i * 60} />
            ))}
          </div>
        </section>
      </article>
    </PublicLayout>
  )
}
