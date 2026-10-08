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

/** Total characters Discord allows across every embed of one message. */
const TOTAL_TEXT_LIMIT = 6000

/** Per-embed Discord limits. Returns the i18n key of the first violation and the counted text length. */
function specLimitError(normalized: EmbedSpec): { error: string | null; length: number } {
  const fail = (error: string) => ({ error, length: 0 })
  if (normalized.title.length > 256) return fail('embedBuilder.error.validation.title')
  if (normalized.description.length > 4096) return fail('embedBuilder.error.validation.description')
  if (normalized.footer.text.length > 2048) return fail('embedBuilder.error.validation.footer')
  if (normalized.author.name.length > 256) return fail('embedBuilder.error.validation.author')
  if (normalized.fields.length > 25) return fail('embedBuilder.error.validation.fieldsCount')
  for (const field of normalized.fields) {
    if (field.name.length > 256) return fail('embedBuilder.error.validation.fieldName')
    if (field.value.length > 1024) return fail('embedBuilder.error.validation.fieldValue')
  }
  const length =
    normalized.title.length +
    normalized.description.length +
    normalized.footer.text.length +
    normalized.author.name.length +
    normalized.fields.reduce((sum, field) => sum + field.name.length + field.value.length, 0)
  return { error: null, length }
}

/** Discord embed limits: https://discord.com/developers/docs/resources/channel#embed-object-embed-limits */
export function validateEmbedSpec(spec: EmbedSpec | null | undefined, content: string): string | null {
  const normalized = normalizeEmbedSpec(spec)
  if (isEmbedSpecEmpty(normalized) && !content.trim()) {
    return 'embedBuilder.error.validation.empty'
  }
  const { error, length } = specLimitError(normalized)
  if (error) return error
  if (length > TOTAL_TEXT_LIMIT) return 'embedBuilder.error.validation.totalLength'
  return null
}

/** Validate all embeds of one message: empty slots are ignored, the 6000-char limit is shared. */
export function validateEmbedSpecs(specs: EmbedSpec[], content: string): string | null {
  const filled = specs.map((spec) => normalizeEmbedSpec(spec)).filter((spec) => !isEmbedSpecEmpty(spec))
  if (filled.length === 0 && !content.trim()) return 'embedBuilder.error.validation.empty'
  if (filled.length > MAX_EMBEDS) return 'embedBuilder.error.validation.embedsCount'
  let total = 0
  for (const spec of filled) {
    const { error, length } = specLimitError(spec)
    if (error) return error
    total += length
  }
  if (total > TOTAL_TEXT_LIMIT) return 'embedBuilder.error.validation.totalLength'
  return null
}

/**
 * Editor embeds from an API payload: `embeds`, or the single `embed` older records carry.
 * Never empty — the editor always has at least one (possibly blank) embed slot.
 */
export function embedsFromPayload(raw: { embeds?: unknown; embed?: unknown }): EmbedSpec[] {
  if (Array.isArray(raw.embeds) && raw.embeds.length > 0) {
    return raw.embeds.slice(0, MAX_EMBEDS).map((embed) => normalizeEmbedSpec(embed))
  }
  return [normalizeEmbedSpec(raw.embed ?? {})]
}
