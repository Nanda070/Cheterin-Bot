import { ApiError } from './client'

type Translate = (key: string, params?: Record<string, string | number>) => string

/** Known API `error` codes → i18n keys (shown instead of the opaque generic save failure). */
const API_ERROR_KEYS: Record<string, string> = {
  invalid_request: 'apiError.invalid_request',
  empty_embed: 'apiError.empty_embed',
  title_too_long: 'apiError.title_too_long',
  description_too_long: 'apiError.description_too_long',
  footer_too_long: 'apiError.footer_too_long',
  author_name_too_long: 'apiError.author_name_too_long',
  too_many_fields: 'apiError.too_many_fields',
  field_name_too_long: 'apiError.field_name_too_long',
  field_value_too_long: 'apiError.field_value_too_long',
  embed_too_large: 'apiError.embed_too_large',
  too_many_embeds: 'apiError.too_many_embeds',
  v2_too_large: 'apiError.v2_too_large',
  invalid_channel_mode: 'apiError.invalid_channel_mode',
  goodbye_channel_id_not_found: 'apiError.goodbye_channel_not_found',
  channel_not_found: 'apiError.channel_not_found',
  role_not_found: 'apiError.role_not_found',
  role_not_assignable: 'apiError.role_not_assignable',
  not_found: 'apiError.not_found',
  service_unavailable: 'apiError.service_unavailable',
  discord_error: 'apiError.discord_error',
  forbidden: 'apiError.forbidden',
  unauthorized: 'apiError.unauthorized',
  duplicate_emoji: 'apiError.duplicate_emoji',
  message_not_found: 'apiError.message_not_found',
  channel_required: 'apiError.channel_required',
  bot_not_in_guild: 'apiError.bot_not_in_guild',
  no_guild_selected: 'apiError.no_guild_selected',
  invalid_language: 'apiError.invalid_language',
  upload_failed: 'apiError.upload_failed',
  invalid_size: 'apiError.invalid_size',
  invalid_format: 'apiError.invalid_format',
  invalid_poll_interval: 'apiError.invalid_poll_interval',
  invalid_enabled: 'apiError.invalid_enabled',
  invalid_channel: 'apiError.invalid_channel',
  module_disabled: 'apiError.module_disabled',
  not_configured: 'apiError.not_configured',
  channel_not_messageable: 'apiError.channel_not_messageable',
  forbidden_by_discord: 'apiError.forbidden_by_discord',
  publish_failed: 'apiError.publish_failed',
}

/**
 * Prefer a human-readable API error; fall back to the page-specific save message.
 * Backend returns `{ "error": "code_or_message" }` which ApiError surfaces as `.message`.
 */
export function formatApiError(err: unknown, t: Translate, fallbackKey: string): string {
  if (!(err instanceof ApiError)) {
    return t(fallbackKey)
  }

  const code = (err.message || '').trim()
  if (!code || code.startsWith('HTTP ')) {
    return t(fallbackKey)
  }

  const mapped = API_ERROR_KEYS[code]
  if (mapped) {
    const detail = t(mapped)
    // If translation missing, i18n returns the key — still show the code.
    if (detail === mapped) {
      return `${t(fallbackKey)} (${code})`
    }
    return detail
  }

  // Unknown machine code: keep the generic line and append the code for support/debug.
  return `${t(fallbackKey)} (${code})`
}

export function isForbiddenError(err: unknown): boolean {
  return err instanceof ApiError && (err.status === 403 || err.message === 'forbidden')
}
