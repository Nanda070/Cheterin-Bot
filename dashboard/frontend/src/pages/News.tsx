import { Megaphone, Plus, Trash } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  fetchChannels,
  fetchNewsSettings,
  updateNewsSettings,
  type ChannelInfo,
  type NewsSettings,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

export function NewsPage() {
  const t = useT()
  const [settings, setSettings] = useState<NewsSettings | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)
  const [botIdsRaw, setBotIdsRaw] = useState('')

  useEffect(() => {
    Promise.all([fetchNewsSettings(), fetchChannels()])
      .then(([s, ch]) => {
        setSettings(s)
        setBotIdsRaw(s.source_bot_ids.join(', '))
        setChannels(ch)
      })
      .catch((err) => setError(formatApiError(err, t, 'news.errorLoad')))
  }, [t])

  if (!settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  const setField = <K extends keyof NewsSettings>(key: K, value: NewsSettings[K]) => {
    setSettings((prev) => (prev ? { ...prev, [key]: value } : prev))
  }

  const setMapping = (index: number, key: 'source_channel_id' | 'target_channel_id' | 'label', value: string) => {
    setSettings((prev) => {
      if (!prev) return prev
      const mappings = prev.mappings.map((m, i) => (i === index ? { ...m, [key]: value } : m))
      return { ...prev, mappings }
    })
  }

  const addMapping = () => {
    setField('mappings', [...settings.mappings, { source_channel_id: '', target_channel_id: '', label: '' }])
  }

  const removeMapping = (index: number) => {
    setField(
      'mappings',
      settings.mappings.filter((_, i) => i !== index),
    )
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const payload: NewsSettings = {
        ...settings,
        source_bot_ids: botIdsRaw
          .split(',')
          .map((v) => v.trim())
          .filter(Boolean),
        mappings: settings.mappings.filter((m) => m.source_channel_id && m.target_channel_id),
      }
      const updated = await updateNewsSettings(payload)
      setSettings(updated)
      setBotIdsRaw(updated.source_bot_ids.join(', '))
      setSaved(t('common.saved'))
    } catch (err) {
      setError(formatApiError(err, t, 'news.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  const inputClass =
    'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
        <Megaphone size={22} className="text-primary" />
        {t('news.title')}
      </h1>
      <p className="text-sm text-muted">{t('news.intro')}</p>

      {error && <p className="text-sm text-danger">{error}</p>}
      {saved && <p className="text-sm text-primary">{saved}</p>}

      <Card className="flex flex-col gap-3">
        <Toggle
          checked={settings.enabled}
          onChange={(v) => setField('enabled', v)}
          label={t('news.enabled')}
        />

        <div className="flex flex-col gap-1">
          <label className="text-sm text-muted" htmlFor="news-guild">
            {t('news.sourceGuildId')}
          </label>
          <input
            id="news-guild"
            value={settings.source_guild_id}
            onChange={(e) => setField('source_guild_id', e.target.value.trim())}
            className={inputClass}
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-sm text-muted" htmlFor="news-bots">
            {t('news.sourceBotIds')}
          </label>
          <input
            id="news-bots"
            value={botIdsRaw}
            onChange={(e) => setBotIdsRaw(e.target.value)}
            className={inputClass}
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-sm text-muted" htmlFor="news-log">
            {t('news.logChannel')}
          </label>
          <Select
            id="news-log"
            value={settings.log_channel_id}
            onChange={(id) => setField('log_channel_id', id)}
            options={channels}
            placeholder={t('common.notSet')}
          />
        </div>
      </Card>

      <Card className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-foreground">{t('news.routesTitle')}</h2>
          <Button variant="secondary" onClick={addMapping}>
            <Plus size={16} />
            {t('common.add')}
          </Button>
        </div>
        {settings.mappings.length === 0 && <p className="text-sm text-muted">{t('news.routesEmpty')}</p>}
        {settings.mappings.map((m, index) => (
          <div key={index} className="flex flex-wrap items-end gap-2 border-t border-border pt-3 first:border-t-0 first:pt-0">
            <div className="flex min-w-40 flex-1 flex-col gap-1">
              <label className="text-xs text-muted">{t('news.sourceChannelId')}</label>
              <input
                value={m.source_channel_id}
                onChange={(e) => setMapping(index, 'source_channel_id', e.target.value.trim())}
                className={inputClass}
              />
            </div>
            <div className="flex min-w-40 flex-1 flex-col gap-1">
              <label className="text-xs text-muted">{t('news.targetChannel')}</label>
              <Select
                value={m.target_channel_id}
                onChange={(id) => setMapping(index, 'target_channel_id', id)}
                options={channels}
                placeholder={t('news.selectChannel')}
              />
            </div>
            <div className="flex min-w-28 flex-1 flex-col gap-1">
              <label className="text-xs text-muted">{t('news.label')}</label>
              <input
                value={m.label}
                placeholder={t('news.labelPlaceholder')}
                onChange={(e) => setMapping(index, 'label', e.target.value)}
                className={inputClass}
              />
            </div>
            <Button variant="ghost" onClick={() => removeMapping(index)}>
              <Trash size={16} />
            </Button>
          </div>
        ))}
      </Card>

      <div>
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? t('common.saving') : t('common.save')}
        </Button>
      </div>
    </div>
  )
}
