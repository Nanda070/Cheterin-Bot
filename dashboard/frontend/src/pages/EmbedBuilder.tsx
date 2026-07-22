import { useEffect, useState } from 'react'
import { useT } from '../context/LanguageContext'
import {
  createEmbedMessage,
  deleteEmbedTemplate,
  fetchChannels,
  fetchEmbedMessage,
  fetchEmbedTemplates,
  fetchRoles,
  saveEmbedTemplate,
  updateEmbedMessage,
  type ChannelInfo,
  type EmbedFieldSpec,
  type EmbedSpec,
  type EmbedTemplate,
  type RoleInfo,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Checkbox } from '../components/ui/Checkbox'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
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

function validateEmbedSpec(spec: EmbedSpec, content: string): string | null {
  const hasEmbedContent = Boolean(
    spec.title || spec.description || spec.fields.length > 0 || spec.image.url || spec.thumbnail.url,
  )
  if (!hasEmbedContent && !content.trim()) {
    return 'embedBuilder.error.validation.empty'
  }
  if (spec.title.length > 256) return 'embedBuilder.error.validation.title'
  if (spec.description.length > 4096) return 'embedBuilder.error.validation.description'
  if (spec.footer.text.length > 2048) return 'embedBuilder.error.validation.footer'
  if (spec.author.name.length > 256) return 'embedBuilder.error.validation.author'
  if (spec.fields.length > 25) return 'embedBuilder.error.validation.fieldsCount'
  for (const field of spec.fields) {
    if (field.name.length > 256) return 'embedBuilder.error.validation.fieldName'
    if (field.value.length > 1024) return 'embedBuilder.error.validation.fieldValue'
  }
  const totalLength =
    spec.title.length +
    spec.description.length +
    spec.footer.text.length +
    spec.author.name.length +
    spec.fields.reduce((sum, field) => sum + field.name.length + field.value.length, 0)
  if (totalLength > 6000) return 'embedBuilder.error.validation.totalLength'
  return null
}

