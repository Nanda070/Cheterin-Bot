import { useT } from '../context/LanguageContext'
import type { EmbedFieldSpec, EmbedSpec } from '../api/client'
import { Toggle } from './ui/Toggle'
import { EmbedPreview } from './EmbedPreview'

export const EMPTY_EMBED_SPEC: EmbedSpec = {
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

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

interface Props {
  content?: string
  onContentChange?: (value: string) => void
  embed: EmbedSpec
  onEmbedChange: (embed: EmbedSpec) => void
  showContent?: boolean
  showFields?: boolean
  placeholderHint?: string
}

export function EmbedEditor({
  content = '',
  onContentChange,
  embed,
  onEmbedChange,
  showContent = true,
  showFields = true,
  placeholderHint,
}: Props) {
  const t = useT()

  const updateEmbedField = <K extends keyof EmbedSpec>(key: K, value: EmbedSpec[K]) => {
    onEmbedChange({ ...embed, [key]: value })
  }

  const updateField = (index: number, patch: Partial<EmbedFieldSpec>) => {
    const fields = embed.fields.map((field, i) => (i === index ? { ...field, ...patch } : field))
    onEmbedChange({ ...embed, fields })
  }

  const addField = () => {
    if (embed.fields.length >= 25) return
    onEmbedChange({ ...embed, fields: [...embed.fields, { name: '', value: '', inline: false }] })
  }

  const removeField = (index: number) => {
    onEmbedChange({ ...embed, fields: embed.fields.filter((_, i) => i !== index) })
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="flex flex-col gap-3">
        {placeholderHint && <p className="text-xs text-muted">{placeholderHint}</p>}
        {showContent && onContentChange && (
          <>
            <label className="text-sm text-muted">{t('embedBuilder.field.messageContent')}</label>
            <textarea
              value={content}
              onChange={(e) => onContentChange(e.target.value)}
              className={inputClass}
              rows={2}
            />
          </>
        )}
        <label className="text-sm text-muted">{t('embedBuilder.field.title')}</label>
        <input value={embed.title} onChange={(e) => updateEmbedField('title', e.target.value)} className={inputClass} />
        <label className="text-sm text-muted">{t('embedBuilder.field.description')}</label>
        <textarea
          value={embed.description}
          onChange={(e) => updateEmbedField('description', e.target.value)}
          className={inputClass}
          rows={4}
        />
        <label className="text-sm text-muted">{t('embedBuilder.field.color')}</label>
        <div className="flex gap-2">
          <input
            type="color"
            value={embed.color || '#5865F2'}
            onChange={(e) => updateEmbedField('color', e.target.value)}
            className="h-9 w-12 rounded-control border border-border bg-background"
          />
          <input
            value={embed.color}
            onChange={(e) => updateEmbedField('color', e.target.value)}
            placeholder="#5865F2"
            className={`flex-1 ${inputClass}`}
          />
        </div>
        <label className="text-sm text-muted">{t('embedBuilder.field.footer')}</label>
        <input
          value={embed.footer.text}
          onChange={(e) => updateEmbedField('footer', { ...embed.footer, text: e.target.value })}
          className={inputClass}
        />
        <label className="text-sm text-muted">{t('embedBuilder.field.imageUrl')}</label>
        <input
          value={embed.image.url}
          onChange={(e) => updateEmbedField('image', { url: e.target.value })}
          className={inputClass}
        />
        <label className="text-sm text-muted">{t('embedBuilder.field.thumbnailUrl')}</label>
        <input
          value={embed.thumbnail.url}
          onChange={(e) => updateEmbedField('thumbnail', { url: e.target.value })}
          className={inputClass}
        />
        <Toggle
          checked={embed.timestamp !== null}
          onChange={(v) => updateEmbedField('timestamp', v ? new Date().toISOString() : null)}
          label={t('embedBuilder.timestamp')}
        />
        {showFields && (
          <div className="flex flex-col gap-2">
            {embed.fields.map((field, index) => (
              <div key={index} className="flex flex-wrap items-center gap-2 rounded-control border border-border/60 p-2">
                <input
                  value={field.name}
                  onChange={(e) => updateField(index, { name: e.target.value })}
                  placeholder={t('embedBuilder.fieldNamePlaceholder')}
                  className={`min-w-0 flex-1 basis-full ${inputClass}`}
                />
                <textarea
                  value={field.value}
                  onChange={(e) => updateField(index, { value: e.target.value })}
                  placeholder={t('embedBuilder.fieldValuePlaceholder')}
                  className={`min-w-0 flex-1 basis-full ${inputClass}`}
                  rows={2}
                />
                <label className="flex items-center gap-1 text-xs text-muted">
                  <input
                    type="checkbox"
                    checked={field.inline}
                    onChange={(e) => updateField(index, { inline: e.target.checked })}
                  />
                  inline
                </label>
                <button type="button" onClick={() => removeField(index)} className="cursor-pointer text-muted hover:text-danger">
                  ×
                </button>
              </div>
            ))}
            <button type="button" onClick={addField} className="cursor-pointer self-start text-sm text-primary hover:text-primary-hover">
              {t('embedBuilder.addField')}
            </button>
          </div>
        )}
      </div>
      <div>
        <p className="mb-2 text-sm font-medium text-foreground">{t('messageCustomizer.preview')}</p>
        <EmbedPreview content={content} embed={embed} />
      </div>
    </div>
  )
}
