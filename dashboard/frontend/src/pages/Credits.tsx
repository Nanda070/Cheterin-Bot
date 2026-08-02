import {
  ArrowSquareOut,
  DiscordLogo,
  EnvelopeSimple,
  GithubLogo,
  Globe,
  Phone,
  Sparkle,
  TelegramLogo,
} from '@phosphor-icons/react'
import { useState, type CSSProperties, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { PublicLayout } from '../components/PublicLayout'
import { useLanguage } from '../context/LanguageContext'
import { SECRET_ROOMS } from '../utils/easterEggs'

const SUPPORT_INVITE = 'https://discord.gg/cheterin'
const GITHUB_PROFILE = 'https://github.com/nanda070'
const GITHUB_ORG = 'https://github.com/orgs/ChetTeam'
const TELEGRAM_NANDA = 'https://t.me/nanda070'
const SERVER_BANNER = '/credits/404-banner.png'
const NANDA_EMAIL = 'adnan.huseynli1@gmail.com'
const NANDA_PHONE = '+41-77-259-9608'
const NANDA_DISCORD = 'nandak070'

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
    discord: NANDA_DISCORD,
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
  kind: 'github' | 'web'
}

const ASTRA_PROJECTS: Project[] = [
  {
    titleKey: 'credits.projects.astrabuild.title',
    bodyKey: 'credits.projects.astrabuild.body',
    href: 'https://github.com/Nanda070/AstraBuild',
    kind: 'github',
  },
  {
    titleKey: 'credits.projects.astraop.title',
    bodyKey: 'credits.projects.astraop.body',
    href: 'https://github.com/Nanda070/AstraOP',
    kind: 'github',
  },
  {
    titleKey: 'credits.projects.astraip.title',
    bodyKey: 'credits.projects.astraip.body',
    href: 'https://github.com/Nanda070/AstraIP',
    kind: 'github',
  },
]

