import { useEffect, useState } from 'react'
import { useT } from '../context/LanguageContext'
import {
  createFeedbackCategory,
  deleteFeedbackCategory,
  fetchChannels,
  fetchFeedbackCategories,
  fetchRoles,
  publishFeedbackPanel,
  updateFeedbackCategory,
  type ChannelInfo,
  type FeedbackCategoryFieldSpec,
  type FeedbackCategorySpec,
  type RoleInfo,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Checkbox } from '../components/ui/Checkbox'
import { Select } from '../components/ui/Select'
import { Modal } from '../components/ui/Modal'

const EMPTY_FIELD: FeedbackCategoryFieldSpec = { key: '', label: '', style: 'short', required: true, max_length: 200 }

type TranslateFn = (key: string, params?: Record<string, string | number>) => string

function defaultTemplate(t: TranslateFn): FeedbackCategorySpec {
  return {
    key: 'players',
    title: t('feedback.template.title'),
    button_label: t('feedback.template.buttonLabel'),
    channel_id: '',
    case_prefix: 'PR',
    case_title: t('feedback.template.caseTitle'),
    thread_name: 'player-report',
    review_role_ids: [],
    approved_text: t('feedback.template.approvedText'),
    denied_text: t('feedback.template.deniedText'),
    modal_title: t('feedback.template.modalTitle'),
    fields: [
      {
        key: 'offender',
        label: t('feedback.template.fields.offender'),
        style: 'short',
        required: true,
        max_length: 120,
      },
      {
        key: 'complaint',
        label: t('feedback.template.fields.complaint'),
        style: 'paragraph',
        required: true,
        max_length: 1000,
      },
      {
        key: 'datetime',
        label: t('feedback.template.fields.datetime'),
        style: 'short',
        required: false,
        max_length: 120,
      },
      {
        key: 'proof',
        label: t('feedback.template.fields.proof'),
        style: 'paragraph',
        required: false,
        max_length: 1000,
      },
    ],
    mini_summary_key: 'offender',
  }
}

function emptySpec(): FeedbackCategorySpec {
  return {
    key: '',
    title: '',
    button_label: '',
    channel_id: '',
    case_prefix: '',
    case_title: '',
    thread_name: '',
    review_role_ids: [],
    approved_text: '',
    denied_text: '',
    modal_title: '',
    fields: [{ ...EMPTY_FIELD }],
    mini_summary_key: '',
  }
}

