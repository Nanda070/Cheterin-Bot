import type { ReactNode } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { BrandMark, LanguageToggle } from './ui'
import { useT } from '../context/LanguageContext'

const ROOT_LINKS = {
  docs: '/docs',
  about: '/about',
  panel: '/',
  terms: '/terms',
  privacy: '/privacy',
  cookies: '/cookies',
  disclaimer: '/disclaimer',
  credits: '/credits',
} as const

export function LookupLayout({ children }: { children: ReactNode }) {
  const t = useT()

  const nav = [
    { to: '/', label: t('nav.home'), end: true },
    { to: '/about', label: t('nav.about') },
    { to: '/plugins', label: t('nav.plugins') },
  ] as const

  return (
    <div className="lookup-page-bg flex min-h-dvh flex-col">
      <header className="sticky top-0 z-20 border-b border-border/80 bg-background/80 backdrop-blur">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <BrandMark to="/" />
          <div className="flex items-center gap-2 sm:gap-3">
            <LanguageToggle />
            <nav className="hidden items-center gap-1 sm:flex" aria-label="Lookup">
              {nav.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={'end' in item ? item.end : false}
                  className={({ isActive }) =>
                    `rounded-[10px] px-2.5 py-1.5 text-sm transition-colors ${
                      isActive
                        ? 'bg-primary-muted text-foreground'
                        : 'text-muted hover:bg-surface-hover hover:text-foreground'
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              ))}
              <a
                href={ROOT_LINKS.docs}
                className="rounded-[10px] px-2.5 py-1.5 text-sm text-muted transition-colors hover:bg-surface-hover hover:text-foreground"
              >
                {t('nav.docs')}
              </a>
              <a
                href={ROOT_LINKS.about}
                className="rounded-[10px] bg-primary px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-primary-hover"
              >
                {t('nav.botAbout')}
              </a>
            </nav>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">{children}</main>

      <footer className="border-t border-border bg-background/90">
        <div className="mx-auto grid w-full max-w-6xl gap-8 px-4 py-10 sm:px-6 md:grid-cols-[1.4fr_1fr_1fr]">
          <div>
            <BrandMark to="/" />
            <p className="mt-3 max-w-md text-sm leading-relaxed text-muted">{t('footer.tagline')}</p>
            <p className="mt-4 text-xs text-muted">{t('footer.copyright')}</p>
          </div>
          <div>
            <h2 className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">{t('footer.product')}</h2>
            <ul className="mt-3 flex flex-col gap-2 text-sm">
              <li>
                <Link to="/" className="text-foreground/90 hover:text-foreground">
                  {t('nav.home')}
                </Link>
              </li>
              <li>
                <Link to="/about" className="text-foreground/90 hover:text-foreground">
                  {t('nav.about')}
                </Link>
              </li>
              <li>
                <Link to="/plugins" className="text-foreground/90 hover:text-foreground">
                  {t('nav.plugins')}
                </Link>
              </li>
              <li>
                <a href={ROOT_LINKS.docs} className="text-foreground/90 hover:text-foreground">
                  {t('nav.docs')}
                </a>
              </li>
              <li>
                <a href={ROOT_LINKS.panel} className="text-foreground/90 hover:text-foreground">
                  {t('nav.panel')}
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h2 className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">{t('footer.legal')}</h2>
            <ul className="mt-3 flex flex-col gap-2 text-sm">
              <li>
                <a href={ROOT_LINKS.terms} className="text-foreground/90 hover:text-foreground">
                  {t('footer.terms')}
                </a>
              </li>
              <li>
                <a href={ROOT_LINKS.privacy} className="text-foreground/90 hover:text-foreground">
                  {t('footer.privacy')}
                </a>
              </li>
              <li>
                <a href={ROOT_LINKS.cookies} className="text-foreground/90 hover:text-foreground">
                  {t('footer.cookies')}
                </a>
              </li>
              <li>
                <a href={ROOT_LINKS.disclaimer} className="text-foreground/90 hover:text-foreground">
                  {t('footer.disclaimer')}
                </a>
              </li>
              <li>
                <a href={ROOT_LINKS.credits} className="text-foreground/90 hover:text-foreground">
                  {t('footer.credits')}
                </a>
              </li>
            </ul>
          </div>
        </div>
      </footer>
    </div>
  )
}
