import { NavLink, Outlet } from 'react-router-dom'
import { useT } from '../context/LanguageContext'

const TABS = [
  { to: '/plugins', end: true, labelKey: 'plugins.tab.catalog' },
  { to: '/plugins/snowflake', labelKey: 'plugins.tab.snowflake' },
  { to: '/plugins/timestamp', labelKey: 'plugins.tab.timestamp' },
  { to: '/plugins/permissions', labelKey: 'plugins.tab.permissions' },
  { to: '/plugins/badges', labelKey: 'plugins.tab.badges' },
  { to: '/plugins/avatars', labelKey: 'plugins.tab.avatars' },
] as const

export function PluginsLayout() {
  const t = useT()

  return (
    <div className="space-y-8">
      <nav className="lookup-mode-track flex flex-wrap gap-1" aria-label={t('plugins.title')}>
        {TABS.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            end={'end' in tab ? tab.end : false}
            className={({ isActive }) =>
              `cursor-pointer rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary text-white'
                  : 'text-muted hover:bg-surface-hover hover:text-foreground'
              }`
            }
          >
            {t(tab.labelKey)}
          </NavLink>
        ))}
      </nav>
      <Outlet />
    </div>
  )
}
