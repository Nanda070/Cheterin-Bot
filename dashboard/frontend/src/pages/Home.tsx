import {
  Broom,
  CalendarCheck,
  ChatCircleText,
  Clock,
  ClipboardText,
  Gift,
  GlobeHemisphereWest,
  LockKeyOpen,
  Prohibit,
  ShieldCheck,
  ShieldWarning,
  SignOut,
  Siren,
  SpeakerSimpleSlash,
  SpeakerSimpleX,
  UserCheck,
  UsersThree,
  Warning,
} from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  fetchEvents,
  fetchFeedbackCases,
  fetchGiveawayOverview,
  fetchLockdownStatus,
  fetchMembers,
  fetchModerationLog,
  fetchSetupHealth,
  type GiveawayOverview,
  type LockdownStatus,
  type ModerationLogEntry,
  type SetupHealth,
} from '../api/client'
import { WhatsNewCard, WhatsNewModal } from '../components/WhatsNew'
import { Card } from '../components/ui/Card'
import { useAuth } from '../context/AuthContext'
import { useT } from '../context/LanguageContext'

// Where the dashboard admin can go fix a module-health issue.
const MODULE_ROUTE: Record<string, string> = {
  starboard: '/messages?tab=starboard',
  valchecker: '/valchecker',
  birthdays: '/birthdays',
  daily_topic: '/daily-topic',
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

const TYPE_ICON: Record<ModerationLogEntry['type'], typeof Warning> = {
  spam_punish: Warning,
  tempban: Clock,
  manual_ban: Prohibit,
  manual_kick: SignOut,
  warn_manual: Warning,
  command_ban: Prohibit,
  command_kick: SignOut,
  command_mute: SpeakerSimpleX,
  command_unmute: SpeakerSimpleSlash,
  command_unban: LockKeyOpen,
  command_clear: Broom,
  antiraid_trigger: Siren,
  verification_pass: UserCheck,
  verification_expired: UserCheck,
}

function modlogLabel(t: (key: string) => string, type: ModerationLogEntry['type']): string {
  return t(`home.modlog.${type}`)
}

export function HomePage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const t = useT()

  const [feedbackCount, setFeedbackCount] = useState<number | null>(null)
  const [feedbackError, setFeedbackError] = useState('')

  const [eventsCount, setEventsCount] = useState<number | null>(null)
  const [eventsError, setEventsError] = useState('')

  const [activity, setActivity] = useState<ModerationLogEntry[] | null>(null)
  const [activityError, setActivityError] = useState('')

  const [lockdownStatus, setLockdownStatus] = useState<LockdownStatus | null>(null)
  const [lockdownError, setLockdownError] = useState('')

  const [memberCount, setMemberCount] = useState<number | null>(null)
  const [memberError, setMemberError] = useState('')

  const [giveaways, setGiveaways] = useState<GiveawayOverview | null>(null)
  const [giveawaysError, setGiveawaysError] = useState('')

  const [health, setHealth] = useState<SetupHealth | null>(null)

  useEffect(() => {
    fetchFeedbackCases('pending')
      .then((cases) => setFeedbackCount(cases.length))
      .catch(() => setFeedbackError(t('common.errorLoad')))
  }, [t])

  useEffect(() => {
    fetchEvents('open')
      .then((events) => setEventsCount(events.length))
      .catch(() => setEventsError(t('common.errorLoad')))
  }, [t])

  useEffect(() => {
    fetchModerationLog()
      .then(setActivity)
      .catch(() => setActivityError(t('common.errorLoad')))
  }, [t])

  useEffect(() => {
    fetchLockdownStatus()
      .then(setLockdownStatus)
      .catch(() => setLockdownError(t('common.errorLoad')))
  }, [t])

  useEffect(() => {
    fetchMembers('', 1, 1)
      .then((page) => setMemberCount(page.total))
      .catch(() => setMemberError(t('common.errorLoad')))
  }, [t])

  useEffect(() => {
    fetchGiveawayOverview()
      .then(setGiveaways)
      .catch(() => setGiveawaysError(t('common.errorLoad')))
  }, [t])

  useEffect(() => {
    fetchSetupHealth()
      .then(setHealth)
      .catch(() => setHealth(null))
  }, [t])

  return (
    <div>
      <h1 className="mb-4 text-lg font-semibold text-foreground">
        {t('home.welcome', { username: user?.username ?? '' })}
      </h1>

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
          onClick={() => navigate('/lockdown')}
          className="flex cursor-pointer items-center gap-1.5 rounded-control border border-border bg-surface px-3 py-1.5 text-sm text-muted transition hover:border-primary hover:text-foreground"
        >
          <ClipboardText size={14} />
          {t('home.quickLinks.moderationLog')}
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

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card interactive className="animate-fade-in-up" onClick={() => navigate('/feedback')}>
          <div className="flex items-center gap-2 text-foreground">
            <ChatCircleText size={20} className="text-primary" />
            <h2 className="font-semibold">{t('home.feedback')}</h2>
          </div>
          {feedbackError && <p className="mt-2 text-sm text-danger">{feedbackError}</p>}
          {!feedbackError && feedbackCount === null && (
            <p className="mt-2 text-sm text-muted">{t('common.loading')}</p>
          )}
          {!feedbackError && feedbackCount !== null && (
            <p className="mt-2 text-sm text-muted">
              {feedbackCount === 0
                ? t('home.feedback.nonePending')
                : t('home.feedback.pendingCount', { count: feedbackCount })}
            </p>
          )}
        </Card>

        <Card interactive className="animate-fade-in-up" onClick={() => navigate('/events')}>
          <div className="flex items-center gap-2 text-foreground">
            <CalendarCheck size={20} className="text-primary" />
            <h2 className="font-semibold">{t('home.events')}</h2>
          </div>
          {eventsError && <p className="mt-2 text-sm text-danger">{eventsError}</p>}
          {!eventsError && eventsCount === null && (
            <p className="mt-2 text-sm text-muted">{t('common.loading')}</p>
          )}
          {!eventsError && eventsCount !== null && (
            <p className="mt-2 text-sm text-muted">{t('home.events.activeCount', { count: eventsCount })}</p>
          )}
        </Card>

        <Card interactive className="animate-fade-in-up" onClick={() => navigate('/lockdown')}>
          <div className="flex items-center gap-2 text-foreground">
            <ShieldWarning size={20} className="text-primary" />
            <h2 className="font-semibold">{t('home.moderation')}</h2>
          </div>
          {activityError && <p className="mt-2 text-sm text-danger">{activityError}</p>}
          {!activityError && activity === null && (
            <p className="mt-2 text-sm text-muted">{t('common.loading')}</p>
          )}
          {!activityError && activity !== null && activity.length === 0 && (
            <p className="mt-2 text-sm text-muted">{t('home.moderation.noActivity')}</p>
          )}
          {!activityError && activity !== null && activity.length > 0 && (
            <ul className="mt-2 flex flex-col gap-1">
              {activity.slice(0, 3).map((entry, index) => {
                const Icon = TYPE_ICON[entry.type]
                return (
                  <li key={index} className="flex items-center gap-2 text-sm text-muted">
                    <Icon size={14} className="shrink-0" />
                    <span className="truncate">
                      {t('home.modlog.entry', {
                        label: modlogLabel(t, entry.type),
                        user: entry.user_display,
                      })}
                    </span>
                  </li>
                )
              })}
            </ul>
          )}
        </Card>

        <Card interactive className="animate-fade-in-up" onClick={() => navigate('/lockdown')}>
          <div className="flex items-center gap-2 text-foreground">
            {lockdownStatus?.active ? (
              <ShieldWarning size={20} weight="fill" className="text-danger" />
            ) : (
              <ShieldCheck size={20} weight="fill" className="text-success" />
            )}
            <h2 className="font-semibold">{t('home.antispam')}</h2>
          </div>
          {lockdownError && <p className="mt-2 text-sm text-danger">{lockdownError}</p>}
          {!lockdownError && lockdownStatus === null && (
            <p className="mt-2 text-sm text-muted">{t('common.loading')}</p>
          )}
          {!lockdownError && lockdownStatus !== null && (
            <p className="mt-2 text-sm text-muted">
              {lockdownStatus.active ? t('common.on') : t('common.off')}
            </p>
          )}
        </Card>

        <Card interactive className="animate-fade-in-up" onClick={() => navigate('/members')}>
          <div className="flex items-center gap-2 text-foreground">
            <UsersThree size={20} className="text-primary" />
            <h2 className="font-semibold">{t('home.members')}</h2>
          </div>
          {memberError && <p className="mt-2 text-sm text-danger">{memberError}</p>}
          {!memberError && memberCount === null && (
            <p className="mt-2 text-sm text-muted">{t('common.loading')}</p>
          )}
          {!memberError && memberCount !== null && (
            <p className="mt-2 text-sm text-muted">{t('home.members.count', { count: memberCount })}</p>
          )}
        </Card>

        <Card interactive className="animate-fade-in-up" onClick={() => navigate('/giveaways')}>
          <div className="flex items-center gap-2 text-foreground">
            <Gift size={20} className="text-primary" />
            <h2 className="font-semibold">{t('home.giveaways')}</h2>
          </div>
          {giveawaysError && <p className="mt-2 text-sm text-danger">{giveawaysError}</p>}
          {!giveawaysError && giveaways === null && (
            <p className="mt-2 text-sm text-muted">{t('common.loading')}</p>
          )}
          {!giveawaysError && giveaways !== null && (
            <p className="mt-2 text-sm text-muted">
              {giveaways.active.length === 0
                ? t('home.giveaways.none')
                : t('home.giveaways.activeCount', { count: giveaways.active.length })}
            </p>
          )}
        </Card>
      </div>
    </div>
  )
}
