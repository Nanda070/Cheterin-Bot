import { Broadcast, Plus, TiktokLogo, Trash, TwitchLogo, YoutubeLogo } from '@phosphor-icons/react'
import { useT } from '../context/LanguageContext'
import { useEffect, useState } from 'react'
import {
  createStreamSubscription,
  deleteStreamSubscription,
  fetchChannels,
  fetchRoles,
  fetchStreams,
  testStreamSubscription,
  updateStreamSubscription,
  type ChannelInfo,
  type RoleInfo,
  type StreamSubscription,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

type StreamPlatform = 'twitch' | 'youtube' | 'tiktok'

function PlatformIcon({ platform }: { platform: StreamPlatform }) {
  if (platform === 'twitch') {
    return <TwitchLogo size={20} weight="fill" className="text-[#9146ff]" />
  }
  if (platform === 'tiktok') {
    return <TiktokLogo size={20} weight="fill" className="text-[#fe2c55]" />
  }
  return <YoutubeLogo size={20} weight="fill" className="text-[#ff0000]" />
}

function mapStreamError(message: string, t: (key: string) => string): string {
  if (message === 'channel_not_found' || message === 'tiktok_not_found') {
    return t('streams.error.channelNotFound')
  }
  if (message === 'invalid_tiktok_username') {
    return t('streams.error.invalidTiktokUsername')
  }
  if (message === 'already_subscribed') {
    return t('streams.error.alreadySubscribed')
  }
  if (message === 'twitch_not_configured') {
    return t('streams.error.twitchNotConfigured')
  }
  return t('common.operationFailed')
}

export function StreamsPage() {
  const t = useT()
  const [subs, setSubs] = useState<StreamSubscription[] | null>(null)
  const [twitchConfigured, setTwitchConfigured] = useState(true)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const [youtubeForm, setYoutubeForm] = useState({ query: '', channel_id: '' })
  const [tiktokForm, setTiktokForm] = useState({ query: '', channel_id: '' })
  const [twitchForm, setTwitchForm] = useState({ query: '', channel_id: '' })
  const [expanded, setExpanded] = useState<string | null>(null)
  const [keywordsDraft, setKeywordsDraft] = useState('')

  const reload = () =>
    fetchStreams()
      .then((data) => {
        setSubs(data.subscriptions)
        setTwitchConfigured(data.twitch_configured)
        setError('')
      })
      .catch(() => setError(t('streams.errorLoad')))

  useEffect(() => {
    reload()
    fetchChannels().then(setChannels).catch(() => setChannels([]))
    fetchRoles().then(setRoles).catch(() => setRoles([]))
  }, [])

  if (!subs) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  const act = async (fn: () => Promise<unknown>) => {
    setBusy(true)
    setError('')
    try {
      await fn()
      await reload()
    } catch (e) {
      const message = e instanceof Error ? e.message : ''
      setError(mapStreamError(message, t))
    } finally {
      setBusy(false)
    }
  }

  const patchSub = (id: string, fields: Parameters<typeof updateStreamSubscription>[1]) =>
    act(() => updateStreamSubscription(id, fields))

  const youtubeSubs = subs.filter((s) => s.platform === 'youtube')
  const tiktokSubs = subs.filter((s) => s.platform === 'tiktok')
  const twitchSubs = subs.filter((s) => s.platform === 'twitch')

  const renderSubCard = (sub: StreamSubscription) => (
    <Card key={sub.id} className="flex flex-col gap-3">
      <div className="flex items-start gap-3">
        {sub.avatar_url ? (
          <img src={sub.avatar_url} alt="" className="h-10 w-10 shrink-0 rounded-full" />
        ) : (
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-hover">
            <PlatformIcon platform={sub.platform} />
          </span>
        )}
        <div className="min-w-0 flex-1">
          <p className="flex items-center gap-1.5 truncate text-sm font-semibold text-foreground">
            <PlatformIcon platform={sub.platform} />
            {sub.display_name}
          </p>
          <p className="text-xs text-muted">{t(`streams.platform.${sub.platform}`)}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2 self-center">
          <Toggle checked={sub.enabled} onChange={(v) => patchSub(sub.id, { enabled: v })} disabled={busy} />
          <button
            type="button"
            onClick={() => act(() => deleteStreamSubscription(sub.id))}
            className="text-muted transition-colors hover:text-danger"
            aria-label={t('streams.deleteAria')}
          >
            <Trash size={17} />
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Button
          variant="secondary"
          className="!px-3 !py-1.5 text-xs"
          disabled={busy || !sub.channel_id}
          onClick={() => act(() => testStreamSubscription(sub.id))}
        >
          {t('streams.testSend')}
        </Button>
        <button
          type="button"
          onClick={() => {
            setExpanded(expanded === sub.id ? null : sub.id)
            setKeywordsDraft(sub.keywords.join(', '))
          }}
          className="text-xs text-primary hover:underline"
        >
          {expanded === sub.id ? t('streams.hideSettings') : t('streams.showSettings')}
        </button>
      </div>

      {expanded === sub.id && (
        <div className="flex flex-col gap-3 border-t border-border pt-3">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted">{t('streams.field.publishChannel')}</label>
            <Select
              value={sub.channel_id}
              onChange={(id) => patchSub(sub.id, { channel_id: id })}
              options={channels}
              placeholder={t('streams.notSelected')}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted">{t('streams.field.pingRole')}</label>
            <Select
              value={sub.ping_role_id}
              onChange={(id) => patchSub(sub.id, { ping_role_id: id })}
              options={roles}
              kind="role"
              placeholder={t('streams.noPing')}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted">{t('streams.field.template')}</label>
            <textarea
              rows={3}
              defaultValue={sub.template}
              onBlur={(e) => e.target.value !== sub.template && patchSub(sub.id, { template: e.target.value })}
              className={inputClass}
            />
            <span className="text-[11px] text-muted">{t('streams.templateVars')}</span>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted">{t('streams.field.keywords')}</label>
            <input
              value={keywordsDraft}
              onChange={(e) => setKeywordsDraft(e.target.value)}
              onBlur={() =>
                patchSub(sub.id, {
                  keywords: keywordsDraft
                    .split(',')
                    .map((k) => k.trim())
                    .filter(Boolean),
                })
              }
              placeholder={t('streams.keywordsPlaceholder')}
              className={inputClass}
            />
          </div>
          <div className="flex gap-3">
            <div className="flex flex-1 flex-col gap-1">
              <label className="text-xs text-muted">{t('streams.field.filterMode')}</label>
              <Select
                value={sub.keyword_mode}
                onChange={(id) => patchSub(sub.id, { keyword_mode: id as 'any' | 'all' })}
                options={[
                  { id: 'any', name: t('streams.filter.any') },
                  { id: 'all', name: t('streams.filter.all') },
                ]}
              />
            </div>
            <div className="flex flex-1 flex-col gap-1">
              <label className="text-xs text-muted">{t('streams.field.minInterval')}</label>
              <input
                type="number"
                min={0}
                max={10080}
                defaultValue={sub.min_interval_minutes}
                onBlur={(e) => {
                  const v = Math.max(0, Number(e.target.value))
                  if (v !== sub.min_interval_minutes) patchSub(sub.id, { min_interval_minutes: v })
                }}
                className={inputClass}
              />
            </div>
          </div>
          <div className="flex flex-wrap gap-4 pt-1">
            <label className="flex items-center gap-2 text-sm">
              <Toggle
                checked={Boolean(sub.mention_everyone)}
                onChange={(v) => patchSub(sub.id, { mention_everyone: v })}
              />
              {t('streams.field.mentionEveryone')}
            </label>
            <label className="flex items-center gap-2 text-sm">
              <Toggle checked={sub.use_embed !== false} onChange={(v) => patchSub(sub.id, { use_embed: v })} />
              {t('streams.field.useEmbed')}
            </label>
            <input
              className={`${inputClass} w-32`}
              defaultValue={sub.embed_color || ''}
              placeholder="#9146FF"
              aria-label={t('streams.field.embedColor')}
              onBlur={(e) => {
                const v = e.target.value.trim()
                if (v !== (sub.embed_color || '')) patchSub(sub.id, { embed_color: v })
              }}
            />
          </div>
        </div>
      )}
    </Card>
  )

  const renderAddRow = (
    platform: StreamPlatform,
    form: { query: string; channel_id: string },
    setForm: (next: { query: string; channel_id: string }) => void,
  ) => (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <label className="text-xs text-muted">{t(`streams.field.query.${platform}`)}</label>
        <input
          value={form.query}
          onChange={(e) => setForm({ ...form, query: e.target.value })}
          placeholder={t(`streams.queryPlaceholder.${platform}`)}
          className={inputClass}
        />
      </div>
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <label className="text-xs text-muted">{t('streams.field.notifyChannel')}</label>
        <Select
          value={form.channel_id}
          onChange={(id) => setForm({ ...form, channel_id: id })}
          options={channels}
          placeholder={t('common.selectChannel')}
        />
      </div>
      <Button
        variant="primary"
        disabled={busy || !form.query.trim() || !form.channel_id}
        onClick={() =>
          act(async () => {
            await createStreamSubscription({
              platform,
              query: form.query.trim(),
              channel_id: form.channel_id,
            })
            setForm({ query: '', channel_id: form.channel_id })
          })
        }
      >
        <Plus size={16} />
        {busy ? t('streams.checking') : t('streams.subscribe')}
      </Button>
    </div>
  )

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Broadcast size={22} className="text-primary" />
          {t('streams.title')}
        </h1>
      </div>

      {!twitchConfigured && (
        <Card>
          <p className="text-sm text-warning">{t('streams.twitchWarning')}</p>
        </Card>
      )}

      {error && <p className="text-sm text-danger">{error}</p>}

      <section className="flex flex-col gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-base font-semibold text-foreground">
            <YoutubeLogo size={20} weight="fill" className="text-[#ff0000]" />
            {t('streams.section.videoNews')}
          </h2>
          <p className="mt-1 text-sm text-muted">{t('streams.section.videoNewsHint')}</p>
        </div>
        <Card className="flex flex-col gap-3">{renderAddRow('youtube', youtubeForm, setYoutubeForm)}</Card>
        {youtubeSubs.length === 0 ? (
          <p className="text-sm text-muted">{t('streams.empty.youtube')}</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">{youtubeSubs.map(renderSubCard)}</div>
        )}
      </section>

      <section className="flex flex-col gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-base font-semibold text-foreground">
            <TiktokLogo size={20} weight="fill" className="text-[#fe2c55]" />
            {t('streams.section.tiktokStreams')}
          </h2>
          <p className="mt-1 text-sm text-muted">{t('streams.section.tiktokStreamsHint')}</p>
        </div>
        <Card className="flex flex-col gap-3">{renderAddRow('tiktok', tiktokForm, setTiktokForm)}</Card>
        {tiktokSubs.length === 0 ? (
          <p className="text-sm text-muted">{t('streams.empty.tiktok')}</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">{tiktokSubs.map(renderSubCard)}</div>
        )}
      </section>

      <section className="flex flex-col gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-base font-semibold text-foreground">
            <TwitchLogo size={20} weight="fill" className="text-[#9146ff]" />
            {t('streams.section.twitch')}
          </h2>
          <p className="mt-1 text-sm text-muted">{t('streams.section.twitchHint')}</p>
        </div>
        <Card className="flex flex-col gap-3">{renderAddRow('twitch', twitchForm, setTwitchForm)}</Card>
        {twitchSubs.length === 0 ? (
          <p className="text-sm text-muted">{t('streams.empty.twitch')}</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">{twitchSubs.map(renderSubCard)}</div>
        )}
      </section>
    </div>
  )
}
