import {
  ArrowsLeftRight,
  Broadcast,
  CalendarCheck,
  Car,
  Confetti,
  ChartBar,
  ChartLine,
  ChatCircleText,
  ClipboardText,
  Coins,
  Crown,
  DiceThree,
  FilmSlate,
  DoorOpen,
  GlobeHemisphereWest,
  Headset,
  House,
  Lightbulb,
  ListMagnifyingGlass,
  Megaphone,
  Package,
  Shield,
  ShieldWarning,
  SignOut,
  Skull,
  Sparkle,
  Stack,
  Ticket,
  TrendUp,
  Trophy,
  Users,
  UsersThree,
  Vault,
  Wrench,
  type Icon,
} from '@phosphor-icons/react'
import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { logout } from '../api/client'
import { LanguageToggle } from '../components/LanguageToggle'
import { Dropdown, DropdownItem } from '../components/ui/Dropdown'
import { useAuth } from '../context/AuthContext'
import { useT } from '../context/LanguageContext'

interface Section {
  labelKey: string
  icon: Icon
  to: string
  mainGuildOnly?: boolean
}

interface NavGroup {
  titleKey: string
  icon: Icon
  items: Section[]
  superAdminOnly?: boolean
}

const NAV_GROUPS: NavGroup[] = [
  {
    titleKey: 'nav.group.activity',
    icon: TrendUp,
    items: [
      { labelKey: 'nav.levels', icon: ChartBar, to: '/levels' },
      { labelKey: 'nav.economy', icon: Coins, to: '/economy' },
      { labelKey: 'nav.casino', icon: DiceThree, to: '/casino' },
      { labelKey: 'nav.voiceStats', icon: ChartLine, to: '/voice-stats' },
    ],
  },
  {
    titleKey: 'nav.group.gta5rp',
    icon: Car,
    items: [
      { labelKey: 'nav.family', icon: House, to: '/family' },
      { labelKey: 'nav.supply', icon: Package, to: '/supply' },
    ],
  },
  {
    titleKey: 'nav.group.community',
    icon: Users,
    items: [
      { labelKey: 'nav.feedback', icon: ChatCircleText, to: '/feedback' },
      { labelKey: 'nav.events', icon: CalendarCheck, to: '/events' },
      { labelKey: 'nav.brackets', icon: Trophy, to: '/brackets' },
      { labelKey: 'nav.mafia', icon: Skull, to: '/mafia' },
      { labelKey: 'nav.bunker', icon: Vault, to: '/bunker' },
      { labelKey: 'nav.voiceRooms', icon: Headset, to: '/voice-rooms' },
    ],
  },
  {
    titleKey: 'nav.group.content',
    icon: FilmSlate,
    items: [
      { labelKey: 'nav.fun', icon: Confetti, to: '/fun' },
      { labelKey: 'nav.reactionRoles', icon: Stack, to: '/reaction-roles' },
      { labelKey: 'nav.streams', icon: Broadcast, to: '/streams' },
      { labelKey: 'nav.dailyTopic', icon: Lightbulb, to: '/daily-topic' },
    ],
  },
  {
    titleKey: 'nav.group.admin',
    icon: Wrench,
    items: [
      { labelKey: 'nav.serverlog', icon: ListMagnifyingGlass, to: '/serverlog' },
      { labelKey: 'nav.lockdown', icon: ShieldWarning, to: '/lockdown' },
      { labelKey: 'nav.automod', icon: Shield, to: '/automod' },
      { labelKey: 'nav.serverEntry', icon: DoorOpen, to: '/server-entry' },
      { labelKey: 'nav.members', icon: UsersThree, to: '/members' },
      { labelKey: 'nav.audit', icon: ClipboardText, to: '/audit' },
      { labelKey: 'nav.settings', icon: GlobeHemisphereWest, to: '/settings' },
    ],
  },
  {
    titleKey: 'nav.group.superadmin',
    icon: Crown,
    superAdminOnly: true,
    items: [
      { labelKey: 'nav.superadminServers', icon: Crown, to: '/superadmin' },
      { labelKey: 'nav.news', icon: Megaphone, to: '/news' },
      { labelKey: 'nav.ctd', icon: Ticket, to: '/ctd', mainGuildOnly: true },
    ],
  },
]

export function DashboardShell() {
  const { user, refresh } = useAuth()
  const t = useT()
  const navigate = useNavigate()
  const [isLoggingOut, setIsLoggingOut] = useState(false)

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
      <header className="flex shrink-0 items-center justify-between border-b border-border px-6 py-4">
        <div className="flex items-center gap-4">
          <Link to="/" className="flex items-center gap-2 text-foreground">
            <Sparkle size={20} weight="fill" className="text-primary" />
            <span className="font-semibold">Cheterin</span>
          </Link>
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
          </nav>
        </div>

        <div className="flex items-center gap-3">
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
                <span className="max-w-[10rem] truncate text-sm text-foreground">
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
        <aside className="w-72 shrink-0 overflow-y-auto border-r border-border p-4">
          <Link
            to="/servers"
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
          <nav className="flex flex-col gap-5">
            {NAV_GROUPS.filter((group) => !group.superAdminOnly || user?.is_super_admin).map((group, groupIndex) => (
              <div key={group.titleKey} className="animate-fade-in-up" style={{ animationDelay: `${groupIndex * 60}ms` }}>
                <p className="mb-1.5 flex items-center gap-1.5 px-2.5 text-[11px] font-semibold uppercase tracking-wider text-muted">
                  <group.icon size={13} weight="bold" className="shrink-0" />
                  {t(group.titleKey)}
                </p>
                <div className="flex flex-col gap-0.5">
                  {group.items
                    .filter((item) => !item.mainGuildOnly || user?.is_main_guild)
                    .map(({ labelKey, icon: SectionIcon, to }) => (
                    <NavLink
                      key={labelKey}
                      to={to}
                      className={({ isActive }) =>
                        `${itemBase} cursor-pointer ${
                          isActive
                            ? 'border-primary bg-primary-muted font-medium text-foreground'
                            : 'border-transparent text-muted hover:bg-surface-hover hover:text-foreground'
                        }`
                      }
                    >
                      {({ isActive }) => (
                        <>
                          <SectionIcon size={17} weight={isActive ? 'fill' : 'regular'} className={`shrink-0 ${isActive ? 'text-primary' : ''}`} />
                          {t(labelKey)}
                        </>
                      )}
                    </NavLink>
                  ))}
                </div>
              </div>
            ))}
          </nav>
        </aside>

        <main className="min-w-0 flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
