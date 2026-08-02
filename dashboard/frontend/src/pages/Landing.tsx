import {
  CalendarCheck,
  ChartBar,
  Coins,
  DiscordLogo,
  Gift,
  Headset,
  House,
  IdentificationBadge,
  Megaphone,
  Package,
  ShieldCheck,
  Sparkle,
  Trophy,
  UsersThree,
  type Icon,
} from '@phosphor-icons/react'
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

/** In-app paths use React Router; `/api/*` and absolute URLs need a real navigation. */
function isSpaPath(href: string): boolean {
  return href.startsWith('/') && !href.startsWith('//') && !href.startsWith('/api')
}

type FeatureDef = {
  id: string
  titleKey: string
  bodyKey: string
  points: [string, string, string]
  icons: Icon[]
  reverse?: boolean
}

const FEATURES: FeatureDef[] = [
  {
    id: 'levels',
    titleKey: 'landing.feature.levels.title',
    bodyKey: 'landing.feature.levels.body',
    points: [
      'landing.feature.levels.point1',
      'landing.feature.levels.point2',
      'landing.feature.levels.point3',
    ],
    icons: [Trophy, ChartBar, Headset],
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
    icons: [Coins, Gift, ChartBar],
    reverse: true,
  },
  {
    id: 'moderation',
    titleKey: 'landing.feature.moderation.title',
    bodyKey: 'landing.feature.moderation.body',
    points: [
      'landing.feature.moderation.point1',
      'landing.feature.moderation.point2',
      'landing.feature.moderation.point3',
    ],
    icons: [ShieldCheck, IdentificationBadge, Megaphone],
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
    icons: [House, UsersThree, IdentificationBadge],
    reverse: true,
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
    icons: [CalendarCheck, Trophy, Gift],
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
    icons: [Megaphone, Headset, Sparkle],
    reverse: true,
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
    icons: [UsersThree, Package, CalendarCheck],
  },
]

function WaveDivider({ className = '', fill = 'var(--color-background)' }: { className?: string; fill?: string }) {
  return (
    <div className={`landing-wave ${className}`} aria-hidden>
      <svg viewBox="0 0 1440 96" preserveAspectRatio="none" className="block h-12 w-full sm:h-16 md:h-20">
        <path
          fill={fill}
          d="M0,64 C240,96 480,16 720,40 C960,64 1200,96 1440,48 L1440,96 L0,96 Z"
        />
      </svg>
    </div>
  )
}

function FeatureVisual({ icons }: { icons: Icon[] }) {
  return (
    <div className="relative mx-auto flex h-56 w-full max-w-md items-center justify-center sm:h-64">
      <div className="absolute inset-6 rounded-[2rem] bg-primary/10 blur-2xl" aria-hidden />
      <div className="relative grid grid-cols-3 gap-3">
        {icons.map((Icon, index) => (
          <div
            key={index}
            className={[
              'landing-feature-glow flex items-center justify-center rounded-2xl border border-border/80 bg-surface/90',
              index === 1 ? 'h-24 w-24 sm:h-28 sm:w-28' : 'h-20 w-20 sm:h-24 sm:w-24',
              index === 0 ? '-translate-y-3' : '',
              index === 2 ? 'translate-y-4' : '',
            ].join(' ')}
          >
            <Icon size={index === 1 ? 40 : 32} weight="duotone" className="text-primary" />
          </div>
        ))}
      </div>
    </div>
  )
}

