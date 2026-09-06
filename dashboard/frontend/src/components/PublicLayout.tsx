import type { ReactNode } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { loginUrl } from '../api/client'
import { BrandMark } from './BrandMark'
import { LanguageToggle } from './LanguageToggle'
import { LookupIcon } from './LookupIcon'
import { SiteFooter } from './SiteFooter'
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
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
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
                className="inline-flex items-center gap-1 rounded-control px-2.5 py-1.5 text-sm text-muted transition-colors hover:bg-surface-hover hover:text-foreground sm:px-3"
              >
                <LookupIcon size={14} className="shrink-0 text-primary" />
                <span>{t('nav.lookup')}</span>
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

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">{children}</main>

      <SiteFooter />
    </div>
  )
}
