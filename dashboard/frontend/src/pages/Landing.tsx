import { DiscordLogo } from '@phosphor-icons/react'
import { useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { fetchInviteUrl, loginUrl } from '../api/client'
import { BrandMark } from '../components/BrandMark'
import { LanguageToggle } from '../components/LanguageToggle'
import { SecretClickTarget } from '../components/SecretClickTarget'
import { useAuth } from '../context/AuthContext'
import { useT } from '../context/LanguageContext'
import { SECRET_ROOMS } from '../utils/easterEggs'

const SUPPORT_INVITE = 'https://discord.gg/cheterin'

/** Dashboard SPA paths use React Router; `/lookup` and `/api/*` need a full navigation. */
function isSpaPath(href: string): boolean {
  return (
    href.startsWith('/') &&
    !href.startsWith('//') &&
    !href.startsWith('/api') &&
    !href.startsWith('/lookup')
  )
}

type FeatureDef = {
  id: string
  titleKey: string
  bodyKey: string
  points: [string, string, string]
}

const FEATURES: FeatureDef[] = [
  {
    id: 'moderation',
    titleKey: 'landing.feature.moderation.title',
    bodyKey: 'landing.feature.moderation.body',
    points: [
      'landing.feature.moderation.point1',
      'landing.feature.moderation.point2',
      'landing.feature.moderation.point3',
    ],
  },
  {
    id: 'levels',
    titleKey: 'landing.feature.levels.title',
    bodyKey: 'landing.feature.levels.body',
    points: [
      'landing.feature.levels.point1',
      'landing.feature.levels.point2',
      'landing.feature.levels.point3',
    ],
  },
  {
    id: 'welcome',
    titleKey: 'landing.feature.welcome.title',
    bodyKey: 'landing.feature.welcome.body',
    points: [
      'landing.feature.welcome.point1',
      'landing.feature.welcome.point2',
      'landing.feature.welcome.point3',
    ],
  },
  {
    id: 'economy',
    titleKey: 'landing.feature.economy.title',
    bodyKey: 'landing.feature.economy.body',
    points: [
      'landing.feature.economy.point1',
      'landing.feature.economy.point2',
      'landing.feature.economy.point3',
    ],
  },
  {
    id: 'events',
    titleKey: 'landing.feature.events.title',
    bodyKey: 'landing.feature.events.body',
    points: [
      'landing.feature.events.point1',
      'landing.feature.events.point2',
      'landing.feature.events.point3',
    ],
  },
  {
    id: 'valorant',
    titleKey: 'landing.feature.valorant.title',
    bodyKey: 'landing.feature.valorant.body',
    points: [
      'landing.feature.valorant.point1',
      'landing.feature.valorant.point2',
      'landing.feature.valorant.point3',
    ],
  },
  {
    id: 'gta',
    titleKey: 'landing.feature.gta.title',
    bodyKey: 'landing.feature.gta.body',
    points: [
      'landing.feature.gta.point1',
      'landing.feature.gta.point2',
      'landing.feature.gta.point3',
    ],
  },
  {
    id: 'games',
    titleKey: 'landing.feature.games.title',
    bodyKey: 'landing.feature.games.body',
    points: [
      'landing.feature.games.point1',
      'landing.feature.games.point2',
      'landing.feature.games.point3',
    ],
  },
  {
    id: 'messages',
    titleKey: 'landing.feature.messages.title',
    bodyKey: 'landing.feature.messages.body',
    points: [
      'landing.feature.messages.point1',
      'landing.feature.messages.point2',
      'landing.feature.messages.point3',
    ],
  },
]

const START_STEPS = [
  { titleKey: 'landing.start.step1.title', bodyKey: 'landing.start.step1.body' },
  { titleKey: 'landing.start.step2.title', bodyKey: 'landing.start.step2.body' },
  { titleKey: 'landing.start.step3.title', bodyKey: 'landing.start.step3.body' },
] as const

function PrimaryButton({
  children,
  onClick,
  href,
  disabled,
  className = '',
}: {
  children: ReactNode
  onClick?: () => void
  href?: string
  disabled?: boolean
  className?: string
}) {
  const base = [
    'inline-flex items-center justify-center gap-2 rounded-control px-5 py-2.5 text-sm font-semibold',
    'bg-primary text-white transition-colors duration-200 hover:bg-primary-hover',
    'disabled:cursor-wait disabled:opacity-80',
    className,
  ].join(' ')

  if (href) {
    if (isSpaPath(href)) {
      return (
        <Link to={href} className={base}>
          {children}
        </Link>
      )
    }
    return (
      <a href={href} className={base}>
        {children}
      </a>
    )
  }

  return (
    <button type="button" onClick={onClick} disabled={disabled} className={['cursor-pointer', base].join(' ')}>
      {children}
    </button>
  )
}

function GhostButton({
  children,
  href,
  className = '',
}: {
  children: ReactNode
  href: string
  className?: string
}) {
  const classNames = [
    'inline-flex items-center justify-center gap-2 rounded-control border border-border bg-transparent px-5 py-2.5',
    'text-sm font-semibold text-foreground transition-colors hover:border-primary/50 hover:bg-primary-muted',
    className,
  ].join(' ')

  if (isSpaPath(href)) {
    return (
      <Link to={href} className={classNames}>
        {children}
      </Link>
    )
  }

  return (
    <a href={href} className={classNames}>
      {children}
    </a>
  )
}

function AccountLink({
  href,
  children,
  className,
}: {
  href: string
  children: ReactNode
  className: string
}) {
  if (isSpaPath(href)) {
    return (
      <Link to={href} className={className}>
        {children}
      </Link>
    )
  }
  return (
    <a href={href} className={className}>
      {children}
    </a>
  )
}

function FeatureRow({ feature, index }: { feature: FeatureDef; index: number }) {
  const t = useT()
  const n = String(index + 1).padStart(2, '0')

  return (
    <article
      className="landing-section-in landing-module border-t border-border/80 py-10 sm:py-12"
      style={{ animationDelay: `${Math.min(index * 50, 280)}ms` }}
    >
      <div className="grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:gap-14">
        <div>
          <p className="landing-display text-xs font-semibold tracking-[0.2em] text-primary/80">{n}</p>
          <h3 className="landing-display mt-2 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            {t(feature.titleKey)}
          </h3>
        </div>
        <div>
          <p className="max-w-xl text-base leading-relaxed text-muted">{t(feature.bodyKey)}</p>
          <ul className="mt-5 flex flex-col gap-2.5">
            {feature.points.map((key) => (
              <li key={key} className="flex items-start gap-3 text-sm text-foreground/90">
                <span className="mt-2 h-px w-4 shrink-0 bg-primary" aria-hidden />
                {t(key)}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </article>
  )
}

export function LandingPage({ authErrorKey }: { authErrorKey?: string }) {
  const t = useT()
  const { user } = useAuth()
  const [inviteBusy, setInviteBusy] = useState(false)
  const [inviteError, setInviteError] = useState('')

  const accountHref = user ? (user.active_guild_id ? '/' : '/servers') : loginUrl()
  const accountLabel = user ? t('landing.nav.myServers') : t('landing.nav.signIn')
  const heroAccountLabel = user ? t('landing.nav.myServers') : t('landing.hero.ctaSignIn')
  const dashboardHref = accountHref
  const dashboardLabel = user ? t('landing.nav.myServers') : t('nav.dashboard')

  const openInvite = async () => {
    setInviteBusy(true)
    setInviteError('')
    try {
      const url = await fetchInviteUrl()
      window.open(url, '_blank', 'noopener,noreferrer')
    } catch {
      setInviteError(t('landing.hero.inviteError'))
    } finally {
      setInviteBusy(false)
    }
  }

  return (
    <div className="landing flex min-h-dvh flex-col bg-background text-foreground">
      <header className="landing-header sticky top-0 z-20 border-b border-border/80 text-foreground backdrop-blur">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <BrandMark
            to="/about"
            className="landing-display flex items-center gap-2 font-bold tracking-tight text-foreground"
            iconClassName="text-primary"
            iconSize={22}
          />

          <div className="flex items-center gap-2 sm:gap-3">
            <nav className="hidden items-center gap-1 md:flex" aria-label="About">
              <a
                href="#modules"
                className="rounded-control px-3 py-1.5 text-sm text-muted transition-colors hover:bg-surface-hover hover:text-foreground"
              >
                {t('landing.nav.features')}
              </a>
              <Link
                to="/docs"
                className="rounded-control px-3 py-1.5 text-sm text-muted transition-colors hover:bg-surface-hover hover:text-foreground"
              >
                {t('nav.docs')}
              </Link>
              <a
                href="/lookup/"
                className="rounded-control px-3 py-1.5 text-sm text-muted transition-colors hover:bg-surface-hover hover:text-foreground"
              >
                {t('landing.nav.lookup')}
              </a>
            </nav>
            <LanguageToggle />
            <button
              type="button"
              onClick={() => void openInvite()}
              disabled={inviteBusy}
              className="hidden cursor-pointer rounded-control bg-primary px-3 py-1.5 text-sm font-semibold text-white transition hover:bg-primary-hover disabled:opacity-80 sm:inline-flex"
            >
              {inviteBusy ? t('landing.hero.ctaOpening') : t('landing.nav.addBot')}
            </button>
            <AccountLink
              href={accountHref}
              className="rounded-control border border-border px-3 py-1.5 text-sm font-medium text-foreground transition hover:bg-surface-hover"
            >
              {accountLabel}
            </AccountLink>
          </div>
        </div>
      </header>

      <section id="top" className="landing-atmosphere relative overflow-hidden">
        <div className="landing-glow pointer-events-none absolute -left-1/4 top-0 h-[70%] w-[70%] rounded-full bg-primary/10 blur-3xl" aria-hidden />
        <div className="landing-glow-delay pointer-events-none absolute -right-1/5 bottom-0 h-[55%] w-[55%] rounded-full bg-primary-deep/40 blur-3xl" aria-hidden />

        <div className="relative mx-auto flex min-h-[min(88vh,820px)] w-full max-w-6xl flex-col justify-center px-4 pb-16 pt-20 sm:px-6 sm:pb-20 sm:pt-24">
          <p className="landing-hero-in landing-display text-[clamp(3.25rem,12vw,7.5rem)] font-extrabold leading-[0.92] tracking-tight text-foreground">
            {t('landing.hero.brand')}
          </p>
          <h1
            className="landing-hero-in mt-6 max-w-2xl text-xl font-semibold leading-snug tracking-tight text-foreground/95 sm:text-2xl md:text-3xl"
            style={{ animationDelay: '90ms' }}
          >
            {t('landing.hero.headline')}
          </h1>
          <p
            className="landing-hero-in mt-4 max-w-xl text-base leading-relaxed text-muted sm:text-lg"
            style={{ animationDelay: '160ms' }}
          >
            {t('landing.hero.sub')}
          </p>

          {authErrorKey && (
            <p className="mt-5 max-w-xl rounded-control border border-border bg-surface px-3 py-2 text-sm text-foreground">
              {t(authErrorKey)}
            </p>
          )}
          {inviteError && (
            <p className="mt-5 max-w-xl rounded-control border border-border bg-surface px-3 py-2 text-sm text-foreground">
              {inviteError}
            </p>
          )}

          <div className="landing-hero-in mt-9 flex flex-wrap items-center gap-3" style={{ animationDelay: '240ms' }}>
            <PrimaryButton onClick={() => void openInvite()} disabled={inviteBusy}>
              <DiscordLogo size={20} weight="fill" />
              {inviteBusy ? t('landing.hero.ctaOpening') : t('landing.hero.ctaAdd')}
            </PrimaryButton>
            <GhostButton href={accountHref}>{heroAccountLabel}</GhostButton>
            <GhostButton href="/lookup/">{t('landing.hero.ctaLookup')}</GhostButton>
          </div>
        </div>
      </section>

      <main className="relative z-10 flex-1">
        <section className="border-t border-border/80">
          <div className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
            <div className="landing-section-in max-w-2xl">
              <p className="text-sm font-medium uppercase tracking-[0.16em] text-primary">{t('landing.start.eyebrow')}</p>
              <h2 className="landing-display mt-3 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                {t('landing.start.title')}
              </h2>
            </div>

            <ol className="mt-12 grid gap-10 sm:grid-cols-3 sm:gap-8">
              {START_STEPS.map((step, index) => (
                <li
                  key={step.titleKey}
                  className="landing-section-in"
                  style={{ animationDelay: `${120 + index * 80}ms` }}
                >
                  <p className="landing-display text-sm font-semibold tracking-[0.18em] text-primary">
                    {String(index + 1).padStart(2, '0')}
                  </p>
                  <h3 className="landing-display mt-3 text-lg font-bold text-foreground">{t(step.titleKey)}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted">{t(step.bodyKey)}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section id="modules" className="border-t border-border/80">
          <div className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
            <div className="landing-section-in mb-4 max-w-2xl">
              <p className="text-sm font-medium uppercase tracking-[0.16em] text-primary">{t('landing.features.eyebrow')}</p>
              <h2 className="landing-display mt-3 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                {t('landing.features.intro')}
              </h2>
            </div>

            <div>
              {FEATURES.map((feature, index) => (
                <FeatureRow key={feature.id} feature={feature} index={index} />
              ))}
            </div>
          </div>
        </section>

        <section id="lookup" className="landing-lookup-band border-y border-border/80">
          <div className="landing-section-in mx-auto flex w-full max-w-6xl flex-col items-start gap-6 px-4 py-14 sm:flex-row sm:items-end sm:justify-between sm:px-6 sm:py-16">
            <div className="max-w-xl">
              <p className="text-sm font-medium uppercase tracking-[0.16em] text-primary">{t('landing.lookup.eyebrow')}</p>
              <h2 className="landing-display mt-3 text-2xl font-bold tracking-tight sm:text-3xl">{t('landing.lookup.title')}</h2>
              <p className="mt-3 text-base leading-relaxed text-muted">{t('landing.lookup.body')}</p>
            </div>
            <PrimaryButton href="/lookup/">{t('landing.lookup.cta')}</PrimaryButton>
          </div>
        </section>

        <section className="landing-atmosphere relative overflow-hidden">
          <div className="landing-section-in relative mx-auto flex w-full max-w-6xl flex-col items-start gap-6 px-4 py-14 sm:flex-row sm:items-center sm:justify-between sm:px-6 sm:py-16">
            <div className="max-w-xl">
              <h2 className="landing-display text-2xl font-bold tracking-tight sm:text-3xl">{t('landing.cta.title')}</h2>
              <p className="mt-2 text-base text-muted">{t('landing.cta.body')}</p>
            </div>
            <div className="flex flex-wrap gap-3">
              <PrimaryButton onClick={() => void openInvite()} disabled={inviteBusy}>
                <DiscordLogo size={20} weight="fill" />
                {inviteBusy ? t('landing.hero.ctaOpening') : t('landing.cta.add')}
              </PrimaryButton>
              <GhostButton href="/docs">{t('landing.cta.docs')}</GhostButton>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-border bg-background">
        <div className="mx-auto grid w-full max-w-6xl gap-10 px-4 py-12 sm:px-6 md:grid-cols-[1.4fr_repeat(3,minmax(0,1fr))]">
          <div>
            <BrandMark to="/about" iconSize={20} className="landing-display flex items-center gap-2 font-bold tracking-tight" />
            <SecretClickTarget clicks={8} to={SECRET_ROOMS.waterfall} className="mt-3 block max-w-xs cursor-default">
              <p className="text-sm leading-relaxed text-muted">{t('landing.footer.tagline')}</p>
            </SecretClickTarget>
            <p className="mt-3 text-xs text-muted">{t('landing.footer.langs')}</p>
            <p className="mt-2 text-xs text-muted">{t('landing.footer.copyright')}</p>
          </div>

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">{t('landing.footer.product')}</h3>
            <ul className="mt-3 flex flex-col gap-2 text-sm">
              <li>
                <a href="#modules" className="text-foreground/90 hover:text-foreground">
                  {t('landing.nav.features')}
                </a>
              </li>
              <li>
                <Link to="/docs" className="text-foreground/90 hover:text-foreground">
                  {t('nav.docs')}
                </Link>
              </li>
              <li>
                <Link to="/credits" className="text-foreground/90 hover:text-foreground">
                  {t('nav.credits')}
                </Link>
              </li>
              <li>
                <a href="/lookup/" className="text-foreground/90 hover:text-foreground">
                  {t('landing.nav.lookup')}
                </a>
              </li>
              <li>
                <AccountLink href={dashboardHref} className="text-foreground/90 hover:text-foreground">
                  {dashboardLabel}
                </AccountLink>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">{t('landing.footer.legal')}</h3>
            <ul className="mt-3 flex flex-col gap-2 text-sm">
              <li>
                <Link to="/terms" className="text-foreground/90 hover:text-foreground">
                  {t('nav.terms')}
                </Link>
              </li>
              <li>
                <Link to="/privacy" className="text-foreground/90 hover:text-foreground">
                  {t('nav.privacy')}
                </Link>
              </li>
              <li>
                <Link to="/cookies" className="text-foreground/90 hover:text-foreground">
                  {t('nav.cookies')}
                </Link>
              </li>
              <li>
                <Link to="/disclaimer" className="text-foreground/90 hover:text-foreground">
                  {t('nav.disclaimer')}
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">{t('landing.footer.community')}</h3>
            <ul className="mt-3 flex flex-col gap-2 text-sm">
              <li>
                <a
                  href={SUPPORT_INVITE}
                  target="_blank"
                  rel="noreferrer"
                  className="text-foreground/90 hover:text-foreground"
                >
                  {t('landing.footer.support')}
                </a>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => void openInvite()}
                  className="cursor-pointer text-left text-foreground/90 hover:text-foreground"
                >
                  {t('landing.nav.addBot')}
                </button>
              </li>
            </ul>
          </div>
        </div>
      </footer>
    </div>
  )
}
