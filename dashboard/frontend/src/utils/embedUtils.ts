import type { EmbedSpec } from '../api/client'

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

/** Discord embed limits: https://discord.com/developers/docs/resources/channel#embed-object-embed-limits */
export function validateEmbedSpec(spec: EmbedSpec, content: string): string | null {
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
