import { Sparkle } from '@phosphor-icons/react'
import type { ReactNode } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { loginUrl } from '../api/client'
import { BrandMark } from './BrandMark'
import { LanguageToggle } from './LanguageToggle'
import { useAuth } from '../context/AuthContext'
import { useT } from '../context/LanguageContext'

export function PublicLayout({ children }: { children: ReactNode }) {
  const t = useT()
  const { user } = useAuth()

  const navLinks = [
    { to: '/docs', labelKey: 'nav.docs' },
    { to: '/terms', labelKey: 'nav.terms' },
    { to: '/privacy', labelKey: 'nav.privacy' },
    { to: '/cookies', labelKey: 'nav.cookies' },
    { to: '/disclaimer', labelKey: 'nav.disclaimer' },
  ] as const

  const dashboardHref = user ? (user.active_guild_id ? '/' : '/servers') : loginUrl()
  const dashboardIsSpa = dashboardHref.startsWith('/') && !dashboardHref.startsWith('/api')

  return (
    <div className="public flex min-h-dvh flex-col">
      <header className="public-header sticky top-0 z-10 border-b backdrop-blur">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <BrandMark to="/about" iconSize={20} />

          <div className="flex items-center gap-2 sm:gap-3">
            <LanguageToggle />
            <nav className="flex items-center gap-1 sm:gap-2">
              {navLinks.map(({ to, labelKey }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    `rounded-control px-2.5 py-1.5 text-sm transition-colors sm:px-3 ${
                      isActive ? 'bg-primary-muted text-foreground' : 'text-muted hover:bg-surface-hover hover:text-foreground'
                    }`
                  }
                >
                  {t(labelKey)}
                </NavLink>
              ))}
              {dashboardIsSpa ? (
                <Link
                  to={dashboardHref}
                  className="ml-1 rounded-control bg-primary px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-primary-hover"
                >
                  {t('nav.dashboard')}
                </Link>
              ) : (
                <a
                  href={dashboardHref}
                  className="ml-1 rounded-control bg-primary px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-primary-hover"
                >
                  {t('nav.dashboard')}
                </a>
              )}
            </nav>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:px-6">{children}</main>

      <footer className="public-footer border-t">
        <div className="mx-auto flex w-full max-w-5xl flex-col items-center justify-between gap-3 px-4 py-6 text-sm text-muted sm:flex-row sm:px-6">
          <p className="flex items-center gap-2">
            <Sparkle size={16} weight="fill" className="text-primary" />
            {t('public.footer')}
          </p>
          <nav className="flex flex-wrap justify-center gap-x-4 gap-y-2">
            <Link to="/docs" className="transition-colors hover:text-primary">
              {t('nav.docs')}
            </Link>
            <Link to="/credits" className="transition-colors hover:text-primary">
              {t('public.footer.credits')}
            </Link>
            <Link to="/terms" className="transition-colors hover:text-primary">
              {t('public.footer.terms')}
            </Link>
            <Link to="/privacy" className="transition-colors hover:text-primary">
              {t('public.footer.privacy')}
            </Link>
            <Link to="/cookies" className="transition-colors hover:text-primary">
              {t('public.footer.cookies')}
            </Link>
            <Link to="/disclaimer" className="transition-colors hover:text-primary">
              {t('public.footer.disclaimer')}
            </Link>
          </nav>
        </div>
      </footer>
    </div>
  )
}
