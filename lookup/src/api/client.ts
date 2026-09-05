export class LookupApiError extends Error {
  status: number
  retryAfter?: number
  code?: string

  constructor(status: number, message: string, opts?: { retryAfter?: number; code?: string }) {
    super(message)
    this.status = status
    this.retryAfter = opts?.retryAfter
    this.code = opts?.code
  }
}

async function parseError(res: Response): Promise<LookupApiError> {
  let message = res.statusText || 'error'
  let code: string | undefined
  let retryAfter: number | undefined
  const headerRetry = res.headers.get('Retry-After')
  if (headerRetry) retryAfter = Number(headerRetry)
  try {
    const body = (await res.json()) as { error?: string; code?: string; retry_after?: number }
    if (body.error) message = body.error
    if (body.code) code = body.code
    if (typeof body.retry_after === 'number') retryAfter = body.retry_after
  } catch {
    /* ignore */
  }
  return new LookupApiError(res.status, message, { retryAfter, code })
}

export async function lookupFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api/lookup${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init?.headers ?? {}),
    },
  })
  if (!res.ok) throw await parseError(res)
  return (await res.json()) as T
}

export type LookupUser = {
  id: string
  username: string
  global_name: string | null
  discriminator: string
  avatar: string | null
  banner: string | null
  accent_color: number | null
  bot: boolean
  system: boolean
  public_flags: number
  avatar_decoration_data?: { asset: string; sku_id: string } | null
  collectibles?: { nameplate?: unknown } | null
  created_at: string
  avatar_url: string
  banner_url: string | null
}

export type LookupBot = {
  user: LookupUser
  application: {
    id: string
    name: string
    description: string | null
    icon: string | null
    bot_public: boolean | null
    bot_require_code_grant: boolean | null
    verify_key: string | null
    flags: number | null
    tags: string[]
    install_params: {
      scopes: string[]
      permissions: string
    } | null
    approximate_guild_count: number | null
  } | null
  scopes: string[]
  permissions: string | null
  permissions_names: string[]
  intents: string[]
  degraded: boolean
}

export type LookupServer = {
  code: string
  expires_at: string | null
  approximate_member_count: number | null
  approximate_presence_count: number | null
  inviter: { id: string; username: string; global_name: string | null; avatar: string | null } | null
  channel: { id: string; name: string; type: number } | null
  guild: {
    id: string
    name: string
    description: string | null
    icon: string | null
    splash: string | null
    banner: string | null
    features: string[]
    verification_level: number | null
    nsfw_level: number | null
    premium_subscription_count: number | null
    icon_url: string | null
    splash_url: string | null
    banner_url: string | null
  }
}

export type LookupConfig = {
  lookup_client_id: string
  cheterin_client_id: string
  captcha_enabled: boolean
  rate_limit_per_minute: number
}

export type PluginEntry = {
  id: string
  name: string
  description: string
  description_ru?: string
  url: string
  tags?: string[]
}
