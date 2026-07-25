import { UserCheck } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { fetchVerificationSettings, updateVerificationSettings, type VerificationSettings } from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

export function VerificationPage() {
  const t = useT()
  const [settings, setSettings] = useState<VerificationSettings | null>(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    fetchVerificationSettings()
      .then(setSettings)
      .catch(() => setError(t('verification.errorLoad')))
  }, [t])

  if (!settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateVerificationSettings(settings)
      setSettings(updated)
      setSaved(t('common.saved'))
    } catch (err) {
      setError(formatApiError(err, t, 'verification.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <UserCheck size={22} className="text-primary" />
          {t('verification.title')}
        </h1>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => setSettings({ ...settings, enabled: v })}
          label={settings.enabled ? t('verification.moduleOn') : t('verification.moduleOff')}
        />
      </div>
      <p className="text-sm text-muted">
        {t('verification.intro.beforeBold')}
        <strong>{t('verification.intro.bold')}</strong>
        {t('verification.intro.afterBold')}
      </p>

      {error && <p className="text-sm text-danger">{error}</p>}

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">{t('verification.rolesTitle')}</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="ver-unverified">
              {t('verification.unverifiedRole')}
            </label>
            <input
              id="ver-unverified"
              type="text"
              inputMode="numeric"
              placeholder={t('verification.rolePlaceholder')}
              value={settings.unverified_role_id}
              onChange={(e) => setSettings({ ...settings, unverified_role_id: e.target.value.replace(/\D/g, '') })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="ver-verified">
              {t('verification.verifiedRole')}
            </label>
            <input
              id="ver-verified"
              type="text"
              inputMode="numeric"
              placeholder={t('verification.rolePlaceholder')}
              value={settings.verified_role_id}
              onChange={(e) => setSettings({ ...settings, verified_role_id: e.target.value.replace(/\D/g, '') })}
              className={inputClass}
            />
          </div>
        </div>
        <p className="text-xs text-muted">{t('verification.rolesHint')}</p>
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">{t('verification.panelTextTitle')}</h2>
        <textarea
          rows={3}
          maxLength={1000}
          value={settings.welcome_text}
          onChange={(e) => setSettings({ ...settings, welcome_text: e.target.value })}
          className={inputClass}
        />
      </Card>

      <Card className="flex flex-col gap-3">
        <div className="flex items-center justify-between gap-3">
          <h2 className="font-semibold text-foreground">{t('verification.rulesTitle')}</h2>
          <Toggle
            checked={settings.rules_consent_enabled}
            onChange={(v) => setSettings({ ...settings, rules_consent_enabled: v })}
            label={
              settings.rules_consent_enabled
                ? t('verification.rulesOn')
                : t('verification.rulesOff')
            }
          />
        </div>
        <p className="text-sm text-muted">{t('verification.rulesHint')}</p>

        <div className="flex items-center justify-between gap-3 border-t border-border pt-3">
          <div className="flex flex-col gap-1">
            <span className="text-sm font-medium text-foreground">{t('verification.reverifyTitle')}</span>
            <span className="text-xs text-muted">{t('verification.reverifyHint')}</span>
          </div>
          <Toggle
            checked={settings.reverify_enabled}
            onChange={(v) => setSettings({ ...settings, reverify_enabled: v })}
            label={
              settings.reverify_enabled
                ? t('verification.reverifyOn')
                : t('verification.reverifyOff')
            }
          />
        </div>

        {settings.reverify_enabled && (
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="ver-reverify-days">
              {t('verification.reverifyDays')}
            </label>
            <input
              id="ver-reverify-days"
              type="number"
              min={1}
              max={365}
              value={settings.reverify_days}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  reverify_days: Math.max(1, Math.min(365, Number(e.target.value) || 1)),
                })
              }
              className={`${inputClass} w-32`}
            />
          </div>
        )}
      </Card>

      {saved && <p className="text-sm text-primary">{saved}</p>}
      <div>
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? t('common.saving') : t('common.save')}
        </Button>
      </div>
    </div>
  )
}
