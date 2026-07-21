import { useEffect, useState } from 'react'
import { fetchWelcomeSettings, updateWelcomeSettings, type WelcomeSettings } from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Toggle } from '../components/ui/Toggle'

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
      <p className="text-sm text-muted">
        Бот автоматически приветствует новых участников при входе на сервер (в выбранном канале или в ЛС) и прощается при выходе. 
        Внешний вид сообщений задаётся через шаблоны в модуле Embed Builder.
      </p>

      <Card className="flex flex-col gap-3">
        <Toggle
          checked={settings.channel_enabled}
          onChange={() => toggle('channel_enabled')}
          label="Отправлять приветствие в канал"
        />
        <Toggle
          checked={settings.dm_enabled}
          onChange={() => toggle('dm_enabled')}
          label="Отправлять приветствие в личные сообщения"
        />
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
