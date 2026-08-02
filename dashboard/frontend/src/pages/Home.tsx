import {
  GlobeHemisphereWest,
  ShieldWarning,
  UsersThree,
  Warning,
} from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchSetupHealth, type SetupHealth } from '../api/client'
import { SecretClickTarget } from '../components/SecretClickTarget'
import { WhatsNewCard, WhatsNewModal } from '../components/WhatsNew'
import { useAuth } from '../context/AuthContext'
import { useT } from '../context/LanguageContext'
import { SECRET_ROOMS } from '../utils/easterEggs'

// Where the dashboard admin can go fix a module-health issue.
const MODULE_ROUTE: Record<string, string> = {
  starboard: '/messages?tab=starboard',
  valchecker: '/valchecker',
  birthdays: '/birthdays',
  daily_topic: '/fun?tab=dailyTopic',
  wordle: '/fun',
  levels: '/levels',
  verification: '/lockdown',
}

const MODULE_LABEL_KEY: Record<string, string> = {
  starboard: 'nav.starboard',
  valchecker: 'nav.valchecker',
  birthdays: 'nav.birthdays',
  daily_topic: 'nav.dailyTopic',
  wordle: 'nav.fun',
  levels: 'nav.levels',
  verification: 'nav.lockdown',
}

export function HomePage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const t = useT()
  const [health, setHealth] = useState<SetupHealth | null>(null)

  useEffect(() => {
    fetchSetupHealth()
      .then(setHealth)
      .catch(() => setHealth(null))
  }, [t])

  return (
    <div>
      <SecretClickTarget clicks={8} to={SECRET_ROOMS.waterfall} className="mb-4 block cursor-default">
        <h1 className="text-lg font-semibold text-foreground">
          {t('home.welcome', { username: user?.username ?? '' })}
        </h1>
      </SecretClickTarget>

      <WhatsNewModal />
      <WhatsNewCard />

      {health && health.missing_permissions.length > 0 && (
        <button
          type="button"
          onClick={() => navigate('/settings')}
          className="mb-3 flex w-full items-start gap-2 rounded-control border border-warning/40 bg-warning/10 px-4 py-3 text-left text-sm text-foreground transition hover:border-warning"
        >
          <ShieldWarning size={18} className="mt-0.5 shrink-0 text-warning" />
          <span>
            <span className="font-medium text-warning">{t('home.setupHealth.warning')}</span>
            <span className="mt-0.5 block text-muted">
              {t('home.setupHealth.missingCount', { count: health.missing_permissions.length })}
            </span>
          </span>
        </button>
      )}

      {health && health.module_issues.length > 0 && (
        <div className="mb-4 flex flex-col gap-1.5 rounded-control border border-danger/40 bg-danger/10 px-4 py-3">
          <span className="flex items-center gap-2 text-sm font-medium text-danger">
            <Warning size={16} weight="fill" />
            {t('home.setupHealth.moduleIssuesTitle')}
          </span>
          <ul className="flex flex-col gap-1">
            {health.module_issues.map((issue, index) => (
              <li key={index}>
                <button
                  type="button"
                  onClick={() => navigate(MODULE_ROUTE[issue.module] ?? '/settings')}
                  className="cursor-pointer text-left text-sm text-foreground underline-offset-2 hover:text-primary hover:underline"
                >
                  {t(`home.setupHealth.moduleIssue.${issue.kind}`, {
                    module: MODULE_LABEL_KEY[issue.module] ? t(MODULE_LABEL_KEY[issue.module]) : issue.module,
                  })}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mb-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => navigate('/lockdown')}
          className="flex cursor-pointer items-center gap-1.5 rounded-control border border-border bg-surface px-3 py-1.5 text-sm text-muted transition hover:border-primary hover:text-foreground"
        >
          <ShieldWarning size={14} />
          {t('home.quickLinks.moderation')}
        </button>
        <button
          type="button"
          onClick={() => navigate('/members')}
          className="flex cursor-pointer items-center gap-1.5 rounded-control border border-border bg-surface px-3 py-1.5 text-sm text-muted transition hover:border-primary hover:text-foreground"
        >
          <UsersThree size={14} />
          {t('home.quickLinks.members')}
        </button>
        <button
          type="button"
          onClick={() => navigate('/settings')}
          className="flex cursor-pointer items-center gap-1.5 rounded-control border border-border bg-surface px-3 py-1.5 text-sm text-muted transition hover:border-primary hover:text-foreground"
        >
          <GlobeHemisphereWest size={14} />
          {t('home.quickLinks.settings')}
        </button>
      </div>
    </div>
  )
}
