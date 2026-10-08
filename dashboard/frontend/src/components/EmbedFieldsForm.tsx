import { useT } from '../context/LanguageContext'
import type { EmbedFieldSpec, EmbedSpec } from '../api/client'
import { EMPTY_EMBED_SPEC } from '../utils/embedUtils'
import { Checkbox } from './ui/Checkbox'
import { Toggle } from './ui/Toggle'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'
const fieldInputClass =
  'min-w-0 flex-1 basis-full rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary'

interface Props {
  embed: EmbedSpec
  onChange: (embed: EmbedSpec) => void
}

/** Inputs for one embed of the Embed Builder message (title … fields). */
export function EmbedFieldsForm({ embed, onChange }: Props) {
  const t = useT()

  const update = <K extends keyof EmbedSpec>(key: K, value: EmbedSpec[K]) => {
    onChange({ ...embed, [key]: value })
  }

  const updateField = (index: number, patch: Partial<EmbedFieldSpec>) => {
    update(
      'fields',
      (embed.fields ?? []).map((f, i) => (i === index ? { ...f, ...patch } : f)),
    )
  }

  const addField = () => {
    update('fields', [...(embed.fields ?? []), { name: '', value: '', inline: false }])
  }

  const removeField = (index: number) => {
    update(
      'fields',
      (embed.fields ?? []).filter((_, i) => i !== index),
    )
  }

  return (
    <>
      <label className="text-sm text-muted" htmlFor="eb-title">
        {t('embedBuilder.field.title')}
      </label>
      <input
        id="eb-title"
        value={embed.title ?? ''}
        onChange={(e) => update('title', e.target.value)}
        className={inputClass}
      />

      <label className="text-sm text-muted" htmlFor="eb-description">
        {t('embedBuilder.field.description')}
      </label>
      <textarea
        id="eb-description"
        value={embed.description ?? ''}
        onChange={(e) => update('description', e.target.value)}
        className={inputClass}
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
          onChange={(e) => update('color', e.target.value)}
          className="h-9 w-12 rounded-control border border-border bg-background"
        />
        <input
          value={embed.color ?? ''}
          onChange={(e) => update('color', e.target.value)}
          placeholder="#D44556"
          className={`flex-1 ${inputClass}`}
        />
      </div>

      <label className="text-sm text-muted" htmlFor="eb-author-name">
        {t('embedBuilder.field.author')}
      </label>
      <input
        id="eb-author-name"
        value={embed.author?.name ?? ''}
        onChange={(e) => update('author', { ...(embed.author ?? EMPTY_EMBED_SPEC.author), name: e.target.value })}
        placeholder={t('embedBuilder.authorPlaceholder')}
        className={inputClass}
      />

      <label className="text-sm text-muted" htmlFor="eb-footer-text">
        {t('embedBuilder.field.footer')}
      </label>
      <input
        id="eb-footer-text"
        value={embed.footer?.text ?? ''}
        onChange={(e) => update('footer', { ...(embed.footer ?? EMPTY_EMBED_SPEC.footer), text: e.target.value })}
        placeholder={t('embedBuilder.footerPlaceholder')}
        className={inputClass}
      />

      <label className="text-sm text-muted" htmlFor="eb-image-url">
        {t('embedBuilder.field.imageUrl')}
      </label>
      <input
        id="eb-image-url"
        value={embed.image?.url ?? ''}
        onChange={(e) => update('image', { url: e.target.value })}
        className={inputClass}
      />

      <label className="text-sm text-muted" htmlFor="eb-thumbnail-url">
        {t('embedBuilder.field.thumbnailUrl')}
      </label>
      <input
        id="eb-thumbnail-url"
        value={embed.thumbnail?.url ?? ''}
        onChange={(e) => update('thumbnail', { url: e.target.value })}
        className={inputClass}
      />

      <Toggle
        checked={embed.timestamp !== null}
        onChange={(v) => update('timestamp', v ? new Date().toISOString() : null)}
        label={t('embedBuilder.timestamp')}
      />

      <div className="flex flex-col gap-2">
        {(embed.fields ?? []).map((field, index) => (
          <div key={index} className="flex flex-wrap items-center gap-2 rounded-control border border-border/60 p-2">
            <input
              value={field.name ?? ''}
              onChange={(e) => updateField(index, { name: e.target.value })}
              placeholder={t('embedBuilder.fieldNamePlaceholder')}
              className={fieldInputClass}
            />
            <input
              value={field.value ?? ''}
              onChange={(e) => updateField(index, { value: e.target.value })}
              placeholder={t('embedBuilder.fieldValuePlaceholder')}
              className={fieldInputClass}
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
    </>
  )
}
