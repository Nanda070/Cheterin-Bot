import { UserCheck } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { fetchVerificationSettings, updateVerificationSettings, type VerificationSettings } from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Toggle } from '../components/ui/Toggle'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

export function VerificationPage() {
  const [settings, setSettings] = useState<VerificationSettings | null>(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    fetchVerificationSettings()
      .then(setSettings)
      .catch(() => setError('Не удалось загрузить настройки модуля «Верификация»'))
  }, [])

  if (!settings) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateVerificationSettings(settings)
      setSettings(updated)
      setSaved('Сохранено.')
    } catch {
      setError('Не удалось сохранить настройки — проверьте поля')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <UserCheck size={22} className="text-primary" />
          Верификация
        </h1>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => setSettings({ ...settings, enabled: v })}
          label={settings.enabled ? 'Модуль включён' : 'Модуль выключен'}
        />
      </div>
      <p className="text-sm text-muted">
        Модуль <strong>выключен по умолчанию</strong> и не имеет никакого эффекта, пока вы явно не включите его здесь
        — не связан с остальными настройками бота. При включении новичкам можно выдавать роль «Unverified» сразу при
        входе (доступ к каналам ограничивается вашими же правами Discord для этой роли), а панель с кнопкой «Я не
        бот» публикуется командой <code className="rounded bg-background px-1 py-0.5 text-xs">/verify_setup</code> в
        любом канале.
      </p>

      {error && <p className="text-sm text-danger">{error}</p>}

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">Роли</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="ver-unverified">
              ID роли «Unverified» (пусто — не выдавать роль при входе)
            </label>
            <input
              id="ver-unverified"
              type="text"
              inputMode="numeric"
              placeholder="ID роли"
              value={settings.unverified_role_id}
              onChange={(e) => setSettings({ ...settings, unverified_role_id: e.target.value.replace(/\D/g, '') })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="ver-verified">
              ID роли «Verified» (обязательно для работы кнопки)
            </label>
            <input
              id="ver-verified"
              type="text"
              inputMode="numeric"
              placeholder="ID роли"
              value={settings.verified_role_id}
              onChange={(e) => setSettings({ ...settings, verified_role_id: e.target.value.replace(/\D/g, '') })}
              className={inputClass}
            />
          </div>
        </div>
        <p className="text-xs text-muted">
          Ограничение доступа к каналам для роли «Unverified» настраивается правами Discord вами самими — бот только
          назначает и снимает роль, а не управляет разрешениями каналов.
        </p>
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">Текст панели</h2>
        <textarea
          rows={3}
          maxLength={1000}
          value={settings.welcome_text}
          onChange={(e) => setSettings({ ...settings, welcome_text: e.target.value })}
          className={inputClass}
        />
      </Card>

      {saved && <p className="text-sm text-primary">{saved}</p>}
      <div>
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? 'Сохраняем…' : 'Сохранить'}
        </Button>
      </div>
    </div>
  )
}