function FeatureSection({ feature, index }: { feature: FeatureDef; index: number }) {
  const t = useT()
  return (
    <section
      className={[
        'landing-section-in grid items-center gap-10 lg:grid-cols-2 lg:gap-16',
        feature.reverse ? 'lg:[&>*:first-child]:order-2' : '',
      ].join(' ')}
      style={{ animationDelay: `${Math.min(index * 60, 240)}ms` }}
    >
      <div>
        <h3 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">{t(feature.titleKey)}</h3>
        <p className="mt-3 max-w-xl text-base leading-relaxed text-muted">{t(feature.bodyKey)}</p>
        <ul className="mt-5 flex flex-col gap-2.5">
          {feature.points.map((key) => (
            <li key={key} className="flex items-start gap-2.5 text-sm text-foreground/90">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" aria-hidden />
              {t(key)}
            </li>
          ))}
        </ul>
      </div>
      <FeatureVisual icons={feature.icons} />
    </section>
  )
}

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
    'inline-flex items-center justify-center gap-2 rounded-control px-5 py-2.5 text-sm font-semibold transition-all duration-200',
    'landing-cta-ink bg-white shadow-[0_8px_24px_-8px_rgba(0,0,0,0.35)]',
    'hover:bg-white/95 disabled:cursor-wait disabled:opacity-80',
    className,
  ].join(' ')

  if (href) {
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
    'inline-flex items-center justify-center gap-2 rounded-control border border-white/35 bg-white/10 px-5 py-2.5',
    'text-sm font-semibold text-white backdrop-blur-sm transition-colors hover:bg-white/15',
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
      <header className="landing-header sticky top-0 z-20 border-b border-white/10 text-white backdrop-blur">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <BrandMark
            to="/about"
            className="flex items-center gap-2 font-semibold tracking-tight text-white"
            iconClassName="text-white"
            iconSize={22}
          />

          <div className="flex items-center gap-2 sm:gap-3">
            <nav className="hidden items-center gap-1 md:flex">
              <a
                href="#features"
                className="rounded-control px-3 py-1.5 text-sm text-white/85 transition-colors hover:bg-white/10 hover:text-white"
              >
                {t('landing.nav.features')}
              </a>
              <Link
                to="/docs"
                className="rounded-control px-3 py-1.5 text-sm text-white/85 transition-colors hover:bg-white/10 hover:text-white"
              >
                {t('nav.docs')}
              </Link>
            </nav>
            <LanguageToggle className="border-white/20 bg-white/10 [&_button]:text-white/80 [&_button[aria-pressed=true]]:bg-white/20 [&_button[aria-pressed=true]]:text-white" />
            <button
              type="button"
              onClick={() => void openInvite()}
              disabled={inviteBusy}
              className="landing-cta-ink hidden cursor-pointer rounded-control bg-white px-3 py-1.5 text-sm font-semibold transition hover:bg-white/95 disabled:opacity-80 sm:inline-flex"
            >
              {inviteBusy ? t('landing.hero.ctaOpening') : t('landing.nav.addBot')}
            </button>
            <AccountLink
              href={accountHref}
              className="rounded-control border border-white/30 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-white/10"
            >
              {accountLabel}
            </AccountLink>
          </div>
        </div>
      </header>

      <section id="top" className="landing-plane relative overflow-hidden text-white">
        <div
          className="pointer-events-none absolute inset-0 opacity-35"
          style={{
            background:
              'radial-gradient(ellipse 70% 50% at 68% 22%, rgba(255,255,255,0.16), transparent 55%)',
          }}
          aria-hidden
        />

        <div className="landing-hero-in relative mx-auto flex min-h-[min(78vh,720px)] w-full max-w-6xl flex-col justify-center px-4 pb-8 pt-16 sm:px-6 sm:pt-20">
          <p className="text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl">{t('landing.hero.brand')}</p>
          <h1 className="mt-4 max-w-2xl text-2xl font-semibold leading-tight tracking-tight text-white/95 sm:text-3xl md:text-4xl">
            {t('landing.hero.headline')}
          </h1>
          <p className="mt-4 max-w-xl text-base leading-relaxed text-white/80 sm:text-lg">{t('landing.hero.sub')}</p>

          {authErrorKey && (
            <p className="mt-5 max-w-xl rounded-control border border-white/25 bg-black/20 px-3 py-2 text-sm text-white">
              {t(authErrorKey)}
            </p>
          )}
          {inviteError && (
            <p className="mt-5 max-w-xl rounded-control border border-white/25 bg-black/20 px-3 py-2 text-sm text-white">
              {inviteError}
            </p>
          )}

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <PrimaryButton onClick={() => void openInvite()} disabled={inviteBusy}>
              <DiscordLogo size={20} weight="fill" />
              {inviteBusy ? t('landing.hero.ctaOpening') : t('landing.hero.ctaAdd')}
            </PrimaryButton>
            <GhostButton href={accountHref}>
              {heroAccountLabel}
            </GhostButton>
          </div>
        </div>

        <WaveDivider />
      </section>

      <main className="relative z-10 flex-1">
        <div id="features" className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
          <div className="landing-section-in mb-14 max-w-2xl">
            <p className="text-sm font-medium uppercase tracking-[0.14em] text-primary">{t('landing.features.eyebrow')}</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              {t('landing.features.intro')}
            </h2>
          </div>

          <div className="flex flex-col gap-20 sm:gap-24">
            {FEATURES.map((feature, index) => (
              <FeatureSection key={feature.id} feature={feature} index={index} />
            ))}
          </div>
        </div>

        <section className="landing-plane relative overflow-hidden text-white">
          <WaveDivider
            className="rotate-180"
            fill="var(--color-background)"
          />
          <div className="landing-section-in relative mx-auto flex w-full max-w-6xl flex-col items-start gap-6 px-4 py-14 sm:flex-row sm:items-center sm:justify-between sm:px-6 sm:py-16">
            <div className="max-w-xl">
              <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">{t('landing.cta.title')}</h2>
              <p className="mt-2 text-base text-white/80">{t('landing.cta.body')}</p>
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
            <BrandMark to="/about" iconSize={20} />
            <SecretClickTarget clicks={8} to={SECRET_ROOMS.waterfall} className="mt-3 block max-w-xs cursor-default">
              <p className="text-sm leading-relaxed text-muted">{t('landing.footer.tagline')}</p>
            </SecretClickTarget>
            <p className="mt-4 text-xs text-muted">{t('landing.footer.copyright')}</p>
          </div>

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">{t('landing.footer.product')}</h3>
            <ul className="mt-3 flex flex-col gap-2 text-sm">
              <li>
                <a href="#features" className="text-foreground/90 hover:text-foreground">
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
