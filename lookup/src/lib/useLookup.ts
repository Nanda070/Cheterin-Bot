/**
 * Shared lookup error-message hook.
 * Converts LookupApiError instances to localised strings.
 */

import { LookupApiError } from '../api/client'
import { useT } from '../context/LanguageContext'

export function useLookupErrorMessage(err: unknown): string {
  const t = useT()
  if (!(err instanceof LookupApiError)) return t('error.network')
  if (err.code === 'captcha_required') return t('common.captchaRequired')
  if (err.status === 429) return t('common.rateLimited', { seconds: String(err.retryAfter ?? 60) })
  if (err.status === 404) return t('error.404')
  if (err.status === 400) return t('error.400')
  if (err.status === 503) return t('error.503')
  if (err.status >= 500) return t('error.502')
  return err.message || t('common.error')
}
