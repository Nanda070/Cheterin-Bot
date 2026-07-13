import { Sparkle } from '@phosphor-icons/react'
import type { ReactNode } from 'react'
import { Link, NavLink } from 'react-router-dom'

const NAV_LINKS = [
  { to: '/docs', label: 'Документация' },
  { to: '/terms', label: 'Условия' },
  { to: '/privacy', label: 'Приватность' },
]

export function PublicLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col">
      <header className="sticky top-0 z-10 border-b border-border bg-background/90 backdrop-blur">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <Link to="/docs" className="flex items-center gap-2 text-foreground">
            <Sparkle size={20} weight="fill" className="text-primary" />
            <span className="font-semibold">Cheterin</span>
          </Link>

          <nav className="flex items-center gap-1 sm:gap-2">
            {NAV_LINKS.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `rounded-control px-2.5 py-1.5 text-sm transition-colors sm:px-3 ${
                    isActive ? 'bg-primary-muted text-foreground' : 'text-muted hover:bg-surface-hover hover:text-foreground'
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
            <Link
              to="/"
              className="ml-1 rounded-control bg-primary px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-primary-hover"
            >
              Дашборд
            </Link>
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:px-6">{children}</main>

      <footer className="border-t border-border">
        <div className="mx-auto flex w-full max-w-5xl flex-col items-center justify-between gap-3 px-4 py-6 text-sm text-muted sm:flex-row sm:px-6">
          <p className="flex items-center gap-2">
            <Sparkle size={16} weight="fill" className="text-primary" />
            Cheterin — Discord-бот и панель управления
          </p>
          <nav className="flex gap-4">
            <Link to="/docs" className="hover:text-foreground">
              Документация
            </Link>
            <Link to="/terms" className="hover:text-foreground">
              Условия пользования
            </Link>
            <Link to="/privacy" className="hover:text-foreground">
              Приватность
            </Link>
          </nav>
        </div>
      </footer>
    </div>
  )
}
