import { useEffect, useState } from 'react'
import {
  fetchChannels,
  fetchConfig,
  fetchRoles,
  updateConfig,
  type BotConfig,
  type ChannelInfo,
  type RoleInfo,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'

const EMPTY_CONFIG: BotConfig = {
  LOG_CHANNEL_ID: '',
  SPAM_EXCEPTION_CHANNELS: [],
  TEMPBAN_CHANNEL_ID: '',
  SPAM_LOG_CHANNEL_ID: '',
  SPAM_LOG_ROLE_ID: '',
  WELCOME_CHANNEL_ID: '',
  INVITE_LOG_CHANNEL_ID: '',
  ANNOUNCEMENTS_CHANNEL_ID: '',
  RULES_CHANNEL_ID: '',
  ROLES_CHANNEL_ID: '',
  SEARCH_PLAYERS_CHANNEL_ID: '',
  CTD_ROLE_ID: '',
  CTD_CHANNEL_ID: '',
  BUTTON_CREATE_ALLOWED_ROLES: [],
  BUTTON_WEBHOOK_URL: '',
  SERVER_INVITE_LINK: '',
}

export function ConfigPage() {
  const [config, setConfig] = useState<BotConfig>(EMPTY_CONFIG)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [savedMessage, setSavedMessage] = useState('')

  useEffect(() => {
    Promise.all([fetchConfig(), fetchChannels(), fetchRoles()])
      .then(([cfg, ch, rl]) => {
        setConfig(cfg)
        setChannels(ch)
        setRoles(rl)
      })
      .catch(() => setError('Не удалось загрузить конфигурацию'))
      .finally(() => setLoading(false))
  }, [])

  const setField = (key: keyof BotConfig, value: string) => {
    setConfig((prev) => ({ ...prev, [key]: value }))
  }

  const toggleListField = (key: 'SPAM_EXCEPTION_CHANNELS' | 'BUTTON_CREATE_ALLOWED_ROLES', id: string) => {
    setConfig((prev) => ({
      ...prev,
      [key]: prev[key].includes(id) ? prev[key].filter((v) => v !== id) : [...prev[key], id],
    }))
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSavedMessage('')
    try {
      const updated = await updateConfig(config)
      setConfig(updated)
      setSavedMessage('Сохранено.')
    } catch {
      setError('Не удалось сохранить конфигурацию — проверьте поля')
    } finally {
      setBusy(false)
    }
  }

  const channelField = (label: string, key: keyof BotConfig) => (
    <div key={key} className="flex flex-col gap-1">
      <label className="text-sm text-muted" htmlFor={key}>
        {label}
      </label>
      <select
        id={key}
        value={config[key] as string}
        onChange={(e) => setField(key, e.target.value)}
        className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
      >
        <option value="">Не задано</option>
        {channels.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
          </option>
        ))}
      </select>
    </div>
  )

  const roleField = (label: string, key: keyof BotConfig) => (
    <div key={key} className="flex flex-col gap-1">
      <label className="text-sm text-muted" htmlFor={key}>
        {label}
      </label>
      <select
        id={key}
        value={config[key] as string}
        onChange={(e) => setField(key, e.target.value)}
        className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
      >
        <option value="">Не задано</option>
        {roles.map((r) => (
          <option key={r.id} value={r.id}>
            {r.name}
          </option>
        ))}
      </select>
    </div>
  )

  const textField = (label: string, key: keyof BotConfig) => (
    <div key={key} className="flex flex-col gap-1">
      <label className="text-sm text-muted" htmlFor={key}>
        {label}
      </label>
      <input
        id={key}
        value={config[key] as string}
        onChange={(e) => setField(key, e.target.value)}
        className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
      />
    </div>
  )

  if (loading) {
    return <p className="text-sm text-muted">Загрузка…</p>
  }

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <h1 className="text-lg font-semibold text-foreground">Конфигурация</h1>

      {error && <p className="text-sm text-danger">{error}</p>}
      {savedMessage && <p className="text-sm text-primary">{savedMessage}</p>}

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">Модерация/спам</h2>
        {channelField('Канал логов', 'LOG_CHANNEL_ID')}
        {channelField('Канал Tempban', 'TEMPBAN_CHANNEL_ID')}
        {channelField('Канал логов спама', 'SPAM_LOG_CHANNEL_ID')}
        {roleField('Роль для пинга при спаме', 'SPAM_LOG_ROLE_ID')}
        <div>
          <p className="mb-1 text-sm text-muted">Каналы-исключения из анти-спама</p>
          <div className="flex flex-wrap gap-2">
            {channels.map((c) => (
              <label key={c.id} className="flex items-center gap-1 text-xs text-foreground">
                <input
                  type="checkbox"
                  checked={config.SPAM_EXCEPTION_CHANNELS.includes(c.id)}
                  onChange={() => toggleListField('SPAM_EXCEPTION_CHANNELS', c.id)}
                />
                {c.name}
              </label>
            ))}
          </div>
        </div>
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">Приветствия/онбординг</h2>
        {channelField('Канал приветствий', 'WELCOME_CHANNEL_ID')}
        {channelField('Канал лога приглашений', 'INVITE_LOG_CHANNEL_ID')}
        {channelField('Канал объявлений', 'ANNOUNCEMENTS_CHANNEL_ID')}
        {channelField('Канал правил', 'RULES_CHANNEL_ID')}
        {channelField('Канал ролей', 'ROLES_CHANNEL_ID')}
        {channelField('Канал поиска игроков', 'SEARCH_PLAYERS_CHANNEL_ID')}
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">CTD</h2>
        {roleField('Роль CTD', 'CTD_ROLE_ID')}
        {channelField('Канал CTD', 'CTD_CHANNEL_ID')}
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">Кнопки/вебхуки</h2>
        <div>
          <p className="mb-1 text-sm text-muted">Роли, которым разрешено создавать кнопки</p>
          <div className="flex flex-wrap gap-2">
            {roles.map((r) => (
              <label key={r.id} className="flex items-center gap-1 text-xs text-foreground">
                <input
                  type="checkbox"
                  checked={config.BUTTON_CREATE_ALLOWED_ROLES.includes(r.id)}
                  onChange={() => toggleListField('BUTTON_CREATE_ALLOWED_ROLES', r.id)}
                />
                {r.name}
              </label>
            ))}
          </div>
        </div>
        {textField('URL вебхука для кнопок', 'BUTTON_WEBHOOK_URL')}
        {textField('Ссылка-приглашение сервера', 'SERVER_INVITE_LINK')}
      </Card>

      <div>
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? 'Сохраняем…' : 'Сохранить'}
        </Button>
      </div>
    </div>
  )
}
