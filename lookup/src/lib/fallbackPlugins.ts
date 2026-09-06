import type { PluginEntry } from '../api/client'

/** Always-available Lookup tool cards when `/plugins` API is empty or down. */
export const FALLBACK_LOOKUP_PLUGINS: PluginEntry[] = [
  {
    id: 'lookup-snowflake',
    name: 'ID Resolver',
    description: 'Decode a Discord snowflake into creation time and components.',
    description_ru: 'Разбор Discord snowflake: время создания и компоненты.',
    url: '/lookup/plugins/snowflake',
    tags: ['lookup', 'tools'],
  },
  {
    id: 'lookup-timestamp',
    name: 'Timestamp Generator',
    description: 'Build Discord relative and absolute timestamp markdown from a date or snowflake.',
    description_ru: 'Генерация Discord timestamp (относительных и абсолютных) из даты или snowflake.',
    url: '/lookup/plugins/timestamp',
    tags: ['lookup', 'tools'],
  },
  {
    id: 'lookup-permissions',
    name: 'Permissions Calculator',
    description: 'Compose a permission bitfield and OAuth2 bot invite URL.',
    description_ru: 'Сборка битмаски прав и OAuth2-ссылки приглашения бота.',
    url: '/lookup/plugins/permissions',
    tags: ['lookup', 'tools'],
  },
  {
    id: 'lookup-avatars',
    name: 'Avatar & Banner Downloader',
    description: 'Preview and download Discord CDN avatars or banners by user ID and hash.',
    description_ru: 'Превью и скачивание аватаров/баннеров Discord CDN по ID и hash.',
    url: '/lookup/plugins/avatars',
    tags: ['lookup', 'tools'],
  },
  {
    id: 'lookup-badges',
    name: 'Badge List',
    description: 'Full Discord badge reference with icons — flags, Nitro, boosts, and more.',
    description_ru: 'Полный справочник бейджей Discord с иконками — флаги, Nitro, бусты и др.',
    url: '/lookup/plugins/badges',
    tags: ['lookup', 'tools'],
  },
]

export function mergePluginCatalog(remote: PluginEntry[] | null | undefined): PluginEntry[] {
  const list = Array.isArray(remote) ? remote : []
  // DSA is a home mode only — never list a standalone Lookup DSA tool card.
  const filtered = list.filter((p) => p.id !== 'lookup-dsa')

  const remoteLookup = filtered.filter((p) => (p.tags ?? []).includes('lookup'))
  const remoteOther = filtered.filter((p) => !(p.tags ?? []).includes('lookup'))

  const lookupBase = remoteLookup.length > 0 ? remoteLookup : FALLBACK_LOOKUP_PLUGINS
  const byId = new Map<string, PluginEntry>()

  for (const p of lookupBase) {
    const fb = FALLBACK_LOOKUP_PLUGINS.find((f) => f.id === p.id)
    byId.set(p.id, fb ? { ...p, url: fb.url } : p)
  }
  for (const fb of FALLBACK_LOOKUP_PLUGINS) {
    if (!byId.has(fb.id)) byId.set(fb.id, fb)
  }
  for (const p of remoteOther) {
    byId.set(p.id, p)
  }

  return [...byId.values()]
}
