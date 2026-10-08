import type { EmbedFieldSpec, EmbedSpec } from '../api/client'
import { MAX_EMBEDS, isEmbedSpecEmpty } from './embedUtils'

/** A translatable message: `key` is an i18n key, `params` its interpolation values. */
export interface JsonNotice {
  key: string
  params?: Record<string, string | number>
}

/** One message read from pasted JSON. `name` is '' when the source carries no usable label. */
export interface ImportedMessage {
  name: string
  group: string
  content: string
  embeds: EmbedSpec[]
}

export type ParseResult =
  | { ok: true; messages: ImportedMessage[]; warnings: JsonNotice[] }
  | { ok: false; error: JsonNotice }

type Json = Record<string, unknown>

/** Webhook-only / unsupported message keys: the bot cannot honour them, so they are reported. */
const IGNORED_MESSAGE_KEYS = ['username', 'avatar_url', 'attachments', 'components', 'thread_name', 'flags']
/** Any of these on an object means "this is an embed", not a message or a wrapper. */
const EMBED_KEYS = ['title', 'description', 'fields', 'author', 'footer', 'image', 'thumbnail']

function isRecord(value: unknown): value is Json {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function asText(value: unknown): string {
  if (typeof value === 'string') return value
  if (typeof value === 'number' && Number.isFinite(value)) return String(value)
  return ''
}

function toColor(value: unknown): string {
  if (typeof value === 'number') {
    return Number.isInteger(value) && value >= 0 && value <= 0xffffff ? `#${value.toString(16).padStart(6, '0')}` : ''
  }
  if (typeof value === 'string' && /^#?[0-9a-f]{6}$/i.test(value.trim())) {
    return `#${value.trim().replace('#', '').toLowerCase()}`
  }
  return ''
}

function toEmbed(raw: Json): EmbedSpec {
  const author = isRecord(raw.author) ? raw.author : {}
  const footer = isRecord(raw.footer) ? raw.footer : {}
  const image = isRecord(raw.image) ? raw.image : {}
  const thumbnail = isRecord(raw.thumbnail) ? raw.thumbnail : {}
  const fields: EmbedFieldSpec[] = (Array.isArray(raw.fields) ? raw.fields : []).filter(isRecord).map((field) => ({
    name: asText(field.name),
    value: asText(field.value),
    inline: field.inline === true,
  }))
  return {
    title: asText(raw.title),
    description: asText(raw.description),
    url: asText(raw.url),
    color: toColor(raw.color),
    author: { name: asText(author.name), url: asText(author.url), icon_url: asText(author.icon_url) },
    footer: { text: asText(footer.text), icon_url: asText(footer.icon_url) },
    image: { url: asText(image.url) },
    thumbnail: { url: asText(thumbnail.url) },
    timestamp: typeof raw.timestamp === 'string' && raw.timestamp ? raw.timestamp : null,
    fields,
  }
}

function isBareEmbed(value: Json): boolean {
  return !Array.isArray(value.embeds) && !isRecord(value.embed) && EMBED_KEYS.some((key) => key in value)
}

function firstText(...values: unknown[]): string {
  for (const value of values) {
    const text = asText(value).trim()
    if (text) return text
  }
  return ''
}

interface Collector {
  ignoredKeys: string[]
  warnings: JsonNotice[]
}

function noteIgnoredKeys(source: Json, collector: Collector) {
  for (const key of IGNORED_MESSAGE_KEYS) {
    const value = source[key]
    const present = Array.isArray(value) ? value.length > 0 : Boolean(value)
    if (present && !collector.ignoredKeys.includes(key)) collector.ignoredKeys.push(key)
  }
}

/** Turn one JSON object into a message, or null when it is not a message, wrapper or embed. */
function toMessage(source: Json, collector: Collector): ImportedMessage | null {
  let rawEmbeds: unknown[]
  let content: unknown
  let labels: unknown[]

  if (Array.isArray(source.embeds)) {
    // Discohook / Discord message
    rawEmbeds = source.embeds
    content = source.content
    labels = [source.event, source.name]
  } else if (isRecord(source.embed)) {
    // Wrapper: { event, category, embed: { plainText, ... } }
    rawEmbeds = [source.embed]
    content = source.embed.plainText ?? source.plainText ?? source.content
    labels = [source.event, source.name, source.title]
  } else if (isBareEmbed(source)) {
    rawEmbeds = [source]
    content = source.plainText ?? source.content
    labels = [source.event, source.name]
  } else if ('content' in source) {
    rawEmbeds = []
    content = source.content
    labels = [source.event, source.name]
  } else {
    return null
  }

  let embeds = rawEmbeds.filter(isRecord).map(toEmbed).filter((embed) => !isEmbedSpecEmpty(embed))
  const text = asText(content)
  if (embeds.length === 0 && !text.trim()) return null

  const name = firstText(...labels, embeds[0]?.title, embeds[0]?.author.name)
  if (embeds.length > MAX_EMBEDS) {
    embeds = embeds.slice(0, MAX_EMBEDS)
    collector.warnings.push({ key: 'embedBuilder.json.warn.tooManyEmbeds', params: { name } })
  }
  noteIgnoredKeys(source, collector)
  return { name, group: asText(source.category).trim(), content: text, embeds }
}

function stripWrapping(text: string): string {
  const trimmed = text.replace(/^﻿/, '').trim()
  const fenced = /^```[a-z]*[ \t]*\r?\n([\s\S]*?)\r?\n?```$/i.exec(trimmed)
  return fenced ? fenced[1].trim() : trimmed
}

/**
 * Parse pasted JSON into messages. Accepts a Discohook message (`{content, embeds}`), a Discohook
 * backup (`{messages: [{data}]}`), a wrapper library (`[{event, embed: {plainText, ...}}]`), a bare
 * embed, or an array of any of these. An array of up to 10 bare embeds is one multi-embed message.
 */
export function parseMessageJson(text: string): ParseResult {
  let root: unknown
  try {
    root = JSON.parse(stripWrapping(text))
  } catch (err) {
    const detail = err instanceof Error ? err.message : String(err)
    return { ok: false, error: { key: 'embedBuilder.json.error.syntax', params: { detail } } }
  }
  if (root === null || typeof root !== 'object') {
    return { ok: false, error: { key: 'embedBuilder.json.error.shape' } }
  }

  const collector: Collector = { ignoredKeys: [], warnings: [] }
  const messages: ImportedMessage[] = []
  let skipped = 0

  const addEach = (items: unknown[]) => {
    for (const item of items) {
      const message = isRecord(item) ? toMessage(item, collector) : null
      if (message) messages.push(message)
      else skipped += 1
    }
  }

  if (Array.isArray(root)) {
    const oneMessage =
      root.length > 0 &&
      root.length <= MAX_EMBEDS &&
      root.every((item) => isRecord(item) && isBareEmbed(item) && !('plainText' in item) && !('content' in item))
    if (oneMessage) addEach([{ embeds: root }])
    else addEach(root)
  } else if (isRecord(root) && Array.isArray(root.messages)) {
    addEach(root.messages.map((entry) => (isRecord(entry) && isRecord(entry.data) ? entry.data : entry)))
  } else {
    addEach([root])
    skipped = 0
  }

  if (messages.length === 0) {
    return { ok: false, error: { key: 'embedBuilder.json.error.noMessages' } }
  }
  const warnings = [...collector.warnings]
  if (skipped > 0) warnings.push({ key: 'embedBuilder.json.warn.skippedItems', params: { count: skipped } })
  if (collector.ignoredKeys.length > 0) {
    warnings.push({ key: 'embedBuilder.json.warn.ignoredKeys', params: { keys: collector.ignoredKeys.join(', ') } })
  }
  return { ok: true, messages, warnings }
}

function exportEmbed(spec: EmbedSpec): Json {
  const out: Json = {}
  if (spec.title) out.title = spec.title
  if (spec.description) out.description = spec.description
  if (spec.url) out.url = spec.url
  const color = toColor(spec.color)
  if (color) out.color = parseInt(color.slice(1), 16)
  if (spec.fields.length > 0) {
    out.fields = spec.fields.map((field) => ({ name: field.name, value: field.value, inline: field.inline }))
  }
  if (spec.author.name) {
    out.author = {
      name: spec.author.name,
      ...(spec.author.url ? { url: spec.author.url } : {}),
      ...(spec.author.icon_url ? { icon_url: spec.author.icon_url } : {}),
    }
  }
  if (spec.footer.text) {
    out.footer = { text: spec.footer.text, ...(spec.footer.icon_url ? { icon_url: spec.footer.icon_url } : {}) }
  }
  if (spec.timestamp) out.timestamp = spec.timestamp
  if (spec.image.url) out.image = { url: spec.image.url }
  if (spec.thumbnail.url) out.thumbnail = { url: spec.thumbnail.url }
  return out
}

/** Serialise the current message the way Discohook does: numeric colours, no empty keys. */
export function exportMessageJson(content: string, embeds: EmbedSpec[]): string {
  const exported = embeds.filter((embed) => !isEmbedSpecEmpty(embed)).map(exportEmbed)
  return JSON.stringify(
    { content: content || null, embeds: exported.length > 0 ? exported : null, attachments: [] },
    null,
    2,
  )
}
