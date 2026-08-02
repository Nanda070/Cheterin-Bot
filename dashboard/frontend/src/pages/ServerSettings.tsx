import {
  Bell,
  ChatTeardropText,
  ClipboardText,
  Clock,
  GearSix,
  GlobeHemisphereWest,
  IdentificationCard,
  Warning,
} from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  fetchChannels,
  fetchLanguage,
  fetchOwnerAlerts,
  fetchSetupHealth,
  fetchTimezone,
  testOwnerAlerts,
  updateLanguage,
  updateOwnerAlerts,
  updateTimezone,
  type ChannelInfo,
  type OwnerAlertsSettings,
  type ServerLanguage,
  type SetupHealth,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'
import { AuditPage } from './Audit'
import { BotProfilePage } from './BotProfile'
import { CustomCommandsPage } from './CustomCommands'

const LANGUAGE_OPTIONS = [
  { value: 'ru', labelKey: 'settings.lang.ru' },
  { value: 'en', labelKey: 'settings.lang.en' },
] as const

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

const defaultAlerts: OwnerAlertsSettings = {
  enabled: false,
  notify_dm: true,
  channel_id: '',
  mass_ban_threshold: 5,
  mass_ban_window_sec: 60,
  module_error_threshold: 5,
  alert_missing_perms: true,
  alert_mass_ban: true,
  alert_module_errors: true,
  weekly_digest_enabled: false,
  weekly_digest_channel_id: '',
}

type SettingsTab = 'general' | 'botProfile' | 'customCommands' | 'audit'

function parseSettingsTab(raw: string | null): SettingsTab {
  if (raw === 'botProfile' || raw === 'audit' || raw === 'customCommands') return raw
  return 'general'
}

