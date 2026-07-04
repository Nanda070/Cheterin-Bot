import { useEffect, useState } from 'react'
import { fetchWelcomeSettings, updateWelcomeSettings, type WelcomeSettings } from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'

export function WelcomePage() {
  const [settings, setSettings] = useState<WelcomeSettings | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [savedMessage, setSavedMessage] = useState('')

  useEffect(() => {
    fetchWelcomeSettings()
      .then(setSettings)
      .catch(() => setError('Не удалось загрузить настройки'))
  }, [])

  const toggle = (key: keyof WelcomeSettings) => {
    setSettings((prev) => (prev ? { ...prev, [key]: !prev[key] } : prev))
  }

  const save = async () => {
    if (!settings) return
    setBusy(true)
    setError('')
    setSavedMessage('')
    try {
      const updated = await updateWelcomeSettings(settings)
      setSettings(updated)
      setSavedMessage('Сохранено.')
    } catch {
      setError('Не удалось сохранить настройки')
    } finally {
      setBusy(false)
    }
  }

  if (!settings) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
  }

  return (
    <div className="flex max-w-xl flex-col gap-4">
      <h1 className="text-lg font-semibold text-foreground">Приветствие и прощание</h1>

      <Card className="flex flex-col gap-3">
        <label className="flex items-center gap-2 text-sm text-foreground">
          <input
            type="checkbox"
            checked={settings.channel_enabled}
            onChange={() => toggle('channel_enabled')}
          />
          Отправлять приветствие в канал
        </label>
        <label className="flex items-center gap-2 text-sm text-foreground">
          <input type="checkbox" checked={settings.dm_enabled} onChange={() => toggle('dm_enabled')} />
          Отправлять приветствие в личные сообщения
        </label>
        <p className="text-xs text-muted">Канал для приветствий выбирается на странице «Конфигурация».</p>
      </Card>

      {error && <p className="text-sm text-danger">{error}</p>}
      {savedMessage && <p className="text-sm text-primary">{savedMessage}</p>}

      <div>
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? 'Сохраняем…' : 'Сохранить'}
        </Button>
      </div>
    </div>
  )
}
