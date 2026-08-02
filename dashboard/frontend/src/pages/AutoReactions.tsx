import { Plus, Smiley, Trash } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  fetchAutoReactions,
  fetchChannels,
  updateAutoReactions,
  type AutoReactionRule,
  type AutoReactionsSettings,
  type ChannelInfo,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { ChipPicker } from '../components/ChipPicker'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

function newRule(): AutoReactionRule {
  return {
    id: crypto.randomUUID().replace(/-/g, '').slice(0, 12),
    emoji_mode: 'list',
    emojis: ['👍'],
    keywords: [],
    channel_mode: 'all',
    channel_ids: [],
    exclude_channel_ids: [],
    ignore_bots: true,
  }
}

export function AutoReactionsPage() {
  const t = useT()
  const [settings, setSettings] = useState<AutoReactionsSettings | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    Promise.all([fetchAutoReactions(), fetchChannels()])
      .then(([data, ch]) => {
        setSettings({
          ...data,
          rules: data.rules.map((r) => ({
            ...r,
            emoji_mode: r.emoji_mode === 'all_guild' ? 'all_guild' : 'list',
          })),
        })
        setChannels(ch)
      })
      .catch((err) => setError(formatApiError(err, t, 'autoReactions.errorLoad')))
  }, [t])

  if (!settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  const patchRule = (id: string, patch: Partial<AutoReactionRule>) => {
    setSettings({
      ...settings,
      rules: settings.rules.map((r) => (r.id === id ? { ...r, ...patch } : r)),
    })
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateAutoReactions(settings)
      setSettings(updated)
      setSaved(t('common.saved'))
    } catch (err) {
      setError(formatApiError(err, t, 'autoReactions.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Smiley size={22} className="text-primary" />
          {t('autoReactions.title')}
        </h1>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => setSettings({ ...settings, enabled: v })}
          label={settings.enabled ? t('autoReactions.moduleOn') : t('autoReactions.moduleOff')}
        />
      </div>
      <p className="text-sm text-muted">{t('autoReactions.intro')}</p>

      {error && <p className="text-sm text-danger">{error}</p>}
      {saved && <p className="text-sm text-primary">{saved}</p>}

      {settings.rules.length === 0 && (
        <p className="text-sm text-muted">{t('autoReactions.empty')}</p>
      )}

      {settings.rules.map((rule, index) => (
        <Card key={rule.id} className="flex flex-col gap-3">
          <div className="flex items-center justify-between gap-2">
            <h2 className="font-semibold text-foreground">
              {t('autoReactions.ruleTitle', { n: index + 1 })}
            </h2>
            <button
              type="button"
              className="text-muted hover:text-danger"
              aria-label={t('autoReactions.deleteRule')}
              onClick={() =>
                setSettings({
                  ...settings,
                  rules: settings.rules.filter((r) => r.id !== rule.id),
                })
              }
            >
              <Trash size={18} />
            </button>
          </div>

          <div className="flex flex-col gap-2">
            <span className="text-sm text-muted">{t('autoReactions.emojiMode')}</span>
            <div className="flex flex-wrap gap-2">
              {(['list', 'all_guild'] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() =>
                    patchRule(rule.id, {
                      emoji_mode: mode,
                      emojis: mode === 'all_guild' ? [] : rule.emojis.length ? rule.emojis : ['👍'],
                    })
                  }
                  className={`rounded-control border px-3 py-1.5 text-sm ${
                    rule.emoji_mode === mode
                      ? 'border-primary bg-primary-muted text-foreground'
                      : 'border-border text-muted hover:border-primary/40'
                  }`}
                >
                  {mode === 'list'
                    ? t('autoReactions.emojiModeList')
                    : t('autoReactions.emojiModeAllGuild')}
                </button>
              ))}
            </div>
            {rule.emoji_mode === 'all_guild' && (
              <span className="text-xs text-muted">{t('autoReactions.emojiModeAllGuildHint')}</span>
            )}
          </div>

          {rule.emoji_mode === 'list' && (
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted">{t('autoReactions.emojis')}</label>
              <input
                className={inputClass}
                value={rule.emojis.join(' ')}
                onChange={(e) =>
                  patchRule(rule.id, {
                    emojis: e.target.value
                      .split(/\s+/)
                      .map((s) => s.trim())
                      .filter(Boolean),
                  })
                }
                placeholder={t('autoReactions.emojisPlaceholder')}
              />
              <span className="text-xs text-muted">{t('autoReactions.emojisHint')}</span>
            </div>
          )}

          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted">{t('autoReactions.keywords')}</label>
            <input
              className={inputClass}
              value={rule.keywords.join(', ')}
              onChange={(e) =>
                patchRule(rule.id, {
                  keywords: e.target.value
                    .split(',')
                    .map((s) => s.trim())
                    .filter(Boolean),
                })
              }
              placeholder={t('autoReactions.keywordsPlaceholder')}
            />
            <span className="text-xs text-muted">{t('autoReactions.keywordsHint')}</span>
          </div>

          <div className="flex flex-col gap-2">
            <span className="text-sm text-muted">{t('autoReactions.channelMode')}</span>
            <div className="flex flex-wrap gap-2">
              {(['all', 'include'] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => patchRule(rule.id, { channel_mode: mode })}
                  className={`rounded-control border px-3 py-1.5 text-sm ${
                    rule.channel_mode === mode
                      ? 'border-primary bg-primary-muted text-foreground'
                      : 'border-border text-muted hover:border-primary/40'
                  }`}
                >
                  {mode === 'all'
                    ? t('autoReactions.modeAll')
                    : t('autoReactions.modeInclude')}
                </button>
              ))}
            </div>
          </div>

          {rule.channel_mode === 'include' && (
            <ChipPicker
              label={t('autoReactions.includeChannels')}
              options={channels}
              selected={rule.channel_ids}
              onChange={(ids) => patchRule(rule.id, { channel_ids: ids })}
            />
          )}

          <ChipPicker
            label={t('autoReactions.excludeChannels')}
            hint={t('autoReactions.excludeHint')}
            options={channels}
            selected={rule.exclude_channel_ids}
            onChange={(ids) => patchRule(rule.id, { exclude_channel_ids: ids })}
          />

          <Toggle
            checked={rule.ignore_bots}
            onChange={(v) => patchRule(rule.id, { ignore_bots: v })}
            label={t('autoReactions.ignoreBots')}
          />
        </Card>
      ))}

      <div className="flex flex-wrap gap-2">
        <Button
          variant="secondary"
          onClick={() =>
            setSettings({ ...settings, rules: [...settings.rules, newRule()] })
          }
          disabled={settings.rules.length >= 25}
        >
          <Plus size={16} />
          {t('autoReactions.addRule')}
        </Button>
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? t('common.saving') : t('common.save')}
        </Button>
      </div>
    </div>
  )
}
