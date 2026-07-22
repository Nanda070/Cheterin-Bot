import { useEffect, useMemo, useState } from 'react'
import {
  fetchChannels,
  fetchWelcomeSettings,
  updateWelcomeSettings,
  type ChannelInfo,
  type EmbedSpec,
  type WelcomeMessageSettings,
  type WelcomeSettings,
} from '../api/client'
import { EMPTY_EMBED_SPEC, EmbedEditor } from '../components/EmbedEditor'
import { EmbedPreview } from '../components/EmbedPreview'
import { ModuleConfigPanel } from '../components/ModuleConfigPanel'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'
import { AutoRolesPage } from './AutoRoles'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

const PREVIEW_VARS: Record<string, string> = {
  mention: '@User',
  name: 'User',
  guild_name: 'My Server',
  member_count: '100',
  announcements_channel: '#announcements',
  rules_channel: '#rules',
  roles_channel: '#roles',
  search_channel: '#search',
  guild: 'My Server',
  invite: 'https://discord.gg/example',
  user_id: '123456789',
}

function applyPreview(text: string) {
  return Object.entries(PREVIEW_VARS).reduce(
    (acc, [key, value]) => acc.replaceAll(`{${key}}`, value),
    text,
  )
}

function previewEmbed(embed: EmbedSpec): EmbedSpec {
  return {
    ...embed,
    title: applyPreview(embed.title),
    description: applyPreview(embed.description),
    footer: { ...embed.footer, text: applyPreview(embed.footer.text) },
    fields: embed.fields.map((f) => ({
      ...f,
      name: applyPreview(f.name),
      value: applyPreview(f.value),
    })),
  }
}

function emptyMessages(): WelcomeMessageSettings {
  return {
    channel_mode: 'text',
    channel_text: '',
    channel_embed: { ...EMPTY_EMBED_SPEC },
    dm_content: '',
    dm_embed: { ...EMPTY_EMBED_SPEC },
    dm_thumbnail_url: '',
    dm_fallback_thumbnail_url: '',
    dm_footer_text: '',
    dm_use_guild_icon: true,
    goodbye_text: '',
  }
}