const OTHER_PROJECTS: Project[] = [
  {
    titleKey: 'credits.projects.rpstate.title',
    bodyKey: 'credits.projects.rpstate.body',
    href: 'https://github.com/Nanda070/RP-State',
    kind: 'github',
  },
  {
    titleKey: 'credits.projects.idus.title',
    bodyKey: 'credits.projects.idus.body',
    href: 'https://github.com/Nanda070/IDUS',
    kind: 'github',
  },
  {
    titleKey: 'credits.projects.nandaSite.title',
    bodyKey: 'credits.projects.nandaSite.body',
    href: 'https://nanda070.github.io/nanda.com/',
    kind: 'web',
  },
  {
    titleKey: 'credits.projects.yanPro.title',
    bodyKey: 'credits.projects.yanPro.body',
    href: 'https://yan-pro.shop/',
    kind: 'web',
  },
  {
    titleKey: 'credits.projects.sorfa.title',
    bodyKey: 'credits.projects.sorfa.body',
    href: 'https://sorfa.vercel.app/',
    kind: 'web',
  },
  {
    titleKey: 'credits.projects.pepegaGo.title',
    bodyKey: 'credits.projects.pepegaGo.body',
    href: 'https://github.com/Nanda070/PepegaGo',
    kind: 'github',
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

function ProjectRow(props: { project: Project; t: (key: string) => string; delayMs: number }) {
  const { project, t, delayMs } = props
  const Icon = project.kind === 'web' ? Globe : GithubLogo
  return (
    <li
      className="animate-fade-in-up border-b border-border/70 last:border-b-0"
      style={{ animationDelay: `${delayMs}ms` }}
    >
      <ExtLink
        href={project.href}
        className="group flex items-start gap-4 py-4 transition-colors hover:bg-white/[0.02] sm:gap-5"
      >
        <span className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
          <Icon size={18} weight="fill" aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-baseline justify-between gap-3">
            <h3 className="text-base font-semibold text-foreground group-hover:text-primary">
              {t(project.titleKey)}
            </h3>
            <ArrowSquareOut
              size={16}
              className="shrink-0 text-muted opacity-0 transition-opacity group-hover:opacity-100"
              aria-hidden
            />
          </div>
          <p className="mt-1 text-sm leading-relaxed text-muted">{t(project.bodyKey)}</p>
          <span className="mt-2 inline-block text-xs font-medium text-primary/90">
            {project.kind === 'web' ? t('credits.projects.openSite') : t('credits.projects.openRepo')}
          </span>
        </div>
      </ExtLink>
    </li>
  )
}

export function CreditsPage() {
  const { lang, t } = useLanguage()
  const [alsoOpen, setAlsoOpen] = useState(false)
  const [tobyNope, setTobyNope] = useState(false)

  return (
    <PublicLayout>
      <article key={`${lang}-credits`} className="mx-auto max-w-3xl">
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

        <section className="landing-section-in mt-14">
          <SectionHeading title={t('credits.history.title')} />
          <div className="mt-4 flex flex-col gap-3 text-sm leading-relaxed text-muted sm:text-base">
            <p>{t('credits.history.p1')}</p>
            <p>{t('credits.history.p2')}</p>
          </div>
        </section>

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

        {/* Team — stacked rows, no cards */}
        <section className="mt-14">
          <SectionHeading title={t('credits.team.title')} />
          <ul className="mt-8 divide-y divide-border/80 border-y border-border/80">
            {TEAM.map((member, index) => (
              <li
                key={member.nameKey}
                className="animate-fade-in-up flex flex-col gap-3 py-6 sm:flex-row sm:items-end sm:justify-between"
                style={{ animationDelay: `${index * 70}ms` }}
              >
                <div className="min-w-0">
                  <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-primary/90">
                    {t(member.roleKey)}
                  </p>
                  <p className="mt-2 text-3xl font-bold tracking-[-0.03em] text-foreground sm:text-4xl">
                    <span className="relative inline-block pb-1">
                      {t(member.nameKey)}
                      <span
                        className="absolute bottom-0 left-0 h-[3px] w-[min(100%,4.75rem)] rounded-full bg-primary"
                        aria-hidden
                      />
                    </span>
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted">
                  {member.discord && (
                    <span className="inline-flex items-center gap-1.5">
                      <DiscordLogo size={16} weight="fill" className="text-primary/80" aria-hidden />
                      <span className="text-foreground/90">{member.discord}</span>
                    </span>
                  )}
                  {member.telegram && (
                    <ExtLink
                      href={member.telegram}
                      className="inline-flex items-center gap-1.5 text-primary hover:text-primary-hover"
                    >
                      <TelegramLogo size={16} weight="fill" aria-hidden />
                      {t('credits.team.telegram')}
                    </ExtLink>
                  )}
                </div>
              </li>
            ))}
          </ul>

          <div className="mt-8 border-t border-border/60 pt-6">
            {!alsoOpen ? (
              <button
                type="button"
                onClick={() => setAlsoOpen(true)}
                className="text-sm text-muted/70 transition hover:text-muted"
                title={t('egg.credits.teaserHint')}
              >
                {t('egg.credits.teaser')}
              </button>
            ) : (
              <div className="animate-fade-in-up space-y-4">
                <h3 className="text-sm font-semibold uppercase tracking-[0.14em] text-primary/90">
                  {t('egg.credits.alsoTitle')}
                </h3>
                <ul className="space-y-2 text-sm text-muted">
                  <li>{t('egg.credits.coffee')}</li>
                  <li>{t('egg.credits.sleep')}</li>
                  <li>{t('egg.credits.git')}</li>
                  <li>{t('egg.credits.test')}</li>
                  <li>
                    <button
                      type="button"
                      className="text-left text-muted transition hover:text-foreground"
                      onClick={() => setTobyNope(true)}
                    >
                      {tobyNope ? t('egg.credits.tobyNope') : t('egg.credits.toby')}
                    </button>
                  </li>
                </ul>
                <p className="pt-2 text-xs font-medium uppercase tracking-[0.12em] text-muted">
                  {t('egg.credits.doors')}
                </p>
                <ul className="flex flex-wrap gap-3 text-sm">
                  <li>
                    <Link to={SECRET_ROOMS.snowdin} className="text-primary hover:text-primary-hover">
                      {t('egg.credits.snowdin')}
                    </Link>
                  </li>
                  <li>
                    <Link to={SECRET_ROOMS.waterfall} className="text-primary hover:text-primary-hover">
                      {t('egg.credits.waterfall')}
                    </Link>
                  </li>
                  <li>
                    <Link to={SECRET_ROOMS.core} className="text-primary hover:text-primary-hover">
                      {t('egg.credits.core')}
                    </Link>
                  </li>
                  <li>
                    <Link to={SECRET_ROOMS.judgment} className="text-primary hover:text-primary-hover">
                      {t('egg.credits.judgment')}
                    </Link>
                  </li>
                </ul>
              </div>
            )}
          </div>
        </section>

        {/* Contact */}
        <section className="landing-section-in mt-14">
          <SectionHeading title={t('credits.contact.title')}>
            <p className="mt-2 text-sm leading-relaxed text-muted sm:text-base">{t('credits.contact.intro')}</p>
          </SectionHeading>
          <div className="mt-6 border-l-2 border-primary pl-5">
            <p className="text-lg font-semibold text-foreground">{t('credits.contact.name')}</p>
            <ul className="mt-4 flex flex-col gap-3 text-sm">
              <li>
                <a
                  href={`mailto:${NANDA_EMAIL}`}
                  className="inline-flex items-center gap-2.5 text-muted transition-colors hover:text-primary"
                >
                  <EnvelopeSimple size={18} className="text-primary" aria-hidden />
                  <span>
                    <span className="text-muted/80">{t('credits.contact.email')}: </span>
                    <span className="text-foreground">{NANDA_EMAIL}</span>
                  </span>
                </a>
              </li>
              <li>
                <a
                  href={`tel:${NANDA_PHONE.replace(/-/g, '')}`}
                  className="inline-flex items-center gap-2.5 text-muted transition-colors hover:text-primary"
                >
                  <Phone size={18} className="text-primary" aria-hidden />
                  <span>
                    <span className="text-muted/80">{t('credits.contact.phone')}: </span>
                    <span className="text-foreground">{NANDA_PHONE}</span>
                  </span>
                </a>
              </li>
              <li className="inline-flex items-center gap-2.5 text-muted">
                <DiscordLogo size={18} weight="fill" className="text-primary" aria-hidden />
                <span>
                  <span className="text-muted/80">{t('credits.contact.discord')}: </span>
                  <span className="text-foreground">{NANDA_DISCORD}</span>
                </span>
              </li>
              <li>
                <ExtLink
                  href={TELEGRAM_NANDA}
                  className="inline-flex items-center gap-2.5 text-muted transition-colors hover:text-primary"
                >
                  <TelegramLogo size={18} weight="fill" className="text-primary" aria-hidden />
                  <span>
                    <span className="text-muted/80">{t('credits.contact.telegram')}: </span>
                    <span className="text-foreground">nanda070</span>
                  </span>
                </ExtLink>
              </li>
            </ul>
          </div>
        </section>

        {/* Projects — list rows */}
        <section className="mt-16 pb-4">
          <SectionHeading eyebrow={t('credits.eyebrow')} title={t('credits.projects.title')}>
            <p className="mt-2 text-sm leading-relaxed text-muted sm:text-base">{t('credits.projects.intro')}</p>
          </SectionHeading>

          <p className="mt-10 text-xs font-semibold uppercase tracking-[0.12em] text-muted">
            {t('credits.projects.series.astra')}
          </p>
          <ul className="mt-1">
            {ASTRA_PROJECTS.map((project, i) => (
              <ProjectRow key={project.href} project={project} t={t} delayMs={i * 50} />
            ))}
          </ul>

          <p className="mt-10 text-xs font-semibold uppercase tracking-[0.12em] text-muted">
            {t('credits.projects.series.bots')}
          </p>
          <ul className="mt-1">
            {OTHER_PROJECTS.map((project, i) => (
              <ProjectRow key={project.href} project={project} t={t} delayMs={i * 50} />
            ))}
          </ul>
        </section>
      </article>
    </PublicLayout>
  )
}
