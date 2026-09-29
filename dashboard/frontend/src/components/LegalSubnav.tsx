import { NavLink } from 'react-router-dom'
import { useT } from '../context/LanguageContext'

const LEGAL_LINKS = [
  { to: '/terms', labelKey: 'legal.nav.terms' },
  { to: '/privacy', labelKey: 'legal.nav.privacy' },
  { to: '/cookies', labelKey: 'legal.nav.cookies' },
  { to: '/disclaimer', labelKey: 'legal.nav.disclaimer' },
] as const

/** Shared tabs between Terms / Privacy / Cookies / Disclaimer. */
export function LegalSubnav() {
  const t = useT()

  return (
    <nav
      className="mb-6 flex flex-wrap gap-1.5 border-b border-border/80 pb-4"
      aria-label={t('legal.nav.aria')}
    >
      {LEGAL_LINKS.map((link) => (
        <NavLink
          key={link.to}
          to={link.to}
          className={({ isActive }) =>
            `rounded-control px-3 py-1.5 text-sm transition-colors ${
              isActive
                ? 'border border-primary/40 bg-primary-muted font-medium text-foreground'
                : 'border border-transparent text-muted hover:bg-surface-hover hover:text-foreground'
            }`
          }
        >
          {t(link.labelKey)}
        </NavLink>
      ))}
    </nav>
  )
}
