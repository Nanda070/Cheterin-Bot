import { useEffect, useMemo, useState } from 'react'
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
  saveEmbedTemplatesBulk,
  setEmbedComponentsVersion,
  updateEmbedMessage,
  type ChannelInfo,
  type EmbedSpec,
  type EmbedTemplate,
  type RoleInfo,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Checkbox } from '../components/ui/Checkbox'
import { ComponentsVersionSelect, type ComponentsVersion } from '../components/ComponentsVersionSelect'
import { Select } from '../components/ui/Select'
import { EmbedFieldsForm } from '../components/EmbedFieldsForm'
import { EmbedPreview } from '../components/EmbedPreview'
import { JsonImportPanel } from '../components/JsonImportPanel'
import { PlaceholderInputs } from '../components/PlaceholderInputs'
import {
  MAX_EMBEDS,
  embedsFromPayload,
  isEmbedSpecEmpty,
  normalizeEmbedSpec,
  validateEmbedSpecs,
} from '../utils/embedUtils'
import { exportMessageJson, type ImportedMessage } from '../utils/messageJson'
import { applyPlaceholders, findPlaceholders } from '../utils/placeholders'

// Deep-link hints (?target=welcome|feedback|events) — Embeds tab under Roles & embeds
// when someone is really looking for a specific embed surface elsewhere in the dashboard.
const DEEP_LINK_HINTS: Record<string, { labelKey: string; to: string }> = {
  welcome: { labelKey: 'embedBuilder.deepLink.welcome', to: '/server-entry' },
  feedback: { labelKey: 'embedBuilder.deepLink.feedback', to: '/feedback' },
  events: { labelKey: 'embedBuilder.deepLink.events', to: '/events' },
}

/** Templates per bulk request: well under the backend cap (200) and the 1 MB request body limit. */
const BULK_TEMPLATES_CHUNK = 50

