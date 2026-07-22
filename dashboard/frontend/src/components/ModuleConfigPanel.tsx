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
import { formatApiError } from '../api/errors'
import { ChipPicker } from './ChipPicker'
import { Button } from './ui/Button'
import { Select } from './ui/Select'
import { useT } from '../context/LanguageContext'
import { EMPTY_BOT_CONFIG, type ModuleConfigVariant } from '../config/botConfigDefaults'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-primary'

interface ModuleConfigPanelProps {
  variant: ModuleConfigVariant
  title?: string
  intro?: string
  children?: ReactNode
}

export function ModuleConfigPanel({ variant, title, intro, children }: ModuleConfigPanelProps) {
  const t = useT()
  const [config, setConfig] = useState<BotConfig>(EMPTY_BOT_CONFIG)
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
      .catch(() => setError(t('config.errorLoad')))
      .finally(() => setLoading(false))
  }, [t])

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
      setSavedMessage(t('common.saved'))
      setDirty(false)
    } catch (err) {
      setError(formatApiError(err, t, 'config.errorSave'))
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
        placeholder={t('common.notSet')}
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
        placeholder={t('common.notSet')}
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

  const fields = () => {
    switch (variant) {
      case 'moderation':
        return channelField(t('config.field.logChannel'), 'LOG_CHANNEL_ID')
      case 'antispam':
        return (
          <>
            {channelField(t('config.field.spamLogChannel'), 'SPAM_LOG_CHANNEL_ID')}
            {roleField(t('config.field.spamLogRole'), 'SPAM_LOG_ROLE_ID')}
            <ChipPicker
              label={t('config.field.spamExceptions')}
              options={channels}
              selected={config.SPAM_EXCEPTION_CHANNELS}
              onChange={(ids) => setListField('SPAM_EXCEPTION_CHANNELS', ids)}
            />
          </>
        )
      case 'tempban':
        return (
          <>
            {channelField(t('config.field.tempbanChannel'), 'TEMPBAN_CHANNEL_ID')}
            {channelField(t('config.field.tempbanLogChannel'), 'TEMPBAN_LOG_CHANNEL_ID')}
            {textField(t('config.field.serverInviteLink'), 'SERVER_INVITE_LINK', t('config.placeholder.invite'))}
          </>
        )
      case 'welcome-onboarding':
        return (
          <>
            {channelField(t('config.field.welcomeChannel'), 'WELCOME_CHANNEL_ID')}
            {channelField(t('config.field.inviteLogChannel'), 'INVITE_LOG_CHANNEL_ID')}
            {channelField(t('config.field.announcementsChannel'), 'ANNOUNCEMENTS_CHANNEL_ID')}
            {channelField(t('config.field.rulesChannel'), 'RULES_CHANNEL_ID')}
            {channelField(t('config.field.rolesChannel'), 'ROLES_CHANNEL_ID')}
            {channelField(t('config.field.searchPlayersChannel'), 'SEARCH_PLAYERS_CHANNEL_ID')}
          </>
        )
      case 'buttons':
        return (
          <>
            <ChipPicker
              label={t('config.field.buttonAllowedRoles')}
              options={roles.map((r) => ({ id: r.id, name: r.name }))}
              selected={config.BUTTON_CREATE_ALLOWED_ROLES}
              onChange={(ids) => setListField('BUTTON_CREATE_ALLOWED_ROLES', ids)}
            />
            {textField(t('config.field.buttonWebhookUrl'), 'BUTTON_WEBHOOK_URL', t('config.placeholder.webhook'))}
            {textField(
              t('config.field.buttonWebhookUsername'),
              'BUTTON_WEBHOOK_USERNAME',
              t('config.placeholder.buttonWebhookUsername'),
            )}
            {textField(
              t('config.field.buttonWebhookAvatarUrl'),
              'BUTTON_WEBHOOK_AVATAR_URL',
              t('config.placeholder.image'),
            )}
            {textField(t('config.field.serverInviteLink'), 'SERVER_INVITE_LINK', t('config.placeholder.invite'))}
          </>
        )
      case 'voice':
        return (
          <>
            {channelField(t('config.field.voiceLobby'), 'VOICE_LOBBY_CHANNEL_ID')}
            {channelField(t('config.field.voicePanel'), 'VOICE_PANEL_CHANNEL_ID')}
            {channelField(t('config.field.voiceLog'), 'VOICE_LOG_CHANNEL_ID')}
            {textField(t('config.field.voiceThumbUrl'), 'VOICE_PANEL_THUMB_URL', t('config.placeholder.image'))}
          </>
        )
      case 'supply':
        return (
          <>
            {roleField(t('config.field.supplyRole'), 'SUPPLY_ROLE_ID')}
            {channelField(t('config.field.supplyVoice'), 'SUPPLY_VOICE_CHANNEL_ID')}
            {channelField(t('config.field.supplyLog'), 'SUPPLY_LOG_CHANNEL_ID')}
            {textField(t('config.field.supplyReminder'), 'SUPPLY_REMINDER_MINUTES', t('config.placeholder.reminder'))}
          </>
        )
      default:
        return null
    }
  }

  if (loading) {
    return <p className="text-sm text-muted">{t('common.loading')}</p>
  }

  return (
    <div className="flex flex-col gap-4">
      {title && <h2 className="font-semibold text-foreground">{title}</h2>}
      {intro && <p className="text-sm text-muted">{intro}</p>}
      {children}
      <div className="flex flex-col gap-3">{fields()}</div>
      {error && <p className="text-sm text-danger">{error}</p>}
      {savedMessage && <p className="text-sm text-primary">{savedMessage}</p>}
      <div>
        <Button variant="primary" onClick={save} disabled={busy || !dirty}>
          {busy ? t('common.saving') : t('common.save')}
        </Button>
      </div>
    </div>
  )
}
