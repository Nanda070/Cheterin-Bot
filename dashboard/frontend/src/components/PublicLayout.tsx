import type { ReactNode } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { loginUrl } from '../api/client'
import { BrandMark } from './BrandMark'
import { LanguageToggle } from './LanguageToggle'
import { LookupIcon } from './LookupIcon'
import { useAuth } from '../context/AuthContext'
import { useT } from '../context/LanguageContext'

const SUPPORT_INVITE = 'https://discord.gg/cheterin'

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
                className="inline-flex items-center gap-1.5 rounded-control px-2.5 py-1.5 text-sm text-muted transition-colors hover:bg-surface-hover hover:text-foreground sm:px-3"
              >
                <LookupIcon size={14} className="text-primary" />
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

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">{children}</main>

      <footer className="public-footer mt-auto border-t">
        <div className="mx-auto grid w-full max-w-6xl gap-10 px-4 py-12 sm:px-6 md:grid-cols-[1.4fr_repeat(3,minmax(0,1fr))]">
          <div>
            <BrandMark to="/about" iconSize={20} />
            <p className="mt-3 max-w-xs text-sm leading-relaxed text-muted">{t('landing.footer.tagline')}</p>
            <p className="mt-2 text-xs text-muted">{t('landing.footer.copyright')}</p>
          </div>

          <div>
            <h2 className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">{t('landing.footer.product')}</h2>
            <ul className="mt-3 flex flex-col gap-2 text-sm">
              <li>
                <Link to="/about" className="text-foreground/90 transition-colors hover:text-foreground">
                  Cheterin
                </Link>
              </li>
              <li>
                <Link to="/docs" className="text-foreground/90 transition-colors hover:text-foreground">
                  {t('nav.docs')}
                </Link>
              </li>
              <li>
                <a href="/lookup/" className="text-foreground/90 transition-colors hover:text-foreground">
                  {t('public.footer.lookup')}
                </a>
              </li>
              <li>
                {dashboardIsSpa ? (
                  <Link to={dashboardHref} className="text-foreground/90 transition-colors hover:text-foreground">
                    {t('nav.dashboard')}
                  </Link>
                ) : (
                  <a href={dashboardHref} className="text-foreground/90 transition-colors hover:text-foreground">
                    {t('nav.dashboard')}
                  </a>
                )}
              </li>
            </ul>
          </div>

          <div>
            <h2 className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">{t('landing.footer.legal')}</h2>
            <ul className="mt-3 flex flex-col gap-2 text-sm">
              <li>
                <Link to="/terms" className="text-foreground/90 transition-colors hover:text-foreground">
                  {t('public.footer.terms')}
                </Link>
              </li>
              <li>
                <Link to="/privacy" className="text-foreground/90 transition-colors hover:text-foreground">
                  {t('public.footer.privacy')}
                </Link>
              </li>
              <li>
                <Link to="/cookies" className="text-foreground/90 transition-colors hover:text-foreground">
                  {t('public.footer.cookies')}
                </Link>
              </li>
              <li>
                <Link to="/disclaimer" className="text-foreground/90 transition-colors hover:text-foreground">
                  {t('public.footer.disclaimer')}
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h2 className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">{t('landing.footer.community')}</h2>
            <ul className="mt-3 flex flex-col gap-2 text-sm">
              <li>
                <a
                  href={SUPPORT_INVITE}
                  target="_blank"
                  rel="noreferrer"
                  className="text-foreground/90 transition-colors hover:text-foreground"
                >
                  {t('landing.footer.support')}
                </a>
              </li>
              <li>
                <Link to="/credits" className="text-foreground/90 transition-colors hover:text-foreground">
                  {t('public.footer.credits')}
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </footer>
    </div>
  )
}
