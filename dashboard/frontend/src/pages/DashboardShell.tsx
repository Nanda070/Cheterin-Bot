import {
  ArrowsLeftRight,
  Broadcast,
  Cake,
  CalendarCheck,
  Crosshair,
  Chats,
  Confetti,
  ChartBar,
  ChartLine,
  ChatCircleText,
  Coins,
  Crown,
  DoorOpen,
  GlobeHemisphereWest,
  Headset,
  Heart,
  House,
  HouseLine,
  Image,
  List,
  ListMagnifyingGlass,
  MagnifyingGlass,
  Megaphone,
  Shield,
  ShieldWarning,
  Pulse,
  SignOut,
  Skull,
  Stack,
  Ticket,
  TrendUp,
  Users,
  UsersThree,
  Vault,
  Wrench,
  X,
  type Icon,
} from '@phosphor-icons/react'
import { useEffect, useMemo, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { BrandMark } from '../components/BrandMark'
import { fetchModules, logout } from '../api/client'
import { CommandPalette } from '../components/CommandPalette'
import { LanguageToggle } from '../components/LanguageToggle'
import { Dropdown, DropdownItem } from '../components/ui/Dropdown'
import { Toggle } from '../components/ui/Toggle'
import { useAuth } from '../context/AuthContext'
import { useT } from '../context/LanguageContext'

const SHOW_DISABLED_MODULES_KEY = 'cheterin.showDisabledModules'

interface Section {
  labelKey: string
  icon: Icon
  to: string
  mainGuildOnly?: boolean
  /** Key returned by GET /api/modules — hides the item when that module is disabled (unless "show disabled" is on). */
  moduleKey?: string
}

interface NavGroup {
  titleKey: string
  icon: Icon
  items: Section[]
  superAdminOnly?: boolean
}

const NAV_GROUPS: NavGroup[] = [
  {
    titleKey: 'nav.group.home',
    icon: HouseLine,
    items: [{ labelKey: 'nav.home', icon: HouseLine, to: '/' }],
  },
  {
    titleKey: 'nav.group.engage',
    icon: TrendUp,
    items: [
      { labelKey: 'nav.levels', icon: ChartBar, to: '/levels', moduleKey: 'levels' },
      { labelKey: 'nav.economy', icon: Coins, to: '/economy', moduleKey: 'economy' },
      { labelKey: 'nav.voiceStats', icon: ChartLine, to: '/voice-stats' },
    ],
  },
  {
    titleKey: 'nav.group.people',
    icon: Users,
    items: [
      { labelKey: 'nav.relations', icon: Heart, to: '/relations', moduleKey: 'relations' },
      { labelKey: 'nav.birthdays', icon: Cake, to: '/birthdays', moduleKey: 'birthdays' },
      { labelKey: 'nav.voiceRooms', icon: Headset, to: '/voice-rooms' },
      { labelKey: 'nav.events', icon: CalendarCheck, to: '/events' },
      { labelKey: 'nav.feedback', icon: ChatCircleText, to: '/feedback' },
      { labelKey: 'nav.messages', icon: Chats, to: '/messages', moduleKey: 'messages' },
      { labelKey: 'nav.reactionRoles', icon: Stack, to: '/reaction-roles' },
    ],
  },
  {
    titleKey: 'nav.group.play',
    icon: Confetti,
    items: [
      { labelKey: 'nav.fun', icon: Confetti, to: '/fun', moduleKey: 'fun' },
      { labelKey: 'nav.mafia', icon: Skull, to: '/mafia', moduleKey: 'mafia' },
      { labelKey: 'nav.bunker', icon: Vault, to: '/bunker', moduleKey: 'bunker' },
      { labelKey: 'nav.valorant', icon: Crosshair, to: '/valorant' },
      { labelKey: 'nav.family', icon: House, to: '/family', moduleKey: 'family' },
      { labelKey: 'nav.streams', icon: Broadcast, to: '/streams' },
    ],
  },
  {
    titleKey: 'nav.group.server',
    icon: Wrench,
    items: [
      { labelKey: 'nav.lockdown', icon: ShieldWarning, to: '/lockdown' },
      { labelKey: 'nav.automod', icon: Shield, to: '/automod', moduleKey: 'automod' },
      { labelKey: 'nav.serverlog', icon: ListMagnifyingGlass, to: '/serverlog' },
      { labelKey: 'nav.serverEntry', icon: DoorOpen, to: '/server-entry' },
      { labelKey: 'nav.members', icon: UsersThree, to: '/members' },
      { labelKey: 'nav.bannerRotation', icon: Image, to: '/banner-rotation', moduleKey: 'bannerRotation' },
      { labelKey: 'nav.settings', icon: GlobeHemisphereWest, to: '/settings' },
    ],
  },
  {
    titleKey: 'nav.group.superadmin',
    icon: Crown,
    superAdminOnly: true,
    items: [
      { labelKey: 'nav.superadminServers', icon: Crown, to: '/superadmin' },
      { labelKey: 'nav.health', icon: Pulse, to: '/health' },
      { labelKey: 'nav.news', icon: Megaphone, to: '/news' },
      { labelKey: 'nav.ctd', icon: Ticket, to: '/ctd', mainGuildOnly: true },
    ],
  },
]

function navItemActive(to: string, pathname: string, search: string): boolean {
  const [path, query = ''] = to.split('?')
  if (pathname !== path) return false
  if (query) return search.includes(query)
  return true
}

function SidebarNav({
  onNavigate,
  itemBase,
  modules,
  showDisabled,
  onShowDisabledChange,
}: {
  onNavigate?: () => void
  itemBase: string
  modules: Record<string, boolean> | null
  showDisabled: boolean
  onShowDisabledChange: (v: boolean) => void
}) {
  const { user } = useAuth()
  const t = useT()
  const location = useLocation()

  const isModuleDisabled = (moduleKey?: string) => !!moduleKey && modules?.[moduleKey] === false

  return (
    <>
      <Link
        to="/servers"
        onClick={onNavigate}
        className="mb-4 flex items-center gap-3 rounded-control border border-border bg-surface p-3 transition-colors hover:bg-surface-hover"
      >
        {user?.active_guild_icon ? (
          <img src={user.active_guild_icon} alt="" className="h-9 w-9 rounded-md" />
        ) : (
          <span className="flex h-9 w-9 items-center justify-center rounded-md bg-primary-muted text-sm font-semibold text-primary">
            {(user?.active_guild_name ?? '?').slice(0, 1).toUpperCase()}
          </span>
        )}
        <div className="flex min-w-0 flex-col">
          <span className="truncate text-sm font-medium text-foreground">
            {user?.active_guild_name ?? t('nav.selectServer')}
          </span>
          <span className="flex items-center gap-1 text-[11px] text-muted">
            <ArrowsLeftRight size={11} />
            {t('nav.switchServer')}
          </span>
        </div>
      </Link>
      <nav className="flex flex-col gap-5" aria-label={t('nav.menu')}>
        {NAV_GROUPS.filter((group) => !group.superAdminOnly || user?.is_super_admin).map((group, groupIndex) => {
          const visibleItems = group.items
            .filter((item) => !item.mainGuildOnly || user?.is_main_guild)
            .filter((item) => showDisabled || !isModuleDisabled(item.moduleKey))
          if (visibleItems.length === 0) return null
          return (
          <div key={group.titleKey} className="animate-fade-in-up" style={{ animationDelay: `${groupIndex * 60}ms` }}>
            <p className="mb-1.5 flex items-center gap-1.5 px-2.5 text-[11px] font-semibold uppercase tracking-wider text-muted">
              <group.icon size={13} weight="bold" className="shrink-0" />
              {t(group.titleKey)}
            </p>
            <div className="flex flex-col gap-0.5">
              {visibleItems.map(({ labelKey, icon: SectionIcon, to, moduleKey }) => {
                  const disabled = isModuleDisabled(moduleKey)
                  return (
                    <NavLink
                      key={labelKey}
                      to={to}
                      end={to === '/'}
                      onClick={onNavigate}
                      className={() => {
                        const isActive = navItemActive(to, location.pathname, location.search)
                        return `${itemBase} cursor-pointer ${disabled ? 'opacity-50' : ''} ${
                          isActive
                            ? 'border-primary bg-primary-muted font-medium text-foreground'
                            : 'border-transparent text-muted hover:bg-surface-hover hover:text-foreground'
                        }`
                      }}
                    >
                      {() => {
                        const isActive = navItemActive(to, location.pathname, location.search)
                        return (
                        <>
                          <SectionIcon
                            size={17}
                            weight={isActive ? 'fill' : 'regular'}
                            className={`shrink-0 ${isActive ? 'text-primary' : ''}`}
                          />
                          <span className="min-w-0 flex-1 truncate">{t(labelKey)}</span>
                          {disabled && (
                            <span className="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted bg-surface-hover">
                              {t('nav.moduleDisabledBadge')}
                            </span>
                          )}
                        </>
                        )
                      }}
                    </NavLink>
                  )
                })}
            </div>
          </div>
          )
        })}
      </nav>
      <div className="mt-5 border-t border-border px-2.5 pt-4">
        <Toggle checked={showDisabled} onChange={onShowDisabledChange} label={t('nav.showDisabledModules')} />
      </div>
    </>
  )
}

export function DashboardShell() {
  const { user, refresh } = useAuth()
  const t = useT()
  const navigate = useNavigate()
  const location = useLocation()
  const [isLoggingOut, setIsLoggingOut] = useState(false)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [modules, setModules] = useState<Record<string, boolean> | null>(null)
  const [showDisabled, setShowDisabled] = useState(() => {
    try {
      const stored = window.localStorage.getItem(SHOW_DISABLED_MODULES_KEY)
      // Default OFF — only show enabled modules until the user opts in.
      return stored === null ? false : stored === '1'
    } catch {
      return false
    }
  })

  useEffect(() => {
    fetchModules()
      .then(setModules)
      .catch(() => setModules({}))
  }, [user?.active_guild_id])

  const toggleShowDisabled = (v: boolean) => {
    setShowDisabled(v)
    try {
      window.localStorage.setItem(SHOW_DISABLED_MODULES_KEY, v ? '1' : '0')
    } catch {
      /* localStorage unavailable (privacy mode, test env) — in-memory toggle still works */
    }
  }

  const isModuleDisabled = (moduleKey?: string) => !!moduleKey && modules?.[moduleKey] === false

  const paletteItems = useMemo(
    () =>
      NAV_GROUPS.filter((group) => !group.superAdminOnly || user?.is_super_admin).flatMap((group) =>
        group.items
          .filter((item) => !item.mainGuildOnly || user?.is_main_guild)
          .filter((item) => showDisabled || !isModuleDisabled(item.moduleKey))
          .map((item) => ({ id: item.to, title: t(item.labelKey), group: t(group.titleKey) })),
      ),
    [user?.is_super_admin, user?.is_main_guild, t, modules, showDisabled],
  )

  useEffect(() => {
    setMobileNavOpen(false)
  }, [location.pathname])

  useEffect(() => {
    if (!mobileNavOpen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMobileNavOpen(false)
    }
    document.addEventListener('keydown', onKey)
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = prev
    }
  }, [mobileNavOpen])

  const handleLogout = async () => {
    setIsLoggingOut(true)
    try {
      await logout()
      await refresh()
    } catch (error) {
      console.error('Failed to log out:', error)
    } finally {
      setIsLoggingOut(false)
    }
  }

  const itemBase =
    'flex items-center gap-2.5 rounded-control border-l-2 px-2.5 py-2 text-sm transition-colors duration-200 ease-out'

  return (
    <div className="flex h-dvh flex-col">
      <header className="flex shrink-0 items-center justify-between border-b border-border px-4 py-4 sm:px-6">
        <div className="flex items-center gap-3 sm:gap-4">
          <button
            type="button"
            className="inline-flex cursor-pointer items-center justify-center rounded-control p-2 text-muted hover:bg-surface-hover hover:text-foreground md:hidden"
            aria-label={mobileNavOpen ? t('nav.closeMenu') : t('nav.openMenu')}
            aria-expanded={mobileNavOpen}
            aria-controls="dashboard-mobile-nav"
            onClick={() => setMobileNavOpen((v) => !v)}
          >
            {mobileNavOpen ? <X size={20} /> : <List size={20} />}
          </button>
          <BrandMark to="/about" iconSize={20} />
          <nav className="hidden items-center gap-3 text-sm text-muted sm:flex">
            <Link to="/docs" className="transition-colors hover:text-foreground">
              {t('nav.docs')}
            </Link>
            <Link to="/terms" className="transition-colors hover:text-foreground">
              {t('nav.terms')}
            </Link>
            <Link to="/privacy" className="transition-colors hover:text-foreground">
              {t('nav.privacy')}
            </Link>
            <Link to="/cookies" className="transition-colors hover:text-foreground">
              {t('nav.cookies')}
            </Link>
            <Link to="/disclaimer" className="transition-colors hover:text-foreground">
              {t('nav.disclaimer')}
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setPaletteOpen(true)}
            aria-label={t('nav.commandPalette.open')}
            className="inline-flex cursor-pointer items-center gap-1.5 rounded-control border border-border bg-surface px-2.5 py-1.5 text-xs text-muted transition-colors hover:border-primary hover:text-foreground"
          >
            <MagnifyingGlass size={14} />
            <span className="hidden rounded-[6px] border border-border bg-background px-1.5 py-0.5 text-[11px] sm:inline">
              Ctrl K
            </span>
          </button>
          <LanguageToggle />
          <Dropdown
            trigger={
              <span className="flex items-center gap-2 rounded-control px-2 py-1.5 hover:bg-surface-hover">
                {user?.avatar ? (
                  <img src={user.avatar} alt="" className="h-7 w-7 rounded-full" />
                ) : (
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary-muted text-xs font-semibold text-primary">
                    {user?.username?.slice(0, 1).toUpperCase()}
                  </span>
                )}
                <span className="hidden max-w-[10rem] truncate text-sm text-foreground sm:inline">
                  {user?.username}
                </span>
              </span>
            }
          >
            <DropdownItem onClick={() => navigate('/servers')}>
              <ArrowsLeftRight size={16} />
              {t('nav.switchServer')}
            </DropdownItem>
            <DropdownItem onClick={handleLogout} danger>
              <SignOut size={16} />
              {isLoggingOut ? t('nav.loggingOut') : t('nav.logout')}
            </DropdownItem>
          </Dropdown>
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        <aside className="hidden w-72 shrink-0 overflow-y-auto border-r border-border p-4 md:block">
          <SidebarNav
            itemBase={itemBase}
            modules={modules}
            showDisabled={showDisabled}
            onShowDisabledChange={toggleShowDisabled}
          />
        </aside>

        {mobileNavOpen && (
          <div className="fixed inset-0 z-40 md:hidden" role="presentation">
            <button
              type="button"
              className="absolute inset-0 cursor-pointer bg-black/50"
              aria-label={t('nav.closeMenu')}
              onClick={() => setMobileNavOpen(false)}
            />
            <aside
              id="dashboard-mobile-nav"
              className="absolute inset-y-0 left-0 flex w-[min(20rem,85vw)] flex-col overflow-y-auto border-r border-border bg-background p-4 shadow-lg"
            >
              <SidebarNav
                itemBase={itemBase}
                modules={modules}
                showDisabled={showDisabled}
                onShowDisabledChange={toggleShowDisabled}
                onNavigate={() => setMobileNavOpen(false)}
              />
            </aside>
          </div>
        )}

        <main className="min-w-0 flex-1 overflow-y-auto p-4 sm:p-6">
          <Outlet />
        </main>
      </div>

      <CommandPalette
        items={paletteItems}
        onSelect={(id) => navigate(id)}
        title={t('nav.commandPalette.title')}
        placeholder={t('nav.commandPalette.placeholder')}
        emptyLabel={t('nav.commandPalette.empty')}
        hideTrigger
        open={paletteOpen}
        onOpenChange={setPaletteOpen}
      />
    </div>
  )
}
