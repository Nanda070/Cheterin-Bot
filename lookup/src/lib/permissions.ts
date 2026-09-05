export type PermissionFlag = {
  key: string
  bit: bigint
  group: string
}

export const PERMISSION_FLAGS: PermissionFlag[] = [
  { key: 'Create Instant Invite', bit: 1n << 0n, group: 'General' },
  { key: 'Kick Members', bit: 1n << 1n, group: 'Moderation' },
  { key: 'Ban Members', bit: 1n << 2n, group: 'Moderation' },
  { key: 'Administrator', bit: 1n << 3n, group: 'General' },
  { key: 'Manage Channels', bit: 1n << 4n, group: 'General' },
  { key: 'Manage Guild', bit: 1n << 5n, group: 'General' },
  { key: 'Add Reactions', bit: 1n << 6n, group: 'Text' },
  { key: 'View Audit Log', bit: 1n << 7n, group: 'General' },
  { key: 'Priority Speaker', bit: 1n << 8n, group: 'Voice' },
  { key: 'Stream', bit: 1n << 9n, group: 'Voice' },
  { key: 'View Channel', bit: 1n << 10n, group: 'General' },
  { key: 'Send Messages', bit: 1n << 11n, group: 'Text' },
  { key: 'Send TTS Messages', bit: 1n << 12n, group: 'Text' },
  { key: 'Manage Messages', bit: 1n << 13n, group: 'Text' },
  { key: 'Embed Links', bit: 1n << 14n, group: 'Text' },
  { key: 'Attach Files', bit: 1n << 15n, group: 'Text' },
  { key: 'Read Message History', bit: 1n << 16n, group: 'Text' },
  { key: 'Mention Everyone', bit: 1n << 17n, group: 'Text' },
  { key: 'Use External Emojis', bit: 1n << 18n, group: 'Text' },
  { key: 'View Guild Insights', bit: 1n << 19n, group: 'General' },
  { key: 'Connect', bit: 1n << 20n, group: 'Voice' },
  { key: 'Speak', bit: 1n << 21n, group: 'Voice' },
  { key: 'Mute Members', bit: 1n << 22n, group: 'Voice' },
  { key: 'Deafen Members', bit: 1n << 23n, group: 'Voice' },
  { key: 'Move Members', bit: 1n << 24n, group: 'Voice' },
  { key: 'Use VAD', bit: 1n << 25n, group: 'Voice' },
  { key: 'Change Nickname', bit: 1n << 26n, group: 'General' },
  { key: 'Manage Nicknames', bit: 1n << 27n, group: 'General' },
  { key: 'Manage Roles', bit: 1n << 28n, group: 'General' },
  { key: 'Manage Webhooks', bit: 1n << 29n, group: 'General' },
  { key: 'Manage Expressions', bit: 1n << 30n, group: 'General' },
  { key: 'Use Application Commands', bit: 1n << 31n, group: 'Text' },
  { key: 'Request to Speak', bit: 1n << 32n, group: 'Voice' },
  { key: 'Manage Events', bit: 1n << 33n, group: 'General' },
  { key: 'Manage Threads', bit: 1n << 34n, group: 'Text' },
  { key: 'Create Public Threads', bit: 1n << 35n, group: 'Text' },
  { key: 'Create Private Threads', bit: 1n << 36n, group: 'Text' },
  { key: 'Use External Stickers', bit: 1n << 37n, group: 'Text' },
  { key: 'Send Messages in Threads', bit: 1n << 38n, group: 'Text' },
  { key: 'Use Embedded Activities', bit: 1n << 39n, group: 'Voice' },
  { key: 'Moderate Members', bit: 1n << 40n, group: 'Moderation' },
  { key: 'View Creator Monetization Analytics', bit: 1n << 41n, group: 'General' },
  { key: 'Use Soundboard', bit: 1n << 42n, group: 'Voice' },
  { key: 'Create Expressions', bit: 1n << 43n, group: 'General' },
  { key: 'Create Events', bit: 1n << 44n, group: 'General' },
  { key: 'Use External Sounds', bit: 1n << 45n, group: 'Voice' },
  { key: 'Send Voice Messages', bit: 1n << 46n, group: 'Text' },
  { key: 'Send Polls', bit: 1n << 49n, group: 'Text' },
  { key: 'Use External Apps', bit: 1n << 50n, group: 'Text' },
]

export function permissionNames(mask: bigint | number | string): string[] {
  const value = typeof mask === 'bigint' ? mask : BigInt(mask || 0)
  return PERMISSION_FLAGS.filter((f) => (value & f.bit) === f.bit).map((f) => f.key)
}

export function buildAuthorizeUrl(clientId: string, permissions: bigint, scopes: string[]): string {
  const params = new URLSearchParams({
    client_id: clientId || 'APPLICATION_ID',
    permissions: permissions.toString(),
    scope: scopes.join(' '),
  })
  return `https://discord.com/oauth2/authorize?${params.toString()}`
}

export type BadgeDef = {
  key: string
  bit: number
  nameEn: string
  nameRu: string
}

/** Public UserFlags commonly shown by lookup UIs. */
export const BADGE_CATALOG: BadgeDef[] = [
  { key: 'staff', bit: 1 << 0, nameEn: 'Discord Employee', nameRu: 'Сотрудник Discord' },
  { key: 'partner', bit: 1 << 1, nameEn: 'Partnered Server Owner', nameRu: 'Владелец партнёрского сервера' },
  { key: 'hypesquad', bit: 1 << 2, nameEn: 'HypeSquad Events', nameRu: 'HypeSquad Events' },
  { key: 'bug1', bit: 1 << 3, nameEn: 'Bug Hunter Level 1', nameRu: 'Bug Hunter Level 1' },
  { key: 'hype_bravery', bit: 1 << 6, nameEn: 'HypeSquad Bravery', nameRu: 'HypeSquad Bravery' },
  { key: 'hype_brilliance', bit: 1 << 7, nameEn: 'HypeSquad Brilliance', nameRu: 'HypeSquad Brilliance' },
  { key: 'hype_balance', bit: 1 << 8, nameEn: 'HypeSquad Balance', nameRu: 'HypeSquad Balance' },
  { key: 'premium_early', bit: 1 << 9, nameEn: 'Early Supporter', nameRu: 'Early Supporter' },
  { key: 'team', bit: 1 << 10, nameEn: 'Team User', nameRu: 'Team User' },
  { key: 'bug2', bit: 1 << 14, nameEn: 'Bug Hunter Level 2', nameRu: 'Bug Hunter Level 2' },
  { key: 'verified_bot', bit: 1 << 16, nameEn: 'Verified Bot', nameRu: 'Verified Bot' },
  { key: 'verified_dev', bit: 1 << 17, nameEn: 'Early Verified Bot Developer', nameRu: 'Early Verified Bot Developer' },
  { key: 'mod_alumni', bit: 1 << 18, nameEn: 'Moderator Programs Alumni', nameRu: 'Moderator Programs Alumni' },
  { key: 'active_dev', bit: 1 << 22, nameEn: 'Active Developer', nameRu: 'Active Developer' },
]

export function badgesFromFlags(flags: number | null | undefined): BadgeDef[] {
  const value = flags ?? 0
  return BADGE_CATALOG.filter((b) => (value & b.bit) === b.bit)
}
