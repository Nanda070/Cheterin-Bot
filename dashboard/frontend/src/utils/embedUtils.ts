import type { EmbedFieldSpec, EmbedSpec } from '../api/client'

/** Shared blank embed spec — consolidated from EmbedBuilder.tsx / EmbedEditor.tsx so every
 * embed surface (builder, welcome/DM, feedback panel, events) starts from the same shape. */
export const EMPTY_EMBED_SPEC: EmbedSpec = {
  title: '',
  description: '',
  url: '',
  color: '#D44556',
  author: { name: '', url: '', icon_url: '' },
  footer: { text: '', icon_url: '' },
  image: { url: '' },
  thumbnail: { url: '' },
  timestamp: null,
  fields: [],
}

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {}
}

function asString(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

/** Fill missing nested keys so inputs/preview never read `undefined.author.name` etc. */
export function normalizeEmbedSpec(raw: unknown): EmbedSpec {
  const src = asRecord(raw)
  const author = asRecord(src.author)
  const footer = asRecord(src.footer)
  const image = asRecord(src.image)
  const thumbnail = asRecord(src.thumbnail)
  const rawFields = Array.isArray(src.fields) ? src.fields : []
  const timestamp = src.timestamp
  const fields: EmbedFieldSpec[] = rawFields.map((field) => {
    const row = asRecord(field)
    return {
      name: asString(row.name),
      value: asString(row.value),
      inline: Boolean(row.inline),
    }
  })
  return {
    title: asString(src.title),
    description: asString(src.description),
    url: asString(src.url),
    color: typeof src.color === 'string' ? src.color : EMPTY_EMBED_SPEC.color,
    author: {
      name: asString(author.name),
      url: asString(author.url),
      icon_url: asString(author.icon_url),
    },
    footer: {
      text: asString(footer.text),
      icon_url: asString(footer.icon_url),
    },
    image: { url: asString(image.url) },
    thumbnail: { url: asString(thumbnail.url) },
    timestamp: typeof timestamp === 'string' && timestamp ? timestamp : null,
    fields,
  }
}

/** Discord allows at most 10 embeds in one message. */
export const MAX_EMBEDS = 10

/** Mirrors the backend's is_embed_spec_empty: such an embed is never sent. */
export function isEmbedSpecEmpty(spec: EmbedSpec): boolean {
  return !(spec.title || spec.description || spec.fields.length > 0 || spec.image.url || spec.thumbnail.url)
}

/** Discord embed limits: https://discord.com/developers/docs/resources/channel#embed-object-embed-limits */
export function validateEmbedSpec(spec: EmbedSpec | null | undefined, content: string): string | null {
  const normalized = normalizeEmbedSpec(spec)
  const hasEmbedContent = Boolean(
    normalized.title ||
      normalized.description ||
      normalized.fields.length > 0 ||
      normalized.image.url ||
      normalized.thumbnail.url,
  )
  if (!hasEmbedContent && !content.trim()) {
    return 'embedBuilder.error.validation.empty'
  }
  if (normalized.title.length > 256) return 'embedBuilder.error.validation.title'
  if (normalized.description.length > 4096) return 'embedBuilder.error.validation.description'
  if (normalized.footer.text.length > 2048) return 'embedBuilder.error.validation.footer'
  if (normalized.author.name.length > 256) return 'embedBuilder.error.validation.author'
  if (normalized.fields.length > 25) return 'embedBuilder.error.validation.fieldsCount'
  for (const field of normalized.fields) {
    if (field.name.length > 256) return 'embedBuilder.error.validation.fieldName'
    if (field.value.length > 1024) return 'embedBuilder.error.validation.fieldValue'
  }
  const totalLength =
    normalized.title.length +
    normalized.description.length +
    normalized.footer.text.length +
    normalized.author.name.length +
    normalized.fields.reduce((sum, field) => sum + field.name.length + field.value.length, 0)
  if (totalLength > 6000) return 'embedBuilder.error.validation.totalLength'
  return null
}
