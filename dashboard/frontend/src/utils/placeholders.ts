import type { EmbedSpec } from '../api/client'

/** `{Name}` — an identifier in braces. Discord mentions (`<@&id>`) and emoji (`<:n:id>`) never match. */
const PLACEHOLDER = /\{([A-Za-z_][A-Za-z0-9_]*)\}/g

/** Rebuild a message with `fn` applied to every user-visible string (colour and timestamp excluded). */
function mapText(content: string, embeds: EmbedSpec[], fn: (text: string) => string) {
  return {
    content: fn(content),
    embeds: embeds.map((embed) => ({
      ...embed,
      title: fn(embed.title),
      description: fn(embed.description),
      url: fn(embed.url),
      author: { name: fn(embed.author.name), url: fn(embed.author.url), icon_url: fn(embed.author.icon_url) },
      footer: { text: fn(embed.footer.text), icon_url: fn(embed.footer.icon_url) },
      image: { url: fn(embed.image.url) },
      thumbnail: { url: fn(embed.thumbnail.url) },
      fields: embed.fields.map((field) => ({ ...field, name: fn(field.name), value: fn(field.value) })),
    })),
  }
}

/** Unique placeholder names used anywhere in the message, in order of first appearance. */
export function findPlaceholders(content: string, embeds: EmbedSpec[]): string[] {
  const names: string[] = []
  mapText(content, embeds, (text) => {
    for (const match of text.matchAll(PLACEHOLDER)) {
      if (!names.includes(match[1])) names.push(match[1])
    }
    return text
  })
  return names
}

/**
 * Fill placeholders in one pass: a substituted value is not scanned again, and a name with an
 * empty or missing value stays as `{Name}`. Returns new objects; the input is not modified.
 */
export function applyPlaceholders(
  content: string,
  embeds: EmbedSpec[],
  values: Record<string, string>,
): { content: string; embeds: EmbedSpec[] } {
  return mapText(content, embeds, (text) =>
    text.replace(PLACEHOLDER, (whole, name: string) => (Object.hasOwn(values, name) && values[name] ? values[name] : whole)),
  )
}