export function ServerEntryPage() {
  const t = useT()
  const [settings, setSettings] = useState<WelcomeSettings | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [savedMessage, setSavedMessage] = useState('')

  useEffect(() => {
    Promise.all([fetchWelcomeSettings(), fetchChannels()])
      .then(([welcome, ch]) => {
        setSettings({
          ...welcome,
          messages: { ...emptyMessages(), ...welcome.messages },
        })
        setChannels(ch)
      })
      .catch(() => setError(t('welcome.errorLoad')))
  }, [t])

  const toggle = (key: 'channel_enabled' | 'dm_enabled' | 'goodbye_channel_enabled') => {
    setSettings((prev) => (prev ? { ...prev, [key]: !prev[key] } : prev))
  }

  const updateMessages = (patch: Partial<WelcomeMessageSettings>) => {
    setSettings((prev) =>
      prev ? { ...prev, messages: { ...prev.messages, ...patch } } : prev,
    )
  }

  const channelPreview = useMemo(() => {
    if (!settings) return { content: '', embed: EMPTY_EMBED_SPEC }
    const msgs = settings.messages
    if (msgs.channel_mode === 'embed') {
      const embed = previewEmbed(msgs.channel_embed)
      if (!embed.title && !embed.description && embed.fields.length === 0) {
        embed.title = applyPreview('{guild_name}')
        embed.description = t('welcome.previewChannelDefault')
      }
      return { content: '', embed }
    }
    const text = msgs.channel_text || t('welcome.previewChannelDefault')
    return { content: applyPreview(text), embed: EMPTY_EMBED_SPEC }
  }, [settings, t])

  const goodbyePreview = useMemo(() => {
    if (!settings) return ''
    const text = settings.messages.goodbye_text || t('welcome.previewGoodbyeDefault')
    return applyPreview(text)
  }, [settings, t])

  const saveWelcome = async () => {
    if (!settings) return
    setBusy(true)
    setError('')
    setSavedMessage('')
    try {
      const updated = await updateWelcomeSettings(settings)
      setSettings({ ...updated, messages: { ...emptyMessages(), ...updated.messages } })
      setSavedMessage(t('common.saved'))
    } catch {
      setError(t('welcome.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  if (!settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  return (
    <div className="flex max-w-5xl flex-col gap-8">
      <div>
        <h1 className="text-lg font-semibold text-foreground">{t('serverEntry.title')}</h1>
        <p className="mt-1 text-sm text-muted">{t('serverEntry.intro')}</p>
      </div>

      <section className="flex flex-col gap-4">
        <h2 className="font-semibold text-foreground">{t('welcome.title')}</h2>
        <p className="text-sm text-muted">{t('welcome.intro')}</p>
        <Card className="flex flex-col gap-3">
          <Toggle
            checked={settings.channel_enabled}
            onChange={() => toggle('channel_enabled')}
            label={t('welcome.channelEnabled')}
          />
          <Toggle
            checked={settings.dm_enabled}
            onChange={() => toggle('dm_enabled')}
            label={t('welcome.dmEnabled')}
          />
          <Toggle
            checked={settings.goodbye_channel_enabled}
            onChange={() => toggle('goodbye_channel_enabled')}
            label={t('welcome.goodbyeChannelEnabled')}
          />
          {settings.goodbye_channel_enabled && (
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="goodbye-channel">
                {t('welcome.goodbyeChannel')}
              </label>
              <Select
                id="goodbye-channel"
                value={settings.goodbye_channel_id}
                onChange={(id) => setSettings((prev) => (prev ? { ...prev, goodbye_channel_id: id } : prev))}
                options={channels}
                placeholder={t('welcome.goodbyeChannelFallback')}
              />
              <p className="text-xs text-muted">{t('welcome.goodbyeChannelHint')}</p>
            </div>
          )}
        </Card>
      </section>

      <section className="flex flex-col gap-4 border-t border-border pt-6">
        <h2 className="font-semibold text-foreground">{t('welcome.channelMessageTitle')}</h2>
        <div className="flex gap-2">
          {(['text', 'embed'] as const).map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => updateMessages({ channel_mode: mode })}
              className={`cursor-pointer rounded-control px-3 py-1.5 text-sm ${
                settings.messages.channel_mode === mode
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-surface text-muted hover:text-foreground'
              }`}
            >
              {mode === 'text' ? t('welcome.channelModeText') : t('welcome.channelModeEmbed')}
            </button>
          ))}
        </div>
        {settings.messages.channel_mode === 'text' ? (
          <div className="grid gap-4 lg:grid-cols-2">
            <textarea
              value={settings.messages.channel_text}
              onChange={(e) => updateMessages({ channel_text: e.target.value })}
              className={inputClass}
              rows={4}
              placeholder={t('welcome.previewChannelDefault')}
            />
            <div>
              <p className="mb-2 text-sm font-medium">{t('messageCustomizer.preview')}</p>
              <EmbedPreview content={channelPreview.content} embed={channelPreview.embed} />
            </div>
          </div>
        ) : (
          <EmbedEditor
            embed={settings.messages.channel_embed}
            onEmbedChange={(channel_embed) => updateMessages({ channel_embed })}
            showContent={false}
            placeholderHint={t('welcome.placeholderHint')}
          />
        )}
      </section>

      <section className="flex flex-col gap-4 border-t border-border pt-6">
        <h2 className="font-semibold text-foreground">{t('welcome.dmMessageTitle')}</h2>
        <Card className="flex flex-col gap-3">
          <label className="text-sm text-muted">{t('welcome.dmThumbnailUrl')}</label>
          <input
            value={settings.messages.dm_thumbnail_url}
            onChange={(e) => updateMessages({ dm_thumbnail_url: e.target.value })}
            className={inputClass}
            placeholder="https://..."
          />
          <label className="text-sm text-muted">{t('welcome.dmFallbackThumbnailUrl')}</label>
          <input
            value={settings.messages.dm_fallback_thumbnail_url}
            onChange={(e) => updateMessages({ dm_fallback_thumbnail_url: e.target.value })}
            className={inputClass}
            placeholder={t('welcome.dmFallbackThumbnailPlaceholder')}
          />
          <label className="text-sm text-muted">{t('welcome.dmFooterText')}</label>
          <input
            value={settings.messages.dm_footer_text}
            onChange={(e) => updateMessages({ dm_footer_text: e.target.value })}
            className={inputClass}
            placeholder={t('welcome.dmFooterPlaceholder')}
          />
          <Toggle
            checked={settings.messages.dm_use_guild_icon}
            onChange={(v) => updateMessages({ dm_use_guild_icon: v })}
            label={t('welcome.dmUseGuildIcon')}
          />
        </Card>
        <EmbedEditor
          content={settings.messages.dm_content}
          onContentChange={(dm_content) => updateMessages({ dm_content })}
          embed={settings.messages.dm_embed}
          onEmbedChange={(dm_embed) => updateMessages({ dm_embed })}
          placeholderHint={t('welcome.placeholderHint')}
        />
      </section>

      <section className="flex flex-col gap-4 border-t border-border pt-6">
        <h2 className="font-semibold text-foreground">{t('welcome.goodbyeMessageTitle')}</h2>
        <div className="grid gap-4 lg:grid-cols-2">
          <textarea
            value={settings.messages.goodbye_text}
            onChange={(e) => updateMessages({ goodbye_text: e.target.value })}
            className={inputClass}
            rows={3}
            placeholder={t('welcome.previewGoodbyeDefault')}
          />
          <div>
            <p className="mb-2 text-sm font-medium">{t('messageCustomizer.preview')}</p>
            <div className="rounded-card border border-border bg-background p-4 text-sm text-foreground">
              {goodbyePreview}
            </div>
          </div>
        </div>
      </section>

      {error && <p className="text-sm text-danger">{error}</p>}
      {savedMessage && <p className="text-sm text-primary">{savedMessage}</p>}
      <div>
        <Button variant="primary" onClick={saveWelcome} disabled={busy}>
          {busy ? t('common.saving') : t('common.save')}
        </Button>
      </div>

      <section className="flex flex-col gap-4 border-t border-border pt-6">
        <ModuleConfigPanel
          variant="welcome-onboarding"
          title={t('config.section.welcome')}
          intro={t('serverEntry.onboardingHint')}
        />
      </section>

      <section className="flex flex-col gap-4 border-t border-border pt-6">
        <AutoRolesPage embedded />
      </section>
    </div>
  )
}
