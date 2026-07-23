import { Bell, GlobeHemisphereWest } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  fetchChannels,
  fetchLanguage,
  fetchOwnerAlerts,
  updateLanguage,
  updateOwnerAlerts,
  type ChannelInfo,
  type OwnerAlertsSettings,
  type ServerLanguage,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

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
}

export function ServerSettingsPage() {
  const t = useT()
  const [language, setLanguage] = useState<ServerLanguage['code']>('ru')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [savedMessage, setSavedMessage] = useState('')

  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [alerts, setAlerts] = useState<OwnerAlertsSettings>(defaultAlerts)
  const [alertsBusy, setAlertsBusy] = useState(false)
  const [alertsError, setAlertsError] = useState('')
  const [alertsSaved, setAlertsSaved] = useState('')

  useEffect(() => {
    fetchLanguage()
      .then((data) => setLanguage(data.code))
      .catch(() => setError(t('settings.errorLoad')))
      .finally(() => setLoading(false))

    fetchOwnerAlerts()
      .then(setAlerts)
      .catch((err) => setAlertsError(formatApiError(err, t, 'ownerAlerts.errorLoad')))

    fetchChannels()
      .then(setChannels)
      .catch(() => setChannels([]))
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

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <div>
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <GlobeHemisphereWest size={22} className="text-primary" />
          {t('settings.title')}
        </h1>
        <p className="mt-1 text-sm text-muted">{t('settings.intro')}</p>
      </div>

      {error && (
        <div className="rounded-control border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</div>
      )}
      {savedMessage && (
        <div className="rounded-control border border-success/40 bg-success/10 px-4 py-3 text-sm text-success">
          {savedMessage}
        </div>
      )}

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
              onChange={(e) => setAlerts((a) => ({ ...a, module_error_threshold: Number(e.target.value) || 0 }))}
              className={inputClass}
              disabled={alertsBusy}
            />
          </div>
        </div>

        <div>
          <Button onClick={saveAlerts} disabled={alertsBusy}>
            {alertsBusy ? t('common.saving') : t('common.save')}
          </Button>
        </div>
      </section>
    </div>
  )
}
