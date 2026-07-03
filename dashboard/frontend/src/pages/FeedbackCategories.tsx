import { useEffect, useState } from 'react'
import {
  createFeedbackCategory,
  deleteFeedbackCategory,
  fetchChannels,
  fetchFeedbackCategories,
  fetchRoles,
  updateFeedbackCategory,
  type ChannelInfo,
  type FeedbackCategoryFieldSpec,
  type FeedbackCategorySpec,
  type RoleInfo,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'

const EMPTY_FIELD: FeedbackCategoryFieldSpec = { key: '', label: '', style: 'short', required: true, max_length: 200 }

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
  const [categories, setCategories] = useState<FeedbackCategorySpec[]>([])
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [formOpen, setFormOpen] = useState(false)
  const [editingKey, setEditingKey] = useState<string | null>(null)
  const [spec, setSpec] = useState<FeedbackCategorySpec>(emptySpec())
  const [pendingDelete, setPendingDelete] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const reload = () => {
    fetchFeedbackCategories().then(setCategories).catch(() => setError('Не удалось загрузить категории'))
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
    } catch {
      setError('Не удалось сохранить категорию — проверьте ключ, префикс, канал и роли')
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
    } catch {
      setError('Не удалось удалить категорию')
    }
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-foreground">Категории обращений</h1>
        <Button variant="primary" onClick={openCreate}>
          Создать категорию
        </Button>
      </div>

      {error && !formOpen && <p className="mb-4 text-sm text-danger">{error}</p>}

      <div className="flex flex-col gap-2">
        {categories.map((category) => (
          <Card key={category.key} className="flex items-center justify-between !p-3">
            <div>
              <p className="text-sm text-foreground">{category.title}</p>
              <p className="text-xs text-muted">
                {category.case_prefix} · {channelName(category.channel_id)} · полей: {category.fields.length}
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => openEdit(category)}>
                Edit
              </Button>
              <Button variant="danger" onClick={() => setPendingDelete(category.key)}>
                Удалить
              </Button>
            </div>
          </Card>
        ))}
        {categories.length === 0 && <p className="text-sm text-muted">Категорий пока нет.</p>}
      </div>

      <Modal
        open={formOpen}
        title={editingKey ? 'Редактировать категорию' : 'Создать категорию'}
        onClose={() => setFormOpen(false)}
      >
        <div className="flex max-h-[70vh] flex-col gap-3 overflow-y-auto">
          <label className="text-sm text-muted" htmlFor="fc-key">
            Ключ
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
            Название
          </label>
          <input
            id="fc-title"
            value={spec.title}
            onChange={(e) => setSpec((prev) => ({ ...prev, title: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-button-label">
            Текст кнопки
          </label>
          <input
            id="fc-button-label"
            value={spec.button_label}
            onChange={(e) => setSpec((prev) => ({ ...prev, button_label: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-case-title">
            Заголовок дела
          </label>
          <input
            id="fc-case-title"
            value={spec.case_title}
            onChange={(e) => setSpec((prev) => ({ ...prev, case_title: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-modal-title">
            Заголовок формы
          </label>
          <input
            id="fc-modal-title"
            value={spec.modal_title}
            onChange={(e) => setSpec((prev) => ({ ...prev, modal_title: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-thread-name">
            Имя треда
          </label>
          <input
            id="fc-thread-name"
            value={spec.thread_name}
            onChange={(e) => setSpec((prev) => ({ ...prev, thread_name: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-case-prefix">
            Префикс дела
          </label>
          <input
            id="fc-case-prefix"
            value={spec.case_prefix}
            onChange={(e) => setSpec((prev) => ({ ...prev, case_prefix: e.target.value.toUpperCase() }))}
            placeholder="PR"
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-channel">
            Канал
          </label>
          <select
            id="fc-channel"
            value={spec.channel_id}
            onChange={(e) => setSpec((prev) => ({ ...prev, channel_id: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
          >
            <option value="">Выберите канал…</option>
            {channels.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>

          <div>
            <p className="mb-1 text-sm text-muted">Роли-ревьюеры</p>
            <div className="flex flex-wrap gap-2">
              {roles.map((role) => (
                <label key={role.id} className="flex items-center gap-1 text-xs text-foreground">
                  <input
                    type="checkbox"
                    checked={spec.review_role_ids.includes(role.id)}
                    onChange={() => toggleRole(role.id)}
                  />
                  {role.name}
                </label>
              ))}
            </div>
          </div>

          <label className="text-sm text-muted" htmlFor="fc-approved-text">
            Текст при принятии
          </label>
          <input
            id="fc-approved-text"
            value={spec.approved_text}
            onChange={(e) => setSpec((prev) => ({ ...prev, approved_text: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-denied-text">
            Текст при отклонении
          </label>
          <input
            id="fc-denied-text"
            value={spec.denied_text}
            onChange={(e) => setSpec((prev) => ({ ...prev, denied_text: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <div className="flex flex-col gap-2">
            <p className="text-sm text-muted">Поля формы (до 5)</p>
            {spec.fields.map((field, index) => (
              <div key={index} className="flex flex-wrap items-center gap-2 rounded-control border border-border/60 p-2">
                <input
                  value={field.key}
                  onChange={(e) => updateField(index, { key: e.target.value })}
                  placeholder="Ключ поля"
                  className="min-w-0 flex-1 basis-full rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary"
                />
                <input
                  value={field.label}
                  onChange={(e) => updateField(index, { label: e.target.value })}
                  placeholder="Название поля"
                  className="min-w-0 flex-1 basis-full rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary"
                />
                <select
                  aria-label="Тип поля"
                  value={field.style}
                  onChange={(e) => updateField(index, { style: e.target.value as 'short' | 'paragraph' })}
                  className="rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground"
                >
                  <option value="short">Короткий</option>
                  <option value="paragraph">Многострочный</option>
                </select>
                <label className="flex items-center gap-1 text-xs text-muted">
                  <input
                    type="checkbox"
                    checked={field.required}
                    onChange={(e) => updateField(index, { required: e.target.checked })}
                  />
                  обязательное
                </label>
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
                + Добавить поле
              </button>
            )}
          </div>

          <label className="text-sm text-muted" htmlFor="fc-mini-summary">
            Поле для краткого превью
          </label>
          <select
            id="fc-mini-summary"
            value={spec.mini_summary_key}
            onChange={(e) => setSpec((prev) => ({ ...prev, mini_summary_key: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
          >
            <option value="">Выберите поле…</option>
            {spec.fields
              .filter((f) => f.key)
              .map((f) => (
                <option key={f.key} value={f.key}>
                  {f.label || f.key}
                </option>
              ))}
          </select>

          {error && <p className="text-sm text-danger">{error}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setFormOpen(false)} disabled={busy}>
              Отмена
            </Button>
            <Button variant="primary" onClick={save} disabled={busy}>
              {busy ? 'Сохраняем…' : 'Сохранить'}
            </Button>
          </div>
        </div>
      </Modal>

      <Modal open={pendingDelete !== null} title="Удалить категорию?" onClose={() => setPendingDelete(null)}>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" onClick={() => setPendingDelete(null)}>
            Отмена
          </Button>
          <Button variant="danger" onClick={confirmDelete}>
            Удалить категорию
          </Button>
        </div>
      </Modal>
    </div>
  )
}
