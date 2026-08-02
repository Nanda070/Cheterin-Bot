import type { useT } from '../context/LanguageContext'

type T = ReturnType<typeof useT>

interface DurationParts {
  weeks: number
  days: number
  hours: number
  minutes: number
}

function durationParts(totalSeconds: number): DurationParts {
  const totalMinutes = Math.floor(Math.max(0, totalSeconds) / 60)
  const weeks = Math.floor(totalMinutes / (7 * 24 * 60))
  let rem = totalMinutes % (7 * 24 * 60)
  const days = Math.floor(rem / (24 * 60))
  rem %= 24 * 60
  const hours = Math.floor(rem / 60)
  const minutes = rem % 60
  return { weeks, days, hours, minutes }
}

/**
 * Human-readable duration ("1 wk 2 d 3 h") using the shared `common.duration.*` i18n keys.
 * Takes raw seconds — prefer this over server-formatted `*_time_text` fields so the
 * dashboard UI language always matches, regardless of the guild's bot language.
 */
export function formatDuration(totalSeconds: number, t: T): string {
  const { weeks, days, hours, minutes } = durationParts(totalSeconds)
  const parts: string[] = []
  if (weeks) parts.push(t('common.duration.weeks', { n: weeks }))
  if (days) parts.push(t('common.duration.days', { n: days }))
  if (hours) parts.push(t('common.duration.hours', { n: hours }))
  if (minutes || parts.length === 0) parts.push(t('common.duration.minutes', { n: minutes }))
  return parts.join(' ')
}

/** Same as `formatDuration`, but the input is minutes (e.g. reward thresholds, escalation rules). */
export function formatDurationMinutes(totalMinutes: number, t: T): string {
  return formatDuration(totalMinutes * 60, t)
}

/** AutoMod-style duration where 0 minutes represents a permanent action. */
export function formatDurationOrPermanent(totalMinutes: number, t: T): string {
  if (totalMinutes <= 0) return t('common.duration.permanent')
  return formatDurationMinutes(totalMinutes, t)
}
