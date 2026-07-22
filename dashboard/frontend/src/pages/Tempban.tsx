import { Clock } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { fetchTempbanSettings, updateTempbanSettings, type TempbanSettings } from '../api/client'
import { ModuleConfigPanel } from '../components/ModuleConfigPanel'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

export function TempbanPage() {
  const t = useT()
  const [tempban, setTempban] = useState<TempbanSettings | null>(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    fetchTempbanSettings()
      .then(setTempban)
      .catch(() => setError(t('tempban.errorLoad')))
  }, [t])

  const save = async () => {
    if (!tempban) return
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateTempbanSettings(tempban)
      setTempban(updated)
      setSaved(t('common.saved'))
    } catch {
      setError(t('tempban.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  if (!tempban) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div>
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Clock size={22} className="text-primary" />
          {t('tempban.title')}
        </h1>
        <p className="mt-1 text-sm text-muted">{t('tempban.intro')}</p>
      </div>

      <ModuleConfigPanel
        variant="tempban"
        title={t('tempban.channelsTitle')}
        intro={t('tempban.channelsIntro')}
      />

      <section className="flex flex-col gap-4 border-t border-border pt-6">
        <h2 className="font-semibold text-foreground">{t('messageCustomizer.tempbanTitle')}</h2>
        <p className="text-sm text-muted">{t('messageCustomizer.tempbanIntro')}</p>
        <Card className="flex flex-col gap-3">
          <Toggle
            checked={tempban.dm_enabled}
            onChange={(v) => setTempban({ ...tempban, dm_enabled: v })}
            label={t('messageCustomizer.tempbanDmEnabled')}
          />
          <label className="text-sm text-muted">{t('messageCustomizer.tempbanDmMessage')}</label>
          <textarea
            value={tempban.dm_message}
            onChange={(e) => setTempban({ ...tempban, dm_message: e.target.value })}
            className={inputClass}
            rows={4}
          />
          <Toggle
            checked={tempban.log_enabled}
            onChange={(v) => setTempban({ ...tempban, log_enabled: v })}
            label={t('messageCustomizer.tempbanLogEnabled')}
          />
          <p className="text-xs text-muted">{t('messageCustomizer.tempbanLogFixedHint')}</p>
          <label className="text-sm text-muted">{t('messageCustomizer.tempbanUnbanReason')}</label>
          <input
            value={tempban.unban_reason}
            onChange={(e) => setTempban({ ...tempban, unban_reason: e.target.value })}
            className={inputClass}
          />
        </Card>
        {error && <p className="text-sm text-danger">{error}</p>}
        {saved && <p className="text-sm text-primary">{saved}</p>}
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? t('common.saving') : t('common.save')}
        </Button>
      </section>
    </div>
  )
}