export function EmbedBuilderPage() {
  const t = useT()
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
  const [templates, setTemplates] = useState<EmbedTemplate[]>([])
  const [templateName, setTemplateName] = useState('')
  const [templateNotice, setTemplateNotice] = useState('')

  useEffect(() => {
    fetchChannels().then(setChannels).catch(() => {})
    fetchRoles().then(setRoles).catch(() => {})
    fetchEmbedTemplates().then(setTemplates).catch(() => {})
  }, [])

  const applyTemplate = (id: string) => {
    const template = templates.find((t) => t.id === id)
    if (!template) return
    setContent(template.content)
    setEmbed({ ...EMPTY_EMBED_SPEC, ...template.embed })
    setRoleIds(template.role_ids)
    setTemplateNotice(t('embedBuilder.templateLoaded', { name: template.name }))
  }

  const handleSaveTemplate = async () => {
    setError('')
    setTemplateNotice('')
    const name = templateName.trim()
    if (!name) {
      setError(t('embedBuilder.error.templateName'))
      return
    }
    const validationError = validateEmbedSpec(embed, content)
    if (validationError) {
      setError(t(validationError))
      return
    }
    setBusy(true)
    try {
      const created = await saveEmbedTemplate({ name, content, embed, role_ids: roleIds })
      setTemplates((prev) => [...prev, created])
      setTemplateName('')
      setTemplateNotice(t('embedBuilder.templateSaved', { name: created.name }))
    } catch (e) {
      setError(e instanceof Error && e.message === 'duplicate_name' ? t('embedBuilder.error.duplicateName') : t('embedBuilder.error.saveTemplate'))
    } finally {
      setBusy(false)
    }
  }

  const handleDeleteTemplate = async (id: string) => {
    try {
      await deleteEmbedTemplate(id)
      setTemplates((prev) => prev.filter((t) => t.id !== id))
    } catch (err) {
      setError(formatApiError(err, t, 'embedBuilder.error.deleteTemplate'))
    }
  }

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
      setError(t('embedBuilder.error.channelAndId'))
      return
    }
    setBusy(true)
    try {
      const data = await fetchEmbedMessage(channelId, messageId)
      setContent(data.content)
      setEmbed(data.embed)
      setRoleIds(data.role_ids)
    } catch (err) {
      setError(formatApiError(err, t, 'embedBuilder.error.load'))
    } finally {
      setBusy(false)
    }
  }

  const handleSave = async () => {
    setError('')
    setSavedResult(null)
    if (!channelId) {
      setError(t('embedBuilder.error.channel'))
      return
    }
    if (mode === 'edit' && !messageId) {
      setError(t('embedBuilder.error.messageId'))
      return
    }
    if (roleIds.length > 5) {
      setError(t('embedBuilder.error.tooManyRoles'))
      return
    }
    const validationError = validateEmbedSpec(embed, content)
    if (validationError) {
      setError(t(validationError))
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
    } catch (err) {
      setError(formatApiError(err, t, 'embedBuilder.error.save'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="flex flex-col gap-3">
        <div className="flex gap-2">
          <Button variant={mode === 'create' ? 'primary' : 'secondary'} onClick={() => setMode('create')}>
            {t('embedBuilder.mode.create')}
          </Button>
          <Button variant={mode === 'edit' ? 'primary' : 'secondary'} onClick={() => setMode('edit')}>
            {t('embedBuilder.mode.edit')}
          </Button>
        </div>

        <div className="flex flex-col gap-2 rounded-control border border-border bg-surface p-3">
          <p className="text-sm font-medium text-foreground">{t('embedBuilder.templates')}</p>
          <div className="flex gap-2">
            <Select
              value=""
              onChange={(id) => applyTemplate(id)}
              options={templates}
              placeholder={t('embedBuilder.loadTemplate')}
              className="flex-1"
            />
            {templates.length > 0 && (
              <Select
                value=""
                onChange={(id) => handleDeleteTemplate(id)}
                options={templates}
                placeholder={t('embedBuilder.deleteTemplate')}
                ariaLabel={t('embedBuilder.deleteTemplateAria')}
              />
            )}
          </div>
          <div className="flex gap-2">
            <input
              value={templateName}
              onChange={(e) => setTemplateName(e.target.value)}
              placeholder={t('embedBuilder.templateNamePlaceholder')}
              className="flex-1 rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
            />
            <Button variant="secondary" onClick={handleSaveTemplate} disabled={busy}>
              {t('embedBuilder.saveAsTemplate')}
            </Button>
          </div>
          {templateNotice && <p className="text-xs text-primary">{templateNotice}</p>}
        </div>

        <label className="text-sm text-muted" htmlFor="eb-channel">
          {t('common.channel')}
        </label>
        <Select
          id="eb-channel"
          value={channelId}
          onChange={(id) => setChannelId(id)}
          options={channels}
          placeholder={t('common.selectChannel')}
        />

        {mode === 'edit' && (
          <div className="flex gap-2">
            <input
              value={messageId}
              onChange={(e) => setMessageId(e.target.value)}
              placeholder={t('embedBuilder.messageIdPlaceholder')}
              className="flex-1 rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
            />
            <Button variant="secondary" onClick={handleLoad} disabled={busy}>
              {t('embedBuilder.load')}
            </Button>
          </div>
        )}

        <label className="text-sm text-muted" htmlFor="eb-content">
          {t('embedBuilder.field.messageContent')}
        </label>
        <textarea
          id="eb-content"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          rows={2}
        />

        <label className="text-sm text-muted" htmlFor="eb-title">
          {t('embedBuilder.field.title')}
        </label>
        <input
          id="eb-title"
          value={embed.title}
          onChange={(e) => updateEmbedField('title', e.target.value)}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />

        <label className="text-sm text-muted" htmlFor="eb-description">
          {t('embedBuilder.field.description')}
        </label>
        <textarea
          id="eb-description"
          value={embed.description}
          onChange={(e) => updateEmbedField('description', e.target.value)}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          rows={3}
        />

        <label className="text-sm text-muted" htmlFor="eb-color">
          {t('embedBuilder.field.color')}
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
          {t('embedBuilder.field.author')}
        </label>
        <input
          id="eb-author-name"
          value={embed.author.name}
          onChange={(e) => updateEmbedField('author', { ...embed.author, name: e.target.value })}
          placeholder={t('embedBuilder.authorPlaceholder')}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />

        <label className="text-sm text-muted" htmlFor="eb-footer-text">
          {t('embedBuilder.field.footer')}
        </label>
        <input
          id="eb-footer-text"
          value={embed.footer.text}
          onChange={(e) => updateEmbedField('footer', { ...embed.footer, text: e.target.value })}
          placeholder={t('embedBuilder.footerPlaceholder')}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />

        <label className="text-sm text-muted" htmlFor="eb-image-url">
          {t('embedBuilder.field.imageUrl')}
        </label>
        <input
          id="eb-image-url"
          value={embed.image.url}
          onChange={(e) => updateEmbedField('image', { url: e.target.value })}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />

        <label className="text-sm text-muted" htmlFor="eb-thumbnail-url">
          {t('embedBuilder.field.thumbnailUrl')}
        </label>
        <input
          id="eb-thumbnail-url"
          value={embed.thumbnail.url}
          onChange={(e) => updateEmbedField('thumbnail', { url: e.target.value })}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />

        <Toggle
          checked={embed.timestamp !== null}
          onChange={(v) => updateEmbedField('timestamp', v ? new Date().toISOString() : null)}
          label={t('embedBuilder.timestamp')}
        />

        <div className="flex flex-col gap-2">
          {embed.fields.map((field, index) => (
            <div key={index} className="flex flex-wrap items-center gap-2 rounded-control border border-border/60 p-2">
              <input
                value={field.name}
                onChange={(e) => updateField(index, { name: e.target.value })}
                placeholder={t('embedBuilder.fieldNamePlaceholder')}
                className="min-w-0 flex-1 basis-full rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary"
              />
              <input
                value={field.value}
                onChange={(e) => updateField(index, { value: e.target.value })}
                placeholder={t('embedBuilder.fieldValuePlaceholder')}
                className="min-w-0 flex-1 basis-full rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary"
              />
              <Checkbox checked={field.inline} onChange={(v) => updateField(index, { inline: v })} label="inline" />
              <button type="button" onClick={() => removeField(index)} className="cursor-pointer text-muted hover:text-danger">
                ×
              </button>
            </div>
          ))}
          <button type="button" onClick={addField} className="cursor-pointer self-start text-sm text-primary hover:text-primary-hover">
            {t('embedBuilder.addField')}
          </button>
        </div>

        <div>
          <p className="mb-1 text-sm text-muted">{t('embedBuilder.roleButtons')}</p>
          <div className="flex flex-wrap gap-3">
            {roles.map((role) => (
              <Checkbox
                key={role.id}
                checked={roleIds.includes(role.id)}
                onChange={() => toggleRole(role.id)}
                label={role.name}
              />
            ))}
          </div>
        </div>

        {error && <p className="text-sm text-danger">{error}</p>}
        {savedResult && (
          <p className="text-sm text-success">
{t('embedBuilder.saved', { messageId: savedResult.message_id, channelId: savedResult.channel_id })}
          </p>
        )}

        <Button variant="primary" onClick={handleSave} disabled={busy}>
          {busy ? t('common.saving') : mode === 'edit' ? t('common.save') : t('embedBuilder.send')}
        </Button>
      </div>

      <div>
        <EmbedPreview content={content} embed={embed} />
      </div>
    </div>
  )
}
