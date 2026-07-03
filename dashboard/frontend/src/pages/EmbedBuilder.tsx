import { useEffect, useState } from 'react'
import {
  createEmbedMessage,
  fetchChannels,
  fetchEmbedMessage,
  fetchRoles,
  updateEmbedMessage,
  type ChannelInfo,
  type EmbedFieldSpec,
  type EmbedSpec,
  type RoleInfo,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { EmbedPreview } from '../components/EmbedPreview'

const EMPTY_EMBED_SPEC: EmbedSpec = {
  title: '',
  description: '',
  url: '',
  color: '#5865F2',
  author: { name: '', url: '', icon_url: '' },
  footer: { text: '', icon_url: '' },
  image: { url: '' },
  thumbnail: { url: '' },
  timestamp: null,
  fields: [],
}

function validateEmbedSpec(spec: EmbedSpec): string | null {
  if (!(spec.title || spec.description || spec.fields.length > 0 || spec.image.url || spec.thumbnail.url)) {
    return 'Заполните хотя бы title, description, поле или изображение'
  }
  if (spec.title.length > 256) return 'Title длиннее 256 символов'
  if (spec.description.length > 4096) return 'Description длиннее 4096 символов'
  if (spec.footer.text.length > 2048) return 'Текст footer длиннее 2048 символов'
  if (spec.author.name.length > 256) return 'Имя author длиннее 256 символов'
  if (spec.fields.length > 25) return 'Не больше 25 полей'
  for (const field of spec.fields) {
    if (field.name.length > 256) return 'Название поля длиннее 256 символов'
    if (field.value.length > 1024) return 'Значение поля длиннее 1024 символов'
  }
  const totalLength =
    spec.title.length +
    spec.description.length +
    spec.footer.text.length +
    spec.author.name.length +
    spec.fields.reduce((sum, field) => sum + field.name.length + field.value.length, 0)
  if (totalLength > 6000) return 'Суммарная длина текста эмбеда превышает 6000 символов'
  return null
}

export function EmbedBuilderPage() {
  const [mode, setMode] = useState<'create' | 'edit'>('create')
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [channelId, setChannelId] = useState('')
  const [messageId, setMessageId] = useState('')
  const [content, setContent] = useState('')
  const [embed, setEmbed] = useState<EmbedSpec>(EMPTY_EMBED_SPEC)
  const [roleIds, setRoleIds] = useState<string[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [savedResult, setSavedResult] = useState<{ message_id: string; channel_id: string } | null>(null)

  useEffect(() => {
    fetchChannels().then(setChannels).catch(() => {})
    fetchRoles().then(setRoles).catch(() => {})
  }, [])

  const updateEmbedField = <K extends keyof EmbedSpec>(key: K, value: EmbedSpec[K]) => {
    setEmbed((prev) => ({ ...prev, [key]: value }))
  }

  const updateField = (index: number, patch: Partial<EmbedFieldSpec>) => {
    setEmbed((prev) => ({ ...prev, fields: prev.fields.map((f, i) => (i === index ? { ...f, ...patch } : f)) }))
  }

  const addField = () => {
    setEmbed((prev) => ({ ...prev, fields: [...prev.fields, { name: '', value: '', inline: false }] }))
  }

  const removeField = (index: number) => {
    setEmbed((prev) => ({ ...prev, fields: prev.fields.filter((_, i) => i !== index) }))
  }

  const toggleRole = (roleId: string) => {
    setRoleIds((prev) => (prev.includes(roleId) ? prev.filter((r) => r !== roleId) : [...prev, roleId]))
  }

  const handleLoad = async () => {
    setError('')
    if (!channelId || !messageId) {
      setError('Укажите канал и Message ID')
      return
    }
    setBusy(true)
    try {
      const data = await fetchEmbedMessage(channelId, messageId)
      setContent(data.content)
      setEmbed(data.embed)
      setRoleIds(data.role_ids)
    } catch {
      setError('Не удалось загрузить сообщение — проверьте канал/ID')
    } finally {
      setBusy(false)
    }
  }

  const handleSave = async () => {
    setError('')
    setSavedResult(null)
    if (!channelId) {
      setError('Укажите канал')
      return
    }
    if (mode === 'edit' && !messageId) {
      setError('Укажите Message ID')
      return
    }
    if (roleIds.length > 5) {
      setError('Не больше 5 роль-кнопок')
      return
    }
    const validationError = validateEmbedSpec(embed)
    if (validationError) {
      setError(validationError)
      return
    }

    setBusy(true)
    try {
      const payload = { content, embed, role_ids: roleIds }
      const result =
        mode === 'edit'
          ? await updateEmbedMessage(channelId, messageId, payload)
          : await createEmbedMessage(channelId, payload)
      setSavedResult(result)
    } catch {
      setError('Не удалось сохранить — проверьте канал/ID сообщения и права на роли')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="flex flex-col gap-3">
        <div className="flex gap-2">
          <Button variant={mode === 'create' ? 'primary' : 'secondary'} onClick={() => setMode('create')}>
            Новое сообщение
          </Button>
          <Button variant={mode === 'edit' ? 'primary' : 'secondary'} onClick={() => setMode('edit')}>
            Редактировать существующее
          </Button>
        </div>

        <label className="text-sm text-muted" htmlFor="eb-channel">
          Канал
        </label>
        <select
          id="eb-channel"
          value={channelId}
          onChange={(e) => setChannelId(e.target.value)}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
        >
          <option value="">Выберите канал…</option>
          {channels.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>

        {mode === 'edit' && (
          <div className="flex gap-2">
            <input
              value={messageId}
              onChange={(e) => setMessageId(e.target.value)}
              placeholder="ID существующего сообщения"
              className="flex-1 rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
            />
            <Button variant="secondary" onClick={handleLoad} disabled={busy}>
              Загрузить
            </Button>
          </div>
        )}

        <label className="text-sm text-muted" htmlFor="eb-content">
          Текст сообщения
        </label>
        <textarea
          id="eb-content"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          rows={2}
        />

        <label className="text-sm text-muted" htmlFor="eb-title">
          Title
        </label>
        <input
          id="eb-title"
          value={embed.title}
          onChange={(e) => updateEmbedField('title', e.target.value)}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />

        <label className="text-sm text-muted" htmlFor="eb-description">
          Description
        </label>
        <textarea
          id="eb-description"
          value={embed.description}
          onChange={(e) => updateEmbedField('description', e.target.value)}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          rows={3}
        />

        <label className="text-sm text-muted" htmlFor="eb-color">
          Цвет
        </label>
        <div className="flex gap-2">
          <input
            id="eb-color"
            type="color"
            value={embed.color || '#5865F2'}
            onChange={(e) => updateEmbedField('color', e.target.value)}
            className="h-9 w-12 rounded-control border border-border bg-background"
          />
          <input
            value={embed.color}
            onChange={(e) => updateEmbedField('color', e.target.value)}
            placeholder="#5865F2"
            className="flex-1 rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />
        </div>

        <label className="text-sm text-muted" htmlFor="eb-author-name">
          Author
        </label>
        <input
          id="eb-author-name"
          value={embed.author.name}
          onChange={(e) => updateEmbedField('author', { ...embed.author, name: e.target.value })}
          placeholder="Имя автора"
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />

        <label className="text-sm text-muted" htmlFor="eb-footer-text">
          Footer
        </label>
        <input
          id="eb-footer-text"
          value={embed.footer.text}
          onChange={(e) => updateEmbedField('footer', { ...embed.footer, text: e.target.value })}
          placeholder="Текст footer"
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />

        <label className="text-sm text-muted" htmlFor="eb-image-url">
          Image URL
        </label>
        <input
          id="eb-image-url"
          value={embed.image.url}
          onChange={(e) => updateEmbedField('image', { url: e.target.value })}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />

        <label className="text-sm text-muted" htmlFor="eb-thumbnail-url">
          Thumbnail URL
        </label>
        <input
          id="eb-thumbnail-url"
          value={embed.thumbnail.url}
          onChange={(e) => updateEmbedField('thumbnail', { url: e.target.value })}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />

        <label className="flex items-center gap-2 text-sm text-muted">
          <input
            type="checkbox"
            checked={embed.timestamp !== null}
            onChange={(e) => updateEmbedField('timestamp', e.target.checked ? new Date().toISOString() : null)}
          />
          Текущее время
        </label>

        <div className="flex flex-col gap-2">
          {embed.fields.map((field, index) => (
            <div key={index} className="flex flex-wrap items-center gap-2 rounded-control border border-border/60 p-2">
              <input
                value={field.name}
                onChange={(e) => updateField(index, { name: e.target.value })}
                placeholder="Название поля"
                className="min-w-0 flex-1 basis-full rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary"
              />
              <input
                value={field.value}
                onChange={(e) => updateField(index, { value: e.target.value })}
                placeholder="Значение поля"
                className="min-w-0 flex-1 basis-full rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary"
              />
              <label className="flex items-center gap-1 text-xs text-muted">
                <input type="checkbox" checked={field.inline} onChange={(e) => updateField(index, { inline: e.target.checked })} />
                inline
              </label>
              <button type="button" onClick={() => removeField(index)} className="cursor-pointer text-muted hover:text-danger">
                ×
              </button>
            </div>
          ))}
          <button type="button" onClick={addField} className="cursor-pointer self-start text-sm text-primary hover:text-primary-hover">
            + Добавить поле
          </button>
        </div>

        <div>
          <p className="mb-1 text-sm text-muted">Роль-кнопки (до 5)</p>
          <div className="flex flex-wrap gap-2">
            {roles.map((role) => (
              <label key={role.id} className="flex items-center gap-1 text-xs text-foreground">
                <input type="checkbox" checked={roleIds.includes(role.id)} onChange={() => toggleRole(role.id)} />
                {role.name}
              </label>
            ))}
          </div>
        </div>

        {error && <p className="text-sm text-danger">{error}</p>}
        {savedResult && (
          <p className="text-sm text-success">
            Сохранено: message_id {savedResult.message_id} в канале {savedResult.channel_id}
          </p>
        )}

        <Button variant="primary" onClick={handleSave} disabled={busy}>
          {busy ? 'Сохраняем…' : mode === 'edit' ? 'Сохранить' : 'Отправить'}
        </Button>
      </div>

      <div>
        <EmbedPreview content={content} embed={embed} />
      </div>
    </div>
  )
}
