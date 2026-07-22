import { ChatCircle, EnvelopeSimple, GearSix, UsersThree } from '@phosphor-icons/react'
import { useEffect, useMemo, useState } from 'react'
import {
  fetchChannels,
  fetchConfig,
  fetchWelcomeSettings,
  updateConfig,
  updateWelcomeSettings,
  type BotConfig,
  type ChannelInfo,
  type EmbedSpec,
  type WelcomeMessageSettings,
  type WelcomeSettings,
} from '../api/client'
import { EMPTY_EMBED_SPEC, EmbedEditor } from '../components/EmbedEditor'
import { EmbedPreview } from '../components/EmbedPreview'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { EMPTY_BOT_CONFIG } from '../config/botConfigDefaults'
import {
  buildDefaultDmEmbed,
  DEFAULT_DM_THUMBNAIL_URL,
  embedHasContent,
} from '../config/welcomeDmDefaults'
import { useLanguage, useT } from '../context/LanguageContext'
import { AutoRolesPage } from './AutoRoles'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

type Tab = 'welcome' | 'greeting' | 'autoroles'

const ONBOARDING_CHANNEL_KEYS = [
  'WELCOME_CHANNEL_ID',
  'INVITE_LOG_CHANNEL_ID',
  'ANNOUNCEMENTS_CHANNEL_ID',
  'RULES_CHANNEL_ID',
  'ROLES_CHANNEL_ID',
  'SEARCH_PLAYERS_CHANNEL_ID',
] as const

type OnboardingChannelKey = (typeof ONBOARDING_CHANNEL_KEYS)[number]

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

function channelLabel(channels: ChannelInfo[], id: string, fallback: string): string {
  if (!id) return fallback
  const found = channels.find((c) => c.id === id)
  return found ? `#${found.name}` : `<#${id}>`
}

function applyVars(text: string, vars: Record<string, string>) {
  return Object.entries(vars).reduce((acc, [key, value]) => acc.replaceAll(`{${key}}`, value), text)
}

function previewEmbed(embed: EmbedSpec, vars: Record<string, string>): EmbedSpec {
  return {
    ...embed,
    title: applyVars(embed.title, vars),
    description: applyVars(embed.description, vars),
    footer: { ...embed.footer, text: applyVars(embed.footer.text, vars) },
    fields: embed.fields.map((f) => ({
      ...f,
      name: applyVars(f.name, vars),
      value: applyVars(f.value, vars),
    })),
  }
}