export function FeedbackCategoriesPage() {
  const t = useT()
  const [categories, setCategories] = useState<FeedbackCategorySpec[]>([])
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [formOpen, setFormOpen] = useState(false)
  const [editingKey, setEditingKey] = useState<string | null>(null)
  const [spec, setSpec] = useState<FeedbackCategorySpec>(emptySpec())
  const [pendingDelete, setPendingDelete] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [publishOpen, setPublishOpen] = useState(false)
  const [publishChannelId, setPublishChannelId] = useState('')
  const [publishBusy, setPublishBusy] = useState(false)
  const [publishError, setPublishError] = useState('')

  const reload = () => {
    fetchFeedbackCategories().then(setCategories).catch(() => setError(t('feedback.categories.errorLoad')))
    fetchChannels().then(setChannels).catch(() => {})
    fetchRoles().then(setRoles).catch(() => {})
  }

  useEffect(reload, [])

  const channelName = (id: string) => channels.find((c) => c.id === id)?.name ?? id

  const openCreate = () => {
    setEditingKey(null)
    setSpec(emptySpec())
    setError('')
    setFormOpen(true)
  }

  const openDefaultTemplate = () => {
    setEditingKey(null)
    const template = defaultTemplate(t)
    setSpec({ ...template, fields: template.fields.map((f) => ({ ...f })) })
    setError('')
    setFormOpen(true)
  }

  const openPublish = () => {
    setPublishChannelId('')
    setPublishError('')
    setPublishOpen(true)
  }

  const publish = async () => {
    if (!publishChannelId) {
      setPublishError(t('feedback.categories.publish.errorChannel'))
      return
    }
    setPublishBusy(true)
    setPublishError('')
    try {
      await publishFeedbackPanel(publishChannelId)
      setPublishOpen(false)
    } catch (err) {
      setPublishError(formatApiError(err, t, 'feedback.categories.publish.error'))
    } finally {
      setPublishBusy(false)
    }
  }

  const openEdit = (category: FeedbackCategorySpec) => {
    setEditingKey(category.key)
    setSpec({ ...category })
    setError('')
    setFormOpen(true)
  }

  const updateField = (index: number, patch: Partial<FeedbackCategoryFieldSpec>) => {
    setSpec((prev) => ({
      ...prev,
      fields: prev.fields.map((f, i) => (i === index ? { ...f, ...patch } : f)),
    }))
  }

  const addField = () => {
    if (spec.fields.length >= 5) return
    setSpec((prev) => ({ ...prev, fields: [...prev.fields, { ...EMPTY_FIELD }] }))
  }

  const removeField = (index: number) => {
    setSpec((prev) => ({ ...prev, fields: prev.fields.filter((_, i) => i !== index) }))
  }

  const toggleRole = (roleId: string) => {
    setSpec((prev) => ({
      ...prev,
      review_role_ids: prev.review_role_ids.includes(roleId)
        ? prev.review_role_ids.filter((r) => r !== roleId)
        : [...prev.review_role_ids, roleId],
    }))
  }

  const save = async () => {
    setError('')
    setBusy(true)
    try {
      const { key, ...rest } = spec
      if (editingKey) {
        await updateFeedbackCategory(editingKey, rest)
      } else {
        await createFeedbackCategory(spec)
      }
      setFormOpen(false)
      reload()
    } catch (err) {
      setError(formatApiError(err, t, 'feedback.categories.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  const confirmDelete = async () => {
    if (!pendingDelete) return
    try {
      await deleteFeedbackCategory(pendingDelete)
      setPendingDelete(null)
      reload()
    } catch (err) {
      setError(formatApiError(err, t, 'feedback.categories.errorDelete'))
    }
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-foreground">{t('feedback.categories.title')}</h1>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={openDefaultTemplate}>
            {t('feedback.categories.defaultTemplate')}
          </Button>
          <Button variant="secondary" onClick={openPublish}>
            {t('common.publish')}
          </Button>
          <Button variant="primary" onClick={openCreate}>
            {t('feedback.categories.create')}
          </Button>
        </div>
      </div>

      {error && !formOpen && <p className="mb-4 text-sm text-danger">{error}</p>}

      <div className="flex flex-col gap-2">
        {categories.map((category) => (
          <Card key={category.key} className="flex items-center justify-between !p-3">
            <div>
              <p className="text-sm text-foreground">{category.title}</p>
              <p className="text-xs text-muted">
                {t('feedback.categories.fieldsCount', {
                  prefix: category.case_prefix,
                  channel: channelName(category.channel_id),
                  count: category.fields.length,
                })}
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => openEdit(category)}>
                {t('feedback.categories.edit')}
              </Button>
              <Button variant="danger" onClick={() => setPendingDelete(category.key)}>
                {t('common.delete')}
              </Button>
            </div>
          </Card>
        ))}
        {categories.length === 0 && <p className="text-sm text-muted">{t('feedback.categories.empty')}</p>}
      </div>

      <Modal
        open={formOpen}
        title={editingKey ? t('feedback.categories.modal.edit') : t('feedback.categories.modal.create')}
        onClose={() => setFormOpen(false)}
      >
        <div className="flex max-h-[70vh] flex-col gap-3 overflow-y-auto">
          <label className="text-sm text-muted" htmlFor="fc-key">
            {t('feedback.categories.field.key')}
          </label>
          <input
            id="fc-key"
            value={spec.key}
            onChange={(e) => setSpec((prev) => ({ ...prev, key: e.target.value }))}
            disabled={!!editingKey}
            placeholder="players"
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary disabled:opacity-50"
          />

          <label className="text-sm text-muted" htmlFor="fc-title">
            {t('feedback.categories.field.title')}
          </label>
          <input
            id="fc-title"
            value={spec.title}
            onChange={(e) => setSpec((prev) => ({ ...prev, title: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-button-label">
            {t('feedback.categories.field.buttonLabel')}
          </label>
          <input
            id="fc-button-label"
            value={spec.button_label}
            onChange={(e) => setSpec((prev) => ({ ...prev, button_label: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-case-title">
            {t('feedback.categories.field.caseTitle')}
          </label>
          <input
            id="fc-case-title"
            value={spec.case_title}
            onChange={(e) => setSpec((prev) => ({ ...prev, case_title: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-modal-title">
            {t('feedback.categories.field.modalTitle')}
          </label>
          <input
            id="fc-modal-title"
            value={spec.modal_title}
            onChange={(e) => setSpec((prev) => ({ ...prev, modal_title: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-thread-name">
            {t('feedback.categories.field.threadName')}
          </label>
          <input
            id="fc-thread-name"
            value={spec.thread_name}
            onChange={(e) => setSpec((prev) => ({ ...prev, thread_name: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-case-prefix">
            {t('feedback.categories.field.casePrefix')}
          </label>
          <input
            id="fc-case-prefix"
            value={spec.case_prefix}
            onChange={(e) => setSpec((prev) => ({ ...prev, case_prefix: e.target.value.toUpperCase() }))}
            placeholder="PR"
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-channel">
            {t('common.channel')}
          </label>
          <Select
            id="fc-channel"
            value={spec.channel_id}
            onChange={(id) => setSpec((prev) => ({ ...prev, channel_id: id }))}
            options={channels}
            placeholder={t('common.selectChannel')}
          />

          <div>
            <p className="mb-1 text-sm text-muted">{t('feedback.categories.field.reviewRoles')}</p>
            <div className="flex flex-wrap gap-3">
              {roles.map((role) => (
                <Checkbox
                  key={role.id}
                  checked={spec.review_role_ids.includes(role.id)}
                  onChange={() => toggleRole(role.id)}
                  label={role.name}
                />
              ))}
            </div>
          </div>

          <label className="text-sm text-muted" htmlFor="fc-approved-text">
            {t('feedback.categories.field.approvedText')}
          </label>
          <input
            id="fc-approved-text"
            value={spec.approved_text}
            onChange={(e) => setSpec((prev) => ({ ...prev, approved_text: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-denied-text">
            {t('feedback.categories.field.deniedText')}
          </label>
          <input
            id="fc-denied-text"
            value={spec.denied_text}
            onChange={(e) => setSpec((prev) => ({ ...prev, denied_text: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <div className="flex flex-col gap-2">
            <p className="text-sm text-muted">{t('feedback.categories.formFields')}</p>
            {spec.fields.map((field, index) => (
              <div key={index} className="flex flex-wrap items-center gap-2 rounded-control border border-border/60 p-2">
                <input
                  value={field.key}
                  onChange={(e) => updateField(index, { key: e.target.value })}
                  placeholder={t('feedback.categories.fieldKeyPlaceholder')}
                  className="min-w-0 flex-1 basis-full rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary"
                />
                <input
                  value={field.label}
                  onChange={(e) => updateField(index, { label: e.target.value })}
                  placeholder={t('feedback.categories.fieldLabelPlaceholder')}
                  className="min-w-0 flex-1 basis-full rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary"
                />
                <Select
                  ariaLabel={t('feedback.categories.fieldType')}
                  value={field.style}
                  onChange={(id) => updateField(index, { style: id as 'short' | 'paragraph' })}
                  options={[
                    { id: 'short', name: t('feedback.categories.fieldType.short') },
                    { id: 'paragraph', name: t('feedback.categories.fieldType.paragraph') },
                  ]}
                  className="w-40"
                />
                <Checkbox
                  checked={field.required}
                  onChange={(v) => updateField(index, { required: v })}
                  label={t('common.required')}
                />
                <button
                  type="button"
                  onClick={() => removeField(index)}
                  className="cursor-pointer text-muted hover:text-danger"
                >
                  ×
                </button>
              </div>
            ))}
            {spec.fields.length < 5 && (
              <button
                type="button"
                onClick={addField}
                className="cursor-pointer self-start text-sm text-primary hover:text-primary-hover"
              >
                {t('common.addField')}
              </button>
            )}
          </div>

          <label className="text-sm text-muted" htmlFor="fc-mini-summary">
            {t('feedback.categories.miniSummary')}
          </label>
          <Select
            id="fc-mini-summary"
            value={spec.mini_summary_key}
            onChange={(id) => setSpec((prev) => ({ ...prev, mini_summary_key: id }))}
            options={spec.fields.filter((f) => f.key).map((f) => ({ id: f.key, name: f.label || f.key }))}
            placeholder={t('common.selectField')}
          />

          {error && <p className="text-sm text-danger">{error}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setFormOpen(false)} disabled={busy}>
              {t('common.cancel')}
            </Button>
            <Button variant="primary" onClick={save} disabled={busy}>
              {busy ? t('common.saving') : t('common.save')}
            </Button>
          </div>
        </div>
      </Modal>

      <Modal open={pendingDelete !== null} title={t('feedback.categories.deleteConfirm')} onClose={() => setPendingDelete(null)}>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" onClick={() => setPendingDelete(null)}>
            {t('common.cancel')}
          </Button>
          <Button variant="danger" onClick={confirmDelete}>
            {t('feedback.categories.deleteAction')}
          </Button>
        </div>
      </Modal>

      <Modal open={publishOpen} title={t('feedback.categories.publishModal.title')} onClose={() => setPublishOpen(false)}>
        <div className="flex flex-col gap-3">
          <label className="text-sm text-muted" htmlFor="fc-publish-channel">
            {t('common.channel')}
          </label>
          <Select
            id="fc-publish-channel"
            value={publishChannelId}
            onChange={(id) => setPublishChannelId(id)}
            options={channels}
            placeholder={t('common.selectChannel')}
          />

          {publishError && <p className="text-sm text-danger">{publishError}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setPublishOpen(false)} disabled={publishBusy}>
              {t('common.cancel')}
            </Button>
            <Button variant="primary" onClick={publish} disabled={publishBusy}>
              {publishBusy ? t('common.publishing') : t('common.publish')}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
