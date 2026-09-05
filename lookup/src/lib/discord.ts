export const SNOWFLAKE_RE = /^\d{17,20}$/
export const DISCORD_EPOCH_MS = 1_420_070_400_000n

export function isSnowflake(value: string): boolean {
  return SNOWFLAKE_RE.test(value.trim())
}

export function normalizeInviteCode(raw: string): string | null {
  const trimmed = raw.trim()
  if (!trimmed) return null
  if (SNOWFLAKE_RE.test(trimmed)) return null

  try {
    if (trimmed.includes('://') || trimmed.startsWith('discord.') || trimmed.startsWith('www.')) {
      const url = new URL(trimmed.startsWith('http') ? trimmed : `https://${trimmed}`)
      const host = url.hostname.replace(/^www\./, '')
      if (host === 'discord.gg') {
        const code = url.pathname.split('/').filter(Boolean)[0]
        return code && !SNOWFLAKE_RE.test(code) ? code : null
      }
      if (host === 'discord.com' || host === 'discordapp.com') {
        const parts = url.pathname.split('/').filter(Boolean)
        const inviteIdx = parts.findIndex((p) => p === 'invite')
        if (inviteIdx >= 0 && parts[inviteIdx + 1]) {
          const code = parts[inviteIdx + 1]
          return !SNOWFLAKE_RE.test(code) ? code : null
        }
      }
    }
  } catch {
    /* fall through */
  }

  const bare = trimmed.replace(/^\/+/, '').split(/[/?#]/)[0] ?? ''
  if (!bare || SNOWFLAKE_RE.test(bare) || bare.includes(' ')) return null
  if (!/^[A-Za-z0-9-]+$/.test(bare)) return null
  return bare
}

export function decodeSnowflake(id: string): {
  timestampMs: number
  createdAt: Date
  workerId: number
  processId: number
  increment: number
} | null {
  if (!isSnowflake(id)) return null
  const snowflake = BigInt(id)
  const timestampMs = Number((snowflake >> 22n) + DISCORD_EPOCH_MS)
  const workerId = Number((snowflake >> 17n) & 0x1fn)
  const processId = Number((snowflake >> 12n) & 0x1fn)
  const increment = Number(snowflake & 0xfffn)
  return {
    timestampMs,
    createdAt: new Date(timestampMs),
    workerId,
    processId,
    increment,
  }
}

export function cdnAvatarUrl(userId: string, hash: string | null | undefined, size = 256, format?: string): string {
  if (!hash) {
    const index = Number((BigInt(userId) >> 22n) % 6n)
    return `https://cdn.discordapp.com/embed/avatars/${index}.png`
  }
  const ext = format ?? (hash.startsWith('a_') ? 'gif' : 'png')
  return `https://cdn.discordapp.com/avatars/${userId}/${hash}.${ext}?size=${size}`
}

export function cdnBannerUrl(userId: string, hash: string, size = 512, format?: string): string {
  const ext = format ?? (hash.startsWith('a_') ? 'gif' : 'png')
  return `https://cdn.discordapp.com/banners/${userId}/${hash}.${ext}?size=${size}`
}

export function cdnGuildIconUrl(guildId: string, hash: string, size = 256, format?: string): string {
  const ext = format ?? (hash.startsWith('a_') ? 'gif' : 'png')
  return `https://cdn.discordapp.com/icons/${guildId}/${hash}.${ext}?size=${size}`
}

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}