function TabBar({
  tab,
  setTab,
  t,
}: {
  tab: SettingsTab
  setTab: (t: SettingsTab) => void
  t: (key: string) => string
}) {
  const tabs: { key: SettingsTab; labelKey: string; icon: typeof GearSix }[] = [
    { key: 'general', labelKey: 'settings.tab.general', icon: GearSix },
    { key: 'botProfile', labelKey: 'settings.tab.botProfile', icon: IdentificationCard },
    { key: 'customCommands', labelKey: 'settings.tab.customCommands', icon: ChatTeardropText },
    { key: 'audit', labelKey: 'settings.tab.audit', icon: ClipboardText },
  ]
  return (
    <div className="flex flex-wrap gap-1 border-b border-border">
      {tabs.map(({ key, labelKey, icon: Icon }) => (
        <button
          key={key}
          type="button"
          onClick={() => setTab(key)}
          className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-sm transition-colors ${
            tab === key ? 'border-primary text-foreground' : 'border-transparent text-muted hover:text-foreground'
          }`}
        >
          <Icon size={15} />
          {t(labelKey)}
        </button>
      ))}
    </div>
  )
}

function GeneralSettings() {
  const t = useT()
  const [language, setLanguage] = useState<ServerLanguage['code']>('ru')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [savedMessage, setSavedMessage] = useState('')

  const [timezone, setTimezone] = useState('Europe/Moscow')
  const [timezoneChoices, setTimezoneChoices] = useState<string[]>([])
  const [tzBusy, setTzBusy] = useState(false)
  const [tzError, setTzError] = useState('')
  const [tzSaved, setTzSaved] = useState('')

  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [alerts, setAlerts] = useState<OwnerAlertsSettings>(defaultAlerts)
  const [alertsBusy, setAlertsBusy] = useState(false)
  const [alertsError, setAlertsError] = useState('')
  const [alertsSaved, setAlertsSaved] = useState('')
  const [testBusy, setTestBusy] = useState(false)

  const [health, setHealth] = useState<SetupHealth | null>(null)
  const [healthError, setHealthError] = useState('')

  useEffect(() => {
    fetchLanguage()
      .then((data) => setLanguage(data.code))
      .catch(() => setError(t('settings.errorLoad')))
      .finally(() => setLoading(false))

    fetchTimezone()
      .then((data) => {
        setTimezone(data.code)
        setTimezoneChoices(data.supported)
      })
      .catch((err) => setTzError(formatApiError(err, t, 'settings.timezone.errorLoad')))

    fetchOwnerAlerts()
      .then(setAlerts)
      .catch((err) => setAlertsError(formatApiError(err, t, 'ownerAlerts.errorLoad')))

    fetchChannels()
      .then(setChannels)
      .catch(() => setChannels([]))

    fetchSetupHealth()
      .then(setHealth)
      .catch((err) => setHealthError(formatApiError(err, t, 'setupHealth.errorLoad')))
  }, [t])

  const handleSave = async () => {
    setBusy(true)
    setError('')
    setSavedMessage('')
    try {
      const data = await updateLanguage(language)
      setLanguage(data.code)
      setSavedMessage(t('settings.saved'))
    } catch (err) {
      setError(formatApiError(err, t, 'settings.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  const saveTimezone = async () => {
    setTzBusy(true)
    setTzError('')
    setTzSaved('')
    try {
      const data = await updateTimezone(timezone)
      setTimezone(data.code)
      setTimezoneChoices(data.supported)
      setTzSaved(t('settings.saved'))
    } catch (err) {
      setTzError(formatApiError(err, t, 'settings.timezone.errorSave'))
    } finally {
      setTzBusy(false)
    }
  }

  const saveAlerts = async () => {
    setAlertsBusy(true)
    setAlertsError('')
    setAlertsSaved('')
    try {
      const data = await updateOwnerAlerts(alerts)
      setAlerts(data)
      setAlertsSaved(t('settings.saved'))
    } catch (err) {
      setAlertsError(formatApiError(err, t, 'ownerAlerts.errorSave'))
    } finally {
      setAlertsBusy(false)
    }
  }

  const sendTestAlert = async () => {
    setTestBusy(true)
    setAlertsError('')
    setAlertsSaved('')
    try {
      await testOwnerAlerts()
      setAlertsSaved(t('ownerAlerts.testSent'))
    } catch (err) {
      setAlertsError(formatApiError(err, t, 'ownerAlerts.testFailed'))
    } finally {
      setTestBusy(false)
    }
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      {error && (
        <div className="rounded-control border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</div>
      )}
      {savedMessage && (
        <div className="rounded-control border border-success/40 bg-success/10 px-4 py-3 text-sm text-success">
          {savedMessage}
        </div>
      )}

      <section className="flex flex-col gap-3 rounded-card border border-border bg-surface p-4">
        <div className="flex items-start gap-2">
          <Warning size={20} className="mt-0.5 text-primary" />
          <div>
            <h2 className="font-medium text-foreground">{t('setupHealth.title')}</h2>
            <p className="mt-1 text-sm text-muted">{t('setupHealth.intro')}</p>
          </div>
        </div>
        {healthError && <p className="text-sm text-danger">{healthError}</p>}
        {!healthError && health === null && <p className="text-sm text-muted">{t('common.loading')}</p>}
        {!healthError && health !== null && health.ok && (
          <p className="text-sm text-success">{t('setupHealth.ok')}</p>
        )}
        {!healthError && health !== null && !health.ok && (
          <div className="rounded-control border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-foreground">
            {health.missing_permissions.length > 0 && (
              <>
                <p className="font-medium text-warning">{t('setupHealth.missing')}</p>
                <ul className="mt-1 list-inside list-disc text-muted">
                  {health.missing_permissions.map((perm) => (
                    <li key={perm}>{perm}</li>
                  ))}
                </ul>
              </>
            )}
            {health.module_issues.length > 0 && (
              <>
                <p className="mt-2 font-medium text-warning">{t('setupHealth.moduleIssues')}</p>
                <ul className="mt-1 list-inside list-disc text-muted">
                  {health.module_issues.map((issue, index) => (
                    <li key={index}>
                      {issue.module}:{' '}
                      {issue.kind === 'missing_role'
                        ? t('setupHealth.missingRole')
                        : t('setupHealth.missingChannel')}
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}
      </section>

      <section className="flex flex-col gap-3 rounded-card border border-border bg-surface p-4">
        <div>
          <h2 className="font-medium text-foreground">{t('settings.botLanguage')}</h2>
          <p className="mt-1 text-sm text-muted">{t('settings.botLanguageHint')}</p>
        </div>
        <Select
          value={language}
          disabled={loading || busy}
          onChange={(id) => setLanguage(id as ServerLanguage['code'])}
          options={LANGUAGE_OPTIONS.map(({ value, labelKey }) => ({ id: value, name: t(labelKey) }))}
        />
        <div>
          <Button onClick={handleSave} disabled={loading || busy}>
            {busy ? t('common.saving') : t('common.save')}
          </Button>
        </div>
      </section>

      <section className="flex flex-col gap-3 rounded-card border border-border bg-surface p-4">
        <div className="flex items-start gap-2">
          <Clock size={20} className="mt-0.5 text-primary" />
          <div>
            <h2 className="font-medium text-foreground">{t('settings.timezone')}</h2>
            <p className="mt-1 text-sm text-muted">{t('settings.timezoneHint')}</p>
          </div>
        </div>
        {tzError && <p className="text-sm text-danger">{tzError}</p>}
        {tzSaved && <p className="text-sm text-success">{tzSaved}</p>}
        <Select
          value={timezone}
          disabled={tzBusy || timezoneChoices.length === 0}
          onChange={setTimezone}
          options={timezoneChoices.map((code) => ({ id: code, name: code }))}
        />
        <div>
          <Button onClick={saveTimezone} disabled={tzBusy || !timezone}>
            {tzBusy ? t('common.saving') : t('common.save')}
          </Button>
        </div>
      </section>

      <section className="flex flex-col gap-3 rounded-card border border-border bg-surface p-4">
        <div className="flex items-start gap-2">
          <Bell size={20} className="mt-0.5 text-primary" />
          <div>
            <h2 className="font-medium text-foreground">{t('ownerAlerts.title')}</h2>
            <p className="mt-1 text-sm text-muted">{t('ownerAlerts.intro')}</p>
          </div>
        </div>

        {alertsError && <p className="text-sm text-danger">{alertsError}</p>}
        {alertsSaved && <p className="text-sm text-success">{alertsSaved}</p>}

        <Toggle
          checked={alerts.enabled}
          onChange={(v) => setAlerts((a) => ({ ...a, enabled: v }))}
          label={t('ownerAlerts.enable')}
          disabled={alertsBusy}
        />
        <Toggle
          checked={alerts.notify_dm}
          onChange={(v) => setAlerts((a) => ({ ...a, notify_dm: v }))}
          label={t('ownerAlerts.notifyDm')}
          disabled={alertsBusy}
        />
        <Toggle
          checked={alerts.alert_missing_perms}
          onChange={(v) => setAlerts((a) => ({ ...a, alert_missing_perms: v }))}
          label={t('ownerAlerts.alertPerms')}
          disabled={alertsBusy}
        />
        <Toggle
          checked={alerts.alert_mass_ban}
          onChange={(v) => setAlerts((a) => ({ ...a, alert_mass_ban: v }))}
          label={t('ownerAlerts.alertBans')}
          disabled={alertsBusy}
        />
        <Toggle
          checked={alerts.alert_module_errors}
          onChange={(v) => setAlerts((a) => ({ ...a, alert_module_errors: v }))}
          label={t('ownerAlerts.alertErrors')}
          disabled={alertsBusy}
        />

        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted">{t('ownerAlerts.channel')}</label>
          <Select
            value={alerts.channel_id}
            onChange={(id) => setAlerts((a) => ({ ...a, channel_id: id }))}
            options={channels}
            placeholder={t('common.selectChannel')}
            disabled={alertsBusy}
          />
        </div>

        <div className="flex flex-col gap-2 border-t border-border pt-3">
          <Toggle
            checked={alerts.weekly_digest_enabled}
            onChange={(v) => setAlerts((a) => ({ ...a, weekly_digest_enabled: v }))}
            label={t('ownerAlerts.weeklyDigest.enable')}
            disabled={alertsBusy}
          />
          <p className="text-xs text-muted">{t('ownerAlerts.weeklyDigest.hint')}</p>
          {alerts.weekly_digest_enabled && (
            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted">{t('ownerAlerts.weeklyDigest.channel')}</label>
              <Select
                value={alerts.weekly_digest_channel_id}
                onChange={(id) => setAlerts((a) => ({ ...a, weekly_digest_channel_id: id }))}
                options={channels}
                placeholder={t('ownerAlerts.weeklyDigest.channelFallback')}
                disabled={alertsBusy}
              />
            </div>
          )}
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted">{t('ownerAlerts.massBanThreshold')}</label>
            <input
              type="number"
              min={2}
              max={50}
              value={alerts.mass_ban_threshold}
              onChange={(e) => setAlerts((a) => ({ ...a, mass_ban_threshold: Number(e.target.value) || 0 }))}
              className={inputClass}
              disabled={alertsBusy}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted">{t('ownerAlerts.massBanWindow')}</label>
            <input
              type="number"
              min={10}
              max={600}
              value={alerts.mass_ban_window_sec}
              onChange={(e) => setAlerts((a) => ({ ...a, mass_ban_window_sec: Number(e.target.value) || 0 }))}
              className={inputClass}
              disabled={alertsBusy}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted">{t('ownerAlerts.moduleErrors')}</label>
            <input
              type="number"
              min={2}
              max={100}
              value={alerts.module_error_threshold}
              onChange={(e) =>
                setAlerts((a) => ({ ...a, module_error_threshold: Number(e.target.value) || 0 }))
              }
              className={inputClass}
              disabled={alertsBusy}
            />
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button onClick={saveAlerts} disabled={alertsBusy || testBusy}>
            {alertsBusy ? t('common.saving') : t('common.save')}
          </Button>
          <Button variant="secondary" onClick={sendTestAlert} disabled={alertsBusy || testBusy}>
            {testBusy ? t('common.saving') : t('ownerAlerts.testSend')}
          </Button>
        </div>
      </section>
    </div>
  )
}

export function ServerSettingsPage() {
  const t = useT()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = parseSettingsTab(searchParams.get('tab'))
  const setTab = (next: SettingsTab) => {
    if (next === 'general') setSearchParams({}, { replace: true })
    else setSearchParams({ tab: next }, { replace: true })
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <GlobeHemisphereWest size={22} className="text-primary" />
          {t('settings.title')}
        </h1>
        <p className="mt-1 text-sm text-muted">{t('settings.intro')}</p>
      </div>

      <TabBar tab={tab} setTab={setTab} t={t} />

      {tab === 'general' && <GeneralSettings />}
      {tab === 'botProfile' && <BotProfilePage embedded />}
      {tab === 'customCommands' && <CustomCommandsPage embedded />}
      {tab === 'audit' && <AuditPage embedded />}
    </div>
  )
}
