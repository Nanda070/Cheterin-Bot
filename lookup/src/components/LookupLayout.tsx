import { useState, type ReactNode } from 'react'
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
  const [menuOpen, setMenuOpen] = useState(false)

  const nav = [
    { to: '/', label: t('nav.home'), end: true },
    { to: '/about', label: t('nav.about') },
    { to: '/plugins', label: t('nav.plugins') },
  ] as const

  const closeMenu = () => setMenuOpen(false)

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `rounded-[10px] px-2.5 py-1.5 text-sm transition-colors ${
      isActive
        ? 'bg-primary-muted text-foreground'
        : 'text-muted hover:bg-surface-hover hover:text-foreground'
    }`

  return (
    <div className="lookup-page-bg flex min-h-dvh flex-col">
      <header className="sticky top-0 z-20 border-b border-border/70 bg-background/85 backdrop-blur-md">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-3 px-4 py-3.5 sm:px-6">
          <BrandMark to="/" />
          <div className="flex items-center gap-2 sm:gap-3">
            <LanguageToggle />
            <nav className="hidden items-center gap-0.5 md:flex" aria-label="Lookup">
              {nav.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={'end' in item ? item.end : false}
                  className={linkClass}
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
                className="ml-1 rounded-[10px] bg-primary px-3.5 py-1.5 text-sm font-semibold text-white transition-colors hover:bg-primary-hover"
              >
                {t('nav.botAbout')}
              </a>
            </nav>
            <button
              type="button"
              className="inline-flex h-9 cursor-pointer items-center justify-center rounded-[10px] border border-border bg-surface px-2.5 text-xs font-medium text-foreground transition-colors hover:bg-surface-hover md:hidden"
              aria-expanded={menuOpen}
              aria-controls="lookup-mobile-nav"
              aria-label={menuOpen ? t('nav.close') : t('nav.menu')}
              onClick={() => setMenuOpen((v) => !v)}
            >
              {menuOpen ? t('nav.close') : t('nav.menu')}
            </button>
          </div>
        </div>

        {menuOpen ? (
          <div id="lookup-mobile-nav" className="border-t border-border/70 bg-background/95 px-4 py-3 md:hidden">
            <nav className="mx-auto flex w-full max-w-6xl flex-col gap-1" aria-label="Lookup mobile">
              {nav.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={'end' in item ? item.end : false}
                  onClick={closeMenu}
                  className={({ isActive }) =>
                    `rounded-[10px] px-3 py-2.5 text-sm transition-colors ${
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
                onClick={closeMenu}
                className="rounded-[10px] px-3 py-2.5 text-sm text-muted hover:bg-surface-hover hover:text-foreground"
              >
                {t('nav.docs')}
              </a>
              <a
                href={ROOT_LINKS.about}
                onClick={closeMenu}
                className="mt-1 rounded-[10px] bg-primary px-3 py-2.5 text-center text-sm font-semibold text-white hover:bg-primary-hover"
              >
                {t('nav.botAbout')}
              </a>
            </nav>
          </div>
        ) : null}
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-9 sm:px-6 sm:py-11">{children}</main>

      <footer className="mt-auto border-t border-border bg-background-deep/90">
        <div className="mx-auto grid w-full max-w-6xl gap-10 px-4 py-12 sm:px-6 md:grid-cols-[1.55fr_1fr_1fr]">
          <div>
            <BrandMark to="/" />
            <p className="mt-4 max-w-md text-sm leading-relaxed text-muted">{t('footer.tagline')}</p>
            <p className="mt-5 text-xs tracking-wide text-muted/80">{t('footer.copyright')}</p>
          </div>
          <div>
            <h2 className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-muted">{t('footer.product')}</h2>
            <ul className="mt-4 flex flex-col gap-2.5 text-sm">
              <li>
                <Link to="/" className="text-foreground/85 transition-colors hover:text-foreground">
                  {t('nav.home')}
                </Link>
              </li>
              <li>
                <Link to="/about" className="text-foreground/85 transition-colors hover:text-foreground">
                  {t('nav.about')}
                </Link>
              </li>
              <li>
                <Link to="/plugins" className="text-foreground/85 transition-colors hover:text-foreground">
                  {t('nav.plugins')}
                </Link>
              </li>
              <li>
                <a href={ROOT_LINKS.docs} className="text-foreground/85 transition-colors hover:text-foreground">
                  {t('nav.docs')}
                </a>
              </li>
              <li>
                <a href={ROOT_LINKS.panel} className="text-foreground/85 transition-colors hover:text-foreground">
                  {t('nav.panel')}
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h2 className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-muted">{t('footer.legal')}</h2>
            <ul className="mt-4 flex flex-col gap-2.5 text-sm">
              <li>
                <a href={ROOT_LINKS.terms} className="text-foreground/85 transition-colors hover:text-foreground">
                  {t('footer.terms')}
                </a>
              </li>
              <li>
                <a href={ROOT_LINKS.privacy} className="text-foreground/85 transition-colors hover:text-foreground">
                  {t('footer.privacy')}
                </a>
              </li>
              <li>
                <a href={ROOT_LINKS.cookies} className="text-foreground/85 transition-colors hover:text-foreground">
                  {t('footer.cookies')}
                </a>
              </li>
              <li>
                <a href={ROOT_LINKS.disclaimer} className="text-foreground/85 transition-colors hover:text-foreground">
                  {t('footer.disclaimer')}
                </a>
              </li>
              <li>
                <a href={ROOT_LINKS.credits} className="text-foreground/85 transition-colors hover:text-foreground">
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
