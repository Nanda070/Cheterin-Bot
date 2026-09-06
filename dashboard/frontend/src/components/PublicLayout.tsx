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

  const dashboardHref = user ? (user.active_guild_id ? '/' : '/servers') : loginUrl()
  const dashboardIsSpa = dashboardHref.startsWith('/') && !dashboardHref.startsWith('/api')

  return (
    <div className="public flex min-h-dvh flex-col overflow-x-hidden">
      <header className="public-header sticky top-0 z-10 border-b backdrop-blur">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <BrandMark to="/about" iconSize={20} className="shrink-0" />

          <div className="flex min-w-0 items-center gap-2 sm:gap-3">
            <LanguageToggle />
            <nav className="flex min-w-0 flex-wrap items-center justify-end gap-1 sm:gap-2" aria-label="Public">
              <NavLink
                to="/docs"
                className={({ isActive }) =>
                  `rounded-control px-2.5 py-1.5 text-sm transition-colors sm:px-3 ${
                    isActive ? 'bg-primary-muted text-foreground' : 'text-muted hover:bg-surface-hover hover:text-foreground'
                  }`
                }
              >
                {t('nav.docs')}
              </NavLink>
              <a
                href="/lookup/"
                className="rounded-control px-2.5 py-1.5 text-sm text-muted transition-colors hover:bg-surface-hover hover:text-foreground sm:px-3"
              >
                {t('nav.lookup')}
              </a>
              {dashboardIsSpa ? (
                <Link
                  to={dashboardHref}
                  className="rounded-control bg-primary px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-primary-hover"
                >
                  {t('nav.dashboard')}
                </Link>
              ) : (
                <a
                  href={dashboardHref}
                  className="rounded-control bg-primary px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-primary-hover"
                >
                  {t('nav.dashboard')}
                </a>
              )}
            </nav>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:px-6">{children}</main>

      <footer className="public-footer mt-auto border-t">
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-5 px-4 py-7 sm:px-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="flex items-center gap-2 text-sm text-muted">
              <Sparkle size={16} weight="fill" className="shrink-0 text-primary" />
              <span>{t('public.footer')}</span>
            </p>
          </div>
          <nav
            className="flex flex-wrap gap-x-4 gap-y-2 text-sm"
            aria-label="Legal and product links"
          >
            <Link to="/docs" className="transition-colors hover:text-primary">
              {t('nav.docs')}
            </Link>
            <a href="/lookup/" className="transition-colors hover:text-primary">
              {t('public.footer.lookup')}
            </a>
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
