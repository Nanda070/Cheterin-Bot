import { useState, type ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { BrandMark, LanguageToggle } from './ui'
import { SiteFooter } from './SiteFooter'
import { useT } from '../context/LanguageContext'

const ROOT_LINKS = {
  docs: '/docs',
  about: '/about',
} as const

export function LookupLayout({ children }: { children: ReactNode }) {
  const t = useT()
  const [menuOpen, setMenuOpen] = useState(false)

  const nav = [
    { to: '/', label: t('nav.home'), end: true },
    { to: '/about', label: t('nav.about') },
    { to: '/plugins', label: t('nav.plugins') },
    { to: '/dsa', label: t('nav.dsa') },
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
                <NavLink key={item.to} to={item.to} end={'end' in item ? item.end : false} className={linkClass}>
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

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-9 sm:px-6 sm:py-11" data-scroll-reset>
        {children}
      </main>

      <SiteFooter />
    </div>
  )
}
