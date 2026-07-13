import { Megaphone, Plus, Trash } from '@phosphor-icons/react'
import { ChannelOptions } from '../components/ChannelOptions'
import { useEffect, useState } from 'react'
import {
  fetchChannels,
  fetchNewsSettings,
  updateNewsSettings,
  type ChannelInfo,
  type NewsSettings,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'

export function NewsPage() {
  const [settings, setSettings] = useState<NewsSettings | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)
  const [botIdsRaw, setBotIdsRaw] = useState('')

  useEffect(() => {
    Promise.all([fetchNewsSettings(), fetchChannels().catch(() => [] as ChannelInfo[])])
      .then(([s, ch]) => {
        setSettings(s)
        setBotIdsRaw(s.source_bot_ids.join(', '))
        setChannels(ch)
      })
      .catch(() => setError('Не удалось загрузить настройки ретрансляции'))
  }, [])

  if (!settings) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
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
      setSaved('Сохранено.')
    } catch {
      setError('Не удалось сохранить — проверьте, что все ID числовые и каналы-источники не повторяются')
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
        Ретрансляция новостей
      </h1>
      <p className="text-sm text-muted">
        Бот пересылает сообщения выбранных ботов с сервера-источника в каналы этого сервера — текст, вложения и
        эмбеды.
      </p>

      {error && <p className="text-sm text-danger">{error}</p>}
      {saved && <p className="text-sm text-primary">{saved}</p>}

      <Card className="flex flex-col gap-3">
        <label className="flex items-center gap-2 text-sm text-foreground">
          <input
            type="checkbox"
            checked={settings.enabled}
            onChange={(e) => setField('enabled', e.target.checked)}
          />
          Ретрансляция включена
        </label>

        <div className="flex flex-col gap-1">
          <label className="text-sm text-muted" htmlFor="news-guild">
            ID сервера-источника
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
            ID ботов-источников (через запятую)
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
            Лог-канал ретрансляции
          </label>
          <select
            id="news-log"
            value={settings.log_channel_id}
            onChange={(e) => setField('log_channel_id', e.target.value)}
            className={inputClass}
          >
            <option value="">Не задано</option>
            <ChannelOptions channels={channels} />
          </select>
        </div>
      </Card>

      <Card className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-foreground">Маршруты каналов</h2>
          <Button variant="secondary" onClick={addMapping}>
            <Plus size={16} />
            Добавить
          </Button>
        </div>
        {settings.mappings.length === 0 && <p className="text-sm text-muted">Маршрутов пока нет.</p>}
        {settings.mappings.map((m, index) => (
          <div key={index} className="flex flex-wrap items-end gap-2 border-t border-border pt-3 first:border-t-0 first:pt-0">
            <div className="flex min-w-40 flex-1 flex-col gap-1">
              <label className="text-xs text-muted">ID канала-источника</label>
              <input
                value={m.source_channel_id}
                onChange={(e) => setMapping(index, 'source_channel_id', e.target.value.trim())}
                className={inputClass}
              />
            </div>
            <div className="flex min-w-40 flex-1 flex-col gap-1">
              <label className="text-xs text-muted">Канал-приёмник</label>
              <select
                value={m.target_channel_id}
                onChange={(e) => setMapping(index, 'target_channel_id', e.target.value)}
                className={inputClass}
              >
                <option value="">Выберите канал</option>
                <ChannelOptions channels={channels} />
              </select>
            </div>
            <div className="flex min-w-28 flex-1 flex-col gap-1">
              <label className="text-xs text-muted">Метка</label>
              <input
                value={m.label}
                placeholder="Valorant"
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
          {busy ? 'Сохраняем…' : 'Сохранить'}
        </Button>
      </div>
    </div>
  )
}
