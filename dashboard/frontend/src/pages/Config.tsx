import {
  GearSix,
  HandWaving,
  Headset,
  LinkSimple,
  Package,
  ShieldWarning,
  type Icon,
} from '@phosphor-icons/react'
import { useEffect, useState, type ReactNode } from 'react'
import {
  fetchChannels,
  fetchConfig,
  fetchRoles,
  updateConfig,
  type BotConfig,
  type ChannelInfo,
  type RoleInfo,
} from '../api/client'
import { ChipPicker } from '../components/ChipPicker'
import { Button } from '../components/ui/Button'
import { Select } from '../components/ui/Select'

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
  BUTTON_CREATE_ALLOWED_ROLES: [],
  BUTTON_WEBHOOK_URL: '',
  SERVER_INVITE_LINK: '',
  VOICE_LOBBY_CHANNEL_ID: '',
  VOICE_PANEL_CHANNEL_ID: '',
  VOICE_LOG_CHANNEL_ID: '',
  VOICE_PANEL_THUMB_URL: '',
  SUPPLY_ROLE_ID: '',
  SUPPLY_VOICE_CHANNEL_ID: '',
  SUPPLY_LOG_CHANNEL_ID: '',
  SUPPLY_REMINDER_MINUTES: '',
}

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-primary'

function Section({ icon: SectionIcon, title, children }: { icon: Icon; title: string; children: ReactNode }) {
  return (
    <section className="animate-fade-in-up flex flex-col gap-3 rounded-card border border-border bg-surface p-4">
      <h2 className="flex items-center gap-2 font-semibold text-foreground">
        <span className="flex h-8 w-8 items-center justify-center rounded-control bg-primary-muted">
          <SectionIcon size={17} className="text-primary" />
        </span>
        {title}
      </h2>
      {children}
    </section>
  )
}

export function ConfigPage() {
  const [config, setConfig] = useState<BotConfig>(EMPTY_CONFIG)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [savedMessage, setSavedMessage] = useState('')
  const [dirty, setDirty] = useState(false)

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
    setDirty(true)
    setSavedMessage('')
  }

  const setListField = (key: 'SPAM_EXCEPTION_CHANNELS' | 'BUTTON_CREATE_ALLOWED_ROLES', ids: string[]) => {
    setConfig((prev) => ({ ...prev, [key]: ids }))
    setDirty(true)
    setSavedMessage('')
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSavedMessage('')
    try {
      const updated = await updateConfig(config)
      setConfig(updated)
      setSavedMessage('Сохранено.')
      setDirty(false)
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
      <Select
        id={key}
        value={config[key] as string}
        onChange={(id) => setField(key, id)}
        options={channels}
        placeholder="Не задано"
      />
    </div>
  )

  const roleField = (label: string, key: keyof BotConfig) => (
    <div key={key} className="flex flex-col gap-1">
      <label className="text-sm text-muted" htmlFor={key}>
        {label}
      </label>
      <Select
        id={key}
        value={config[key] as string}
        onChange={(id) => setField(key, id)}
        options={roles}
        placeholder="Не задано"
      />
    </div>
  )

  const textField = (label: string, key: keyof BotConfig, placeholder = '') => (
    <div key={key} className="flex flex-col gap-1">
      <label className="text-sm text-muted" htmlFor={key}>
        {label}
      </label>
      <input
        id={key}
        value={config[key] as string}
        placeholder={placeholder}
        onChange={(e) => setField(key, e.target.value)}
        className={inputClass}
      />
    </div>
  )

  if (loading) {
    return <p className="text-sm text-muted">Загрузка…</p>
  }

  return (
    <div className="flex max-w-5xl flex-col gap-5 pb-20">
      <div>
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <GearSix size={22} className="text-primary" />
          Конфигурация
        </h1>
        <p className="mt-1 text-sm text-muted">
          Каналы, роли и параметры модулей. Изменения применяются сразу после сохранения — без перезапуска бота.
        </p>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      <div className="grid gap-4 lg:grid-cols-2">
        <Section icon={ShieldWarning} title="Модерация и спам">
          {channelField('Канал логов', 'LOG_CHANNEL_ID')}
          {channelField('Канал Tempban', 'TEMPBAN_CHANNEL_ID')}
          {channelField('Канал логов спама', 'SPAM_LOG_CHANNEL_ID')}
          {roleField('Роль для пинга при спаме', 'SPAM_LOG_ROLE_ID')}
          <ChipPicker
            label="Каналы-исключения из анти-спама"
            options={channels}
            selected={config.SPAM_EXCEPTION_CHANNELS}
            onChange={(ids) => setListField('SPAM_EXCEPTION_CHANNELS', ids)}
          />
        </Section>

        <Section icon={HandWaving} title="Приветствия и онбординг">
          {channelField('Канал приветствий', 'WELCOME_CHANNEL_ID')}
          {channelField('Канал лога приглашений', 'INVITE_LOG_CHANNEL_ID')}
          {channelField('Канал объявлений', 'ANNOUNCEMENTS_CHANNEL_ID')}
          {channelField('Канал правил', 'RULES_CHANNEL_ID')}
          {channelField('Канал ролей', 'ROLES_CHANNEL_ID')}
          {channelField('Канал поиска игроков', 'SEARCH_PLAYERS_CHANNEL_ID')}
        </Section>

        <Section icon={LinkSimple} title="Кнопки и вебхуки">
          <ChipPicker
            label="Роли, которым разрешено создавать кнопки"
            options={roles.map((r) => ({ id: r.id, name: r.name }))}
            selected={config.BUTTON_CREATE_ALLOWED_ROLES}
            onChange={(ids) => setListField('BUTTON_CREATE_ALLOWED_ROLES', ids)}
          />
          {textField('URL вебхука для кнопок', 'BUTTON_WEBHOOK_URL', 'https://discord.com/api/webhooks/…')}
          {textField('Ссылка-приглашение сервера', 'SERVER_INVITE_LINK', 'https://discord.gg/…')}
        </Section>

        <Section icon={Headset} title="Приватные комнаты">
          {channelField('Голосовое лобби (вход = создать комнату)', 'VOICE_LOBBY_CHANNEL_ID')}
          {channelField('Канал панели управления', 'VOICE_PANEL_CHANNEL_ID')}
          {channelField('Канал логов приватных комнат', 'VOICE_LOG_CHANNEL_ID')}
          {textField('URL картинки панели (thumbnail)', 'VOICE_PANEL_THUMB_URL', 'https://…')}
        </Section>

        <Section icon={Package} title="Поставки">
          {roleField('Роль для пинга при сборе', 'SUPPLY_ROLE_ID')}
          {channelField('Голосовой канал сбора', 'SUPPLY_VOICE_CHANNEL_ID')}
          {channelField('Канал логов поставок', 'SUPPLY_LOG_CHANNEL_ID')}
          {textField('Напоминание за N минут до начала (пусто = 10)', 'SUPPLY_REMINDER_MINUTES', '10')}
        </Section>
      </div>

      <div className="fixed inset-x-0 bottom-0 z-10 border-t border-border bg-background/95 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-3 px-6 py-3">
          <span className="text-sm text-muted">
            {savedMessage ? (
              <span className="text-primary">{savedMessage}</span>
            ) : dirty ? (
              'Есть несохранённые изменения'
            ) : (
              'Все изменения сохранены'
            )}
          </span>
          <Button variant="primary" onClick={save} disabled={busy || !dirty}>
            {busy ? 'Сохраняем…' : 'Сохранить'}
          </Button>
        </div>
      </div>
    </div>
  )
}
