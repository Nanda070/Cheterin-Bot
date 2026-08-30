import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useT } from '../context/LanguageContext'
import {
  createEmbedMessage,
  deleteEmbedTemplate,
  fetchChannels,
  fetchEmbedMessage,
  fetchEmbedTemplates,
  fetchRoles,
  saveEmbedTemplate,
  setEmbedComponentsVersion,
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
import { ComponentsVersionSelect, type ComponentsVersion } from '../components/ComponentsVersionSelect'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { EmbedPreview } from '../components/EmbedPreview'
import { EMPTY_EMBED_SPEC, normalizeEmbedSpec, validateEmbedSpec } from '../utils/embedUtils'

// Deep-link hints (?target=welcome|feedback|events) — Embeds tab under Roles & embeds
// when someone is really looking for a specific embed surface elsewhere in the dashboard.
const DEEP_LINK_HINTS: Record<string, { labelKey: string; to: string }> = {
  welcome: { labelKey: 'embedBuilder.deepLink.welcome', to: '/server-entry' },
  feedback: { labelKey: 'embedBuilder.deepLink.feedback', to: '/feedback' },
  events: { labelKey: 'embedBuilder.deepLink.events', to: '/events' },
}

export function EmbedBuilderPage() {
  const t = useT()
  const [searchParams] = useSearchParams()
  const deepLinkHint = DEEP_LINK_HINTS[searchParams.get('target') ?? '']
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
  const [componentsVersion, setComponentsVersion] = useState<ComponentsVersion>('v1')
  const [templateName, setTemplateName] = useState('')
  const [templateNotice, setTemplateNotice] = useState('')
  const [loadNotice, setLoadNotice] = useState('')

  useEffect(() => {
    fetchChannels()
      .then(setChannels)
      .catch((err) => setError(formatApiError(err, t, 'embedBuilder.error.loadChannels')))
    fetchRoles()
      .then(setRoles)
      .catch((err) => setError(formatApiError(err, t, 'embedBuilder.error.loadRoles')))
    fetchEmbedTemplates()
      .then((data) => {
        setTemplates(data.templates)
        setComponentsVersion(data.components_version)
      })
      .catch(() => {})
  }, [t])

  const handleComponentsVersion = async (version: ComponentsVersion) => {
    setComponentsVersion(version)
    try {
      const res = await setEmbedComponentsVersion(version)
      setComponentsVersion(res.components_version)
    } catch {
      // Keep local selection; send still uses local value.
    }
  }

  const applyTemplate = (id: string) => {
    const template = templates.find((t) => t.id === id)
    if (!template) return
    setContent(template.content)
    setEmbed(normalizeEmbedSpec(template.embed))
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
    setEmbed((prev) => ({
      ...prev,
      fields: (prev.fields ?? []).map((f, i) => (i === index ? { ...f, ...patch } : f)),
    }))
  }

  const addField = () => {
    setEmbed((prev) => ({ ...prev, fields: [...(prev.fields ?? []), { name: '', value: '', inline: false }] }))
  }

  const removeField = (index: number) => {
    setEmbed((prev) => ({ ...prev, fields: (prev.fields ?? []).filter((_, i) => i !== index) }))
  }

  const toggleRole = (roleId: string) => {
    setRoleIds((prev) => (prev.includes(roleId) ? prev.filter((r) => r !== roleId) : [...prev, roleId]))
  }

  const handleLoad = async () => {
    setError('')
    setLoadNotice('')
    if (!channelId || !messageId) {
      setError(t('embedBuilder.error.channelAndId'))
      return
    }
    setBusy(true)
    try {
      const data = await fetchEmbedMessage(channelId, messageId)
      setContent(typeof data.content === 'string' ? data.content : '')
      setEmbed(normalizeEmbedSpec(data.embed))
      setRoleIds(Array.isArray(data.role_ids) ? data.role_ids.map(String) : [])
      if (data.components_version === 'v2' || data.components_version === 'v1') {
        setComponentsVersion(data.components_version)
      }
      if (data.components_version === 'v2') {
        setLoadNotice(t('embedBuilder.v2LoadedNotice'))
      }
    } catch (err) {
      setError(formatApiError(err, t, 'embedBuilder.error.load'))
      setEmbed(EMPTY_EMBED_SPEC)
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
      const payload = { content, embed, role_ids: roleIds, components_version: componentsVersion }
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
        {deepLinkHint && (
          <div className="rounded-control border border-primary/40 bg-primary/10 p-3 text-sm text-foreground">
            {t(deepLinkHint.labelKey)}{' '}
            <Link to={deepLinkHint.to} className="font-medium text-primary underline">
              {t('embedBuilder.deepLink.goTo')}
            </Link>
          </div>
        )}
        <div className="flex gap-2">
          <Button variant={mode === 'create' ? 'primary' : 'secondary'} onClick={() => setMode('create')}>
            {t('embedBuilder.mode.create')}
          </Button>
          <Button variant={mode === 'edit' ? 'primary' : 'secondary'} onClick={() => setMode('edit')}>
            {t('embedBuilder.mode.edit')}
          </Button>
        </div>

        <div className="rounded-control border border-border bg-surface p-3">
          <ComponentsVersionSelect value={componentsVersion} onChange={handleComponentsVersion} />
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
        {loadNotice && <p className="text-sm text-muted">{loadNotice}</p>}

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
          value={embed.title ?? ''}
          onChange={(e) => updateEmbedField('title', e.target.value)}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />

        <label className="text-sm text-muted" htmlFor="eb-description">
          {t('embedBuilder.field.description')}
        </label>
        <textarea
          id="eb-description"
          value={embed.description ?? ''}
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
            value={embed.color || '#D44556'}
            onChange={(e) => updateEmbedField('color', e.target.value)}
            className="h-9 w-12 rounded-control border border-border bg-background"
          />
          <input
            value={embed.color ?? ''}
            onChange={(e) => updateEmbedField('color', e.target.value)}
            placeholder="#D44556"
            className="flex-1 rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />
        </div>

        <label className="text-sm text-muted" htmlFor="eb-author-name">
          {t('embedBuilder.field.author')}
        </label>
        <input
          id="eb-author-name"
          value={embed.author?.name ?? ''}
          onChange={(e) =>
            updateEmbedField('author', { ...(embed.author ?? EMPTY_EMBED_SPEC.author), name: e.target.value })
          }
          placeholder={t('embedBuilder.authorPlaceholder')}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />

        <label className="text-sm text-muted" htmlFor="eb-footer-text">
          {t('embedBuilder.field.footer')}
        </label>
        <input
          id="eb-footer-text"
          value={embed.footer?.text ?? ''}
          onChange={(e) =>
            updateEmbedField('footer', { ...(embed.footer ?? EMPTY_EMBED_SPEC.footer), text: e.target.value })
          }
          placeholder={t('embedBuilder.footerPlaceholder')}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />

        <label className="text-sm text-muted" htmlFor="eb-image-url">
          {t('embedBuilder.field.imageUrl')}
        </label>
        <input
          id="eb-image-url"
          value={embed.image?.url ?? ''}
          onChange={(e) => updateEmbedField('image', { url: e.target.value })}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />

        <label className="text-sm text-muted" htmlFor="eb-thumbnail-url">
          {t('embedBuilder.field.thumbnailUrl')}
        </label>
        <input
          id="eb-thumbnail-url"
          value={embed.thumbnail?.url ?? ''}
          onChange={(e) => updateEmbedField('thumbnail', { url: e.target.value })}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />

        <Toggle
          checked={embed.timestamp !== null}
          onChange={(v) => updateEmbedField('timestamp', v ? new Date().toISOString() : null)}
          label={t('embedBuilder.timestamp')}
        />

        <div className="flex flex-col gap-2">
          {(embed.fields ?? []).map((field, index) => (
            <div key={index} className="flex flex-wrap items-center gap-2 rounded-control border border-border/60 p-2">
              <input
                value={field.name ?? ''}
                onChange={(e) => updateField(index, { name: e.target.value })}
                placeholder={t('embedBuilder.fieldNamePlaceholder')}
                className="min-w-0 flex-1 basis-full rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary"
              />
              <input
                value={field.value ?? ''}
                onChange={(e) => updateField(index, { value: e.target.value })}
                placeholder={t('embedBuilder.fieldValuePlaceholder')}
                className="min-w-0 flex-1 basis-full rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary"
              />
              <Checkbox checked={Boolean(field.inline)} onChange={(v) => updateField(index, { inline: v })} label="inline" />
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