const blankEmbed = (): EmbedSpec => normalizeEmbedSpec({})

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
  // A message carries up to MAX_EMBEDS embeds; the form edits the active one. Never empty.
  const [embeds, setEmbeds] = useState<EmbedSpec[]>(() => [blankEmbed()])
  const [activeEmbed, setActiveEmbed] = useState(0)
  const [placeholderValues, setPlaceholderValues] = useState<Record<string, string>>({})
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

  const currentIndex = Math.min(activeEmbed, embeds.length - 1)
  const placeholderNames = useMemo(() => findPlaceholders(content, embeds), [content, embeds])
  // What actually goes to Discord (and into the preview): placeholders filled in.
  const filled = useMemo(
    () => applyPlaceholders(content, embeds, placeholderValues),
    [content, embeds, placeholderValues],
  )
  const unfilledPlaceholders = placeholderNames.filter((name) => !placeholderValues[name])

  /** Replace the whole message in the form (template, existing message or imported JSON). */
  const loadMessage = (nextContent: string, nextEmbeds: EmbedSpec[]) => {
    setContent(nextContent)
    setEmbeds(nextEmbeds.length > 0 ? nextEmbeds.slice(0, MAX_EMBEDS) : [blankEmbed()])
    setActiveEmbed(0)
  }

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
    loadMessage(template.content, embedsFromPayload(template))
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
    const validationError = validateEmbedSpecs(embeds, content)
    if (validationError) {
      setError(t(validationError))
      return
    }
    setBusy(true)
    try {
      // Templates keep the raw text: {placeholders} stay unfilled for the next use.
      const created = await saveEmbedTemplate({
        name,
        content,
        embeds: embeds.filter((embed) => !isEmbedSpecEmpty(embed)),
        role_ids: roleIds,
      })
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

  const handleSaveAllTemplates = async (messages: ImportedMessage[]) => {
    const items = messages.map(({ name, content, embeds }) => ({ name, content, embeds }))
    let created = 0
    let skipped = 0
    for (let offset = 0; offset < items.length; offset += BULK_TEMPLATES_CHUNK) {
      const result = await saveEmbedTemplatesBulk(items.slice(offset, offset + BULK_TEMPLATES_CHUNK))
      setTemplates((prev) => [...prev, ...result.created])
      created += result.created.length
      skipped += result.skipped.length
    }
    return { created, skipped }
  }

  const updateCurrentEmbed = (next: EmbedSpec) => {
    setEmbeds((prev) => prev.map((embed, index) => (index === currentIndex ? next : embed)))
  }

  const addEmbed = () => {
    if (embeds.length >= MAX_EMBEDS) return
    setEmbeds((prev) => [...prev, blankEmbed()])
    setActiveEmbed(embeds.length)
  }

  const removeCurrentEmbed = () => {
    if (embeds.length <= 1) return
    setEmbeds((prev) => prev.filter((_, index) => index !== currentIndex))
    setActiveEmbed(Math.max(0, Math.min(currentIndex, embeds.length - 2)))
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
      loadMessage(typeof data.content === 'string' ? data.content : '', embedsFromPayload(data))
      setRoleIds(Array.isArray(data.role_ids) ? data.role_ids.map(String) : [])
      if (data.components_version === 'v2' || data.components_version === 'v1') {
        setComponentsVersion(data.components_version)
      }
      if (data.components_version === 'v2') {
        setLoadNotice(t('embedBuilder.v2LoadedNotice'))
      }
    } catch (err) {
      setError(formatApiError(err, t, 'embedBuilder.error.load'))
      loadMessage(content, [])
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
    const validationError = validateEmbedSpecs(filled.embeds, filled.content)
    if (validationError) {
      setError(t(validationError))
      return
    }

    setBusy(true)
    try {
      const payload = {
        content: filled.content,
        embeds: filled.embeds.filter((embed) => !isEmbedSpecEmpty(embed)),
        role_ids: roleIds,
        components_version: componentsVersion,
      }
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
      <div className="flex min-w-0 flex-col gap-3">
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

        <JsonImportPanel
          exportJson={() => exportMessageJson(content, embeds)}
          onLoad={(message) => loadMessage(message.content, message.embeds)}
          onSaveAll={handleSaveAllTemplates}
          busy={busy}
        />

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

        <div className="flex flex-wrap items-center gap-2">
          {embeds.map((_, index) => (
            <button
              key={index}
              type="button"
              onClick={() => setActiveEmbed(index)}
              aria-pressed={index === currentIndex}
              className={`cursor-pointer rounded-control border px-3 py-1.5 text-sm transition-colors ${
                index === currentIndex
                  ? 'border-primary bg-primary-muted text-foreground'
                  : 'border-border text-muted hover:text-foreground'
              }`}
            >
              {t('embedBuilder.embedTab', { n: index + 1 })}
            </button>
          ))}
          <button
            type="button"
            onClick={addEmbed}
            disabled={embeds.length >= MAX_EMBEDS}
            className="cursor-pointer text-sm text-primary hover:text-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
          >
            {t('embedBuilder.addEmbed')}
          </button>
          <button
            type="button"
            onClick={removeCurrentEmbed}
            disabled={embeds.length <= 1}
            className="ml-auto cursor-pointer text-sm text-muted hover:text-danger disabled:cursor-not-allowed disabled:opacity-50"
          >
            {t('embedBuilder.removeEmbed')}
          </button>
        </div>

        <EmbedFieldsForm embed={embeds[currentIndex]} onChange={updateCurrentEmbed} />

        <PlaceholderInputs
          names={placeholderNames}
          values={placeholderValues}
          onChange={(name, value) => setPlaceholderValues((prev) => ({ ...prev, [name]: value }))}
        />

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
        {unfilledPlaceholders.length > 0 && (
          <p className="text-xs text-warning">
            {t('embedBuilder.placeholders.unfilled', {
              names: unfilledPlaceholders.map((name) => `{${name}}`).join(', '),
            })}
          </p>
        )}

        <Button variant="primary" onClick={handleSave} disabled={busy}>
          {busy ? t('common.saving') : mode === 'edit' ? t('common.save') : t('embedBuilder.send')}
        </Button>
      </div>

      <div className="min-w-0">
        <EmbedPreview content={filled.content} embeds={filled.embeds} />
      </div>
    </div>
  )
}