export function ServerEntryPage() {
  const t = useT()
  const { lang } = useLanguage()
  const [tab, setTab] = useState<Tab>('welcome')
  const [settings, setSettings] = useState<WelcomeSettings | null>(null)
  const [config, setConfig] = useState<BotConfig>(EMPTY_BOT_CONFIG)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [savedMessage, setSavedMessage] = useState('')
  const [editorOpen, setEditorOpen] = useState(false)

  // Draft for the configure modal (welcome messages + channel config)
  const [draftSettings, setDraftSettings] = useState<WelcomeSettings | null>(null)
  const [draftConfig, setDraftConfig] = useState<BotConfig>(EMPTY_BOT_CONFIG)
  const [editorError, setEditorError] = useState('')
  const [editorBusy, setEditorBusy] = useState(false)

  const tabs = useMemo(
    () =>
      [
        { key: 'welcome' as const, label: t('serverEntry.tab.welcome'), icon: ChatCircle },
        { key: 'greeting' as const, label: t('serverEntry.tab.greeting'), icon: EnvelopeSimple },
        { key: 'autoroles' as const, label: t('serverEntry.tab.autoroles'), icon: UsersThree },
      ] as const,
    [t],
  )

  const channelFieldLabels: Record<OnboardingChannelKey, string> = useMemo(
    () => ({
      WELCOME_CHANNEL_ID: t('config.field.welcomeChannel'),
      INVITE_LOG_CHANNEL_ID: t('config.field.inviteLogChannel'),
      ANNOUNCEMENTS_CHANNEL_ID: t('config.field.announcementsChannel'),
      RULES_CHANNEL_ID: t('config.field.rulesChannel'),
      ROLES_CHANNEL_ID: t('config.field.rolesChannel'),
      SEARCH_PLAYERS_CHANNEL_ID: t('config.field.searchPlayersChannel'),
    }),
    [t],
  )

  useEffect(() => {
    Promise.all([fetchWelcomeSettings(), fetchChannels(), fetchConfig()])
      .then(([welcome, ch, cfg]) => {
        setSettings({
          ...welcome,
          messages: { ...emptyMessages(), ...welcome.messages },
        })
        setChannels(ch)
        setConfig(cfg)
      })
      .catch(() => setError(t('welcome.errorLoad')))
  }, [t])

  const previewVars = useMemo(() => {
    const dash = '—'
    return {
      mention: '@User',
      name: 'User',
      guild_name: 'Server 404: Server Not Found',
      member_count: '100',
      announcements_channel: channelLabel(channels, config.ANNOUNCEMENTS_CHANNEL_ID, dash),
      rules_channel: channelLabel(channels, config.RULES_CHANNEL_ID, dash),
      roles_channel: channelLabel(channels, config.ROLES_CHANNEL_ID, dash),
      search_channel: channelLabel(channels, config.SEARCH_PLAYERS_CHANNEL_ID, dash),
      guild: 'Server 404: Server Not Found',
      invite: 'https://discord.gg/example',
      user_id: '123456789',
    }
  }, [channels, config])

  const applyPreview = (text: string) => applyVars(text, previewVars)

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
      const embed = previewEmbed(msgs.channel_embed, previewVars)
      if (!embed.title && !embed.description && embed.fields.length === 0) {
        embed.title = applyVars('{guild_name}', previewVars)
        embed.description = t('welcome.previewChannelDefault')
      }
      return { content: '', embed }
    }
    const text = msgs.channel_text || t('welcome.previewChannelDefault')
    return { content: applyPreview(text), embed: EMPTY_EMBED_SPEC }
  }, [settings, t, previewVars])

  const goodbyePreview = useMemo(() => {
    if (!settings) return ''
    const text = settings.messages.goodbye_text || t('welcome.previewGoodbyeDefault')
    return applyPreview(text)
  }, [settings, t, previewVars])

  const greetingPreview = useMemo(() => {
    if (!settings) return { content: '', embed: buildDefaultDmEmbed(lang) }
    const msgs = settings.messages
    const base = embedHasContent(msgs.dm_embed)
      ? msgs.dm_embed
      : buildDefaultDmEmbed(lang)
    const thumb =
      msgs.dm_thumbnail_url.trim() ||
      base.thumbnail.url ||
      msgs.dm_fallback_thumbnail_url.trim() ||
      DEFAULT_DM_THUMBNAIL_URL
    const footerText = msgs.dm_footer_text.trim() || base.footer.text
    const embed = previewEmbed(
      {
        ...base,
        thumbnail: { url: thumb },
        footer: { ...base.footer, text: footerText },
      },
      previewVars,
    )
    return {
      content: applyVars(msgs.dm_content || '', previewVars),
      embed,
    }
  }, [settings, lang, previewVars])

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

  const openEditor = () => {
    if (!settings) return
    const seeded: WelcomeSettings = {
      ...settings,
      messages: {
        ...settings.messages,
        dm_embed: embedHasContent(settings.messages.dm_embed)
          ? settings.messages.dm_embed
          : buildDefaultDmEmbed(lang),
        dm_fallback_thumbnail_url:
          settings.messages.dm_fallback_thumbnail_url || DEFAULT_DM_THUMBNAIL_URL,
        dm_footer_text:
          settings.messages.dm_footer_text ||
          (lang === 'en'
            ? 'For help — contact the Administration. For bot questions — message Nandak070.'
            : 'Для помощи — обращайся к Администрации. По вопросам ботов — пиши Nandak070.'),
      },
    }
    setDraftSettings(seeded)
    setDraftConfig({ ...config })
    setEditorError('')
    setEditorOpen(true)
  }

  const updateDraftMessages = (patch: Partial<WelcomeMessageSettings>) => {
    setDraftSettings((prev) =>
      prev ? { ...prev, messages: { ...prev.messages, ...patch } } : prev,
    )
  }

  const saveEditor = async () => {
    if (!draftSettings) return
    setEditorBusy(true)
    setEditorError('')
    try {
      const [updatedWelcome, updatedConfig] = await Promise.all([
        updateWelcomeSettings(draftSettings),
        updateConfig(draftConfig),
      ])
      setSettings({
        ...updatedWelcome,
        messages: { ...emptyMessages(), ...updatedWelcome.messages },
      })
      setConfig(updatedConfig)
      setEditorOpen(false)
      setSavedMessage(t('common.saved'))
    } catch {
      setEditorError(t('welcome.errorSave'))
    } finally {
      setEditorBusy(false)
    }
  }

  if (!settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  return (
    <div className="flex max-w-5xl flex-col gap-6">
      <div>
        <h1 className="text-lg font-semibold text-foreground">{t('serverEntry.title')}</h1>
        <p className="mt-1 text-sm text-muted">{t('serverEntry.intro')}</p>
      </div>

      <div className="flex flex-wrap gap-1 border-b border-border pb-1">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            type="button"
            onClick={() => {
              setTab(key)
              setError('')
              setSavedMessage('')
            }}
            className={`flex cursor-pointer items-center gap-1.5 rounded-control px-3 py-1.5 text-sm transition-colors ${
              tab === key
                ? 'bg-primary-muted text-foreground'
                : 'text-muted hover:text-foreground'
            }`}
          >
            <Icon size={16} weight={tab === key ? 'fill' : 'regular'} />
            {label}
          </button>
        ))}
      </div>

      {tab === 'welcome' && (
        <div className="flex flex-col gap-6">
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
                    onChange={(id) =>
                      setSettings((prev) => (prev ? { ...prev, goodbye_channel_id: id } : prev))
                    }
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
        </div>
      )}

      {tab === 'greeting' && (
        <div className="flex flex-col gap-4">
          <div>
            <h2 className="font-semibold text-foreground">{t('serverEntry.tab.greeting')}</h2>
            <p className="mt-1 text-sm text-muted">{t('serverEntry.greetingIntro')}</p>
          </div>

          <Card className="flex flex-col gap-3">
            <Toggle
              checked={settings.dm_enabled}
              onChange={() => toggle('dm_enabled')}
              label={t('welcome.dmEnabled')}
            />
            <p className="text-xs text-muted">{t('serverEntry.greetingHint')}</p>
          </Card>

          <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
            <div className="min-w-0 flex-1">
              <p className="mb-2 text-sm font-medium text-foreground">{t('messageCustomizer.preview')}</p>
              <EmbedPreview content={greetingPreview.content} embed={greetingPreview.embed} />
            </div>
            <div className="flex shrink-0 flex-col gap-2 sm:pt-7">
              <Button variant="primary" onClick={openEditor}>
                <GearSix size={16} weight="bold" />
                {t('serverEntry.configure')}
              </Button>
            </div>
          </div>

          {error && <p className="text-sm text-danger">{error}</p>}
          {savedMessage && !editorOpen && <p className="text-sm text-primary">{savedMessage}</p>}
          <div>
            <Button variant="primary" onClick={saveWelcome} disabled={busy}>
              {busy ? t('common.saving') : t('common.save')}
            </Button>
          </div>
        </div>
      )}

      {tab === 'autoroles' && <AutoRolesPage embedded />}

      {editorOpen && draftSettings && (
        <Modal open title={t('serverEntry.editorTitle')} onClose={() => setEditorOpen(false)} size="xl">
          <div className="flex flex-col gap-6 pb-2">
            <section className="flex flex-col gap-3">
              <h3 className="text-sm font-semibold text-foreground">{t('serverEntry.editor.sectionEnable')}</h3>
              <Toggle
                checked={draftSettings.dm_enabled}
                onChange={() =>
                  setDraftSettings((prev) => (prev ? { ...prev, dm_enabled: !prev.dm_enabled } : prev))
                }
                label={t('welcome.dmEnabled')}
              />
            </section>

            <section className="flex flex-col gap-3 border-t border-border pt-4">
              <div>
                <h3 className="text-sm font-semibold text-foreground">{t('serverEntry.editor.sectionChannels')}</h3>
                <p className="mt-1 text-xs text-muted">{t('serverEntry.editor.channelsHint')}</p>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {ONBOARDING_CHANNEL_KEYS.map((key) => (
                  <div key={key} className="flex flex-col gap-1">
                    <label className="text-sm text-muted" htmlFor={`editor-${key}`}>
                      {channelFieldLabels[key]}
                    </label>
                    <Select
                      id={`editor-${key}`}
                      value={draftConfig[key]}
                      onChange={(id) => setDraftConfig((prev) => ({ ...prev, [key]: id }))}
                      options={channels}
                      placeholder={t('common.notSet')}
                    />
                  </div>
                ))}
              </div>
            </section>

            <section className="flex flex-col gap-3 border-t border-border pt-4">
              <div>
                <h3 className="text-sm font-semibold text-foreground">{t('serverEntry.editor.sectionEmbed')}</h3>
                <p className="mt-1 text-xs text-muted">{t('welcome.placeholderHint')}</p>
              </div>
              <EmbedEditor
                content={draftSettings.messages.dm_content}
                onContentChange={(dm_content) => updateDraftMessages({ dm_content })}
                embed={draftSettings.messages.dm_embed}
                onEmbedChange={(dm_embed) => updateDraftMessages({ dm_embed })}
              />
            </section>

            <section className="flex flex-col gap-3 border-t border-border pt-4">
              <h3 className="text-sm font-semibold text-foreground">{t('serverEntry.editor.sectionMedia')}</h3>
              <label className="text-sm text-muted">{t('welcome.dmThumbnailUrl')}</label>
              <input
                value={draftSettings.messages.dm_thumbnail_url}
                onChange={(e) => updateDraftMessages({ dm_thumbnail_url: e.target.value })}
                className={inputClass}
                placeholder="https://..."
              />
              <label className="text-sm text-muted">{t('welcome.dmFallbackThumbnailUrl')}</label>
              <input
                value={draftSettings.messages.dm_fallback_thumbnail_url}
                onChange={(e) => updateDraftMessages({ dm_fallback_thumbnail_url: e.target.value })}
                className={inputClass}
                placeholder={DEFAULT_DM_THUMBNAIL_URL}
              />
              <label className="text-sm text-muted">{t('welcome.dmFooterText')}</label>
              <input
                value={draftSettings.messages.dm_footer_text}
                onChange={(e) => updateDraftMessages({ dm_footer_text: e.target.value })}
                className={inputClass}
                placeholder={t('welcome.dmFooterPlaceholder')}
              />
              <Toggle
                checked={draftSettings.messages.dm_use_guild_icon}
                onChange={(v) => updateDraftMessages({ dm_use_guild_icon: v })}
                label={t('welcome.dmUseGuildIcon')}
              />
            </section>

            {editorError && <p className="text-sm text-danger">{editorError}</p>}
            <div className="flex flex-wrap gap-2 border-t border-border pt-4">
              <Button variant="primary" onClick={saveEditor} disabled={editorBusy}>
                {editorBusy ? t('common.saving') : t('common.save')}
              </Button>
              <Button variant="ghost" onClick={() => setEditorOpen(false)} disabled={editorBusy}>
                {t('common.cancel')}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
