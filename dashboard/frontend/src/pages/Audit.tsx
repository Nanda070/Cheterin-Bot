import { ArrowClockwise, ClipboardText, DownloadSimple, MagnifyingGlass } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { fetchAudit, type AuditEntry, type AuditModerator, type AuditPage } from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { useLanguage, useT } from '../context/LanguageContext'

type TranslateFn = (key: string, params?: Record<string, string | number>) => string

/** Legacy Russian labels written before action keys were introduced. */
const LEGACY_ACTION_KEYS: Record<string, string> = {
  'Изменение конфигурации': 'audit.action.config',
  'Язык бота сервера': 'audit.action.language',
  'Настройки тикетов CTD': 'audit.action.ctd',
  'Включение антиспам-режима': 'audit.action.lockdown_on',
  'Выключение антиспам-режима': 'audit.action.lockdown_off',
  'Действие над участником (бан/кик/роль/варн)': 'audit.action.member',
  'Снятие роли с участника': 'audit.action.member_role_remove',
  'Массовая выдача ролей': 'audit.action.mass_assign',
  'Настройки приветствий': 'audit.action.welcome',
  'Настройки авто-ролей': 'audit.action.auto_roles',
  'Создание роли по реакции': 'audit.action.reaction_roles_create',
  'Изменение роли по реакции': 'audit.action.reaction_roles_update',
  'Удаление роли по реакции': 'audit.action.reaction_roles_delete',
  'Отправка/изменение эмбеда': 'audit.action.embed',
  'Действие с обратной связью': 'audit.action.feedback',
  'Изменение категории обратной связи': 'audit.action.feedback_update',
  'Удаление категории обратной связи': 'audit.action.feedback_delete',
  'Действие с событием': 'audit.action.events',
  'Удаление события': 'audit.action.events_delete',
  'Действие с турнирной сеткой': 'audit.action.brackets',
  'Удаление турнирной сетки': 'audit.action.brackets_delete',
  'Действие с поставкой': 'audit.action.supply',
  'Удаление приватной комнаты': 'audit.action.voice_room_delete',
  'Публикация панели комнат': 'audit.action.voice_panel',
  'Настройки ретрансляции': 'audit.action.news',
  'Настройки логирования': 'audit.action.serverlog',
  'Изменение XP участника': 'audit.action.xp_member',
  'Сброс XP участника': 'audit.action.xp_member_reset',
  'Полный сброс рейтинга': 'audit.action.xp_reset_all',
  'Загрузка фона карточки ранга': 'audit.action.xp_card_bg',
  'Удаление фона карточки ранга': 'audit.action.xp_card_bg_delete',
  'Настройки системы уровней': 'audit.action.xp_settings',
  'Действие с подпиской на стримы': 'audit.action.streams',
  'Изменение подписки на стримы': 'audit.action.streams_update',
  'Удаление подписки на стримы': 'audit.action.streams_delete',
  'Настройки модуля «Семья»': 'audit.action.family',
  'Решение по заявке в семью': 'audit.action.family_ticket',
  'Установка дня рождения': 'audit.action.family_birthday',
  'Удаление дня рождения': 'audit.action.family_birthday_delete',
  'Настройки модуля «Мафия»': 'audit.action.mafia',
  'Действие с розыгрышем': 'audit.action.giveaways',
  'Настройки ежедневной рубрики': 'audit.action.daily_topic',
  'Добавление темы дня': 'audit.action.daily_topic_add',
  'Изменение темы дня': 'audit.action.daily_topic_update',
  'Удаление темы дня': 'audit.action.daily_topic_delete',
  'Публикация темы дня вручную': 'audit.action.daily_topic_post',
  'Настройка фильтра автомодерации': 'audit.action.automod_filter',
  'Настройка срока ручных предупреждений': 'audit.action.automod_warn_duration',
  'Добавление порога эскалации варнов': 'audit.action.automod_escalation_add',
  'Изменение порога эскалации варнов': 'audit.action.automod_escalation_update',
  'Удаление порога эскалации варнов': 'audit.action.automod_escalation_delete',
  'Включение/выключение автомодерации': 'audit.action.automod',
  'Снятие предупреждения': 'audit.action.warn_remove',
}

/** Client-side map for legacy rows stored as "PUT /api/wordle". */
const PATH_ACTION_KEYS: [string, string][] = [
  ['/api/wordle', 'audit.action.wordle'],
  ['/api/fun', 'audit.action.fun'],
  ['/api/casino', 'audit.action.casino'],
  ['/api/economy/reset-all', 'audit.action.economy_reset_all'],
  ['/api/economy/balance', 'audit.action.economy_balance'],
  ['/api/economy', 'audit.action.economy'],
  ['/api/bunker', 'audit.action.bunker'],
  ['/api/mafia', 'audit.action.mafia'],
  ['/api/config', 'audit.action.config'],
  ['/api/language', 'audit.action.language'],
  ['/api/ctd', 'audit.action.ctd'],
  ['/api/spam-settings', 'audit.action.spam_settings'],
  ['/api/tempban-settings/publish-warning', 'audit.action.tempban_publish'],
  ['/api/tempban-settings', 'audit.action.tempban_settings'],
  ['/api/quote', 'audit.action.quote'],
  ['/api/antiraid', 'audit.action.antiraid'],
  ['/api/verification', 'audit.action.verification'],
  ['/api/welcome', 'audit.action.welcome'],
  ['/api/auto-roles', 'audit.action.auto_roles'],
  ['/api/reaction-roles', 'audit.action.reaction_roles_update'],
  ['/api/embed-', 'audit.action.embed'],
  ['/api/feedback', 'audit.action.feedback'],
  ['/api/events', 'audit.action.events'],
  ['/api/brackets', 'audit.action.brackets'],
  ['/api/supply', 'audit.action.supply'],
  ['/api/voice', 'audit.action.voice_settings'],
  ['/api/news', 'audit.action.news'],
  ['/api/serverlog', 'audit.action.serverlog'],
  ['/api/xp', 'audit.action.xp_settings'],
  ['/api/streams', 'audit.action.streams'],
  ['/api/family', 'audit.action.family'],
  ['/api/giveaways', 'audit.action.giveaways'],
  ['/api/daily-topic', 'audit.action.daily_topic'],
  ['/api/automod', 'audit.action.automod'],
  ['/api/warns', 'audit.action.warn_remove'],
  ['/api/members', 'audit.action.member'],
  ['/api/roles', 'audit.action.mass_assign'],
  ['/api/lockdown', 'audit.action.lockdown_on'],
]

const RAW_ACTION_RE = /^(GET|POST|PUT|PATCH|DELETE)\s+(\/api\/\S+)$/i

function keyFromRawAction(action: string): string | null {
  const match = action.trim().match(RAW_ACTION_RE)
  if (!match) return null
  const path = match[2]
  for (const [prefix, key] of PATH_ACTION_KEYS) {
    if (path.startsWith(prefix)) return key
  }
  return 'audit.action.other'
}

function resolveActionLabel(action: string, t: TranslateFn): string {
  const key =
    (action.startsWith('audit.action.') ? action : LEGACY_ACTION_KEYS[action]) ||
    keyFromRawAction(action) ||
    'audit.action.other'
  const label = t(key)
  return label === key ? t('audit.action.other') : label
}

function formatWhen(ts: number, locale: string): { relative: string; absolute: string } {
  const date = new Date(ts * 1000)
  const absolute = date.toLocaleString(locale)
  const diffSec = Math.round((Date.now() - date.getTime()) / 1000)
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' })
  let relative: string
  if (Math.abs(diffSec) < 60) relative = rtf.format(-diffSec, 'second')
  else if (Math.abs(diffSec) < 3600) relative = rtf.format(-Math.round(diffSec / 60), 'minute')
  else if (Math.abs(diffSec) < 86400) relative = rtf.format(-Math.round(diffSec / 3600), 'hour')
  else relative = rtf.format(-Math.round(diffSec / 86400), 'day')
  return { relative, absolute }
}

function EntryRow({ entry, t, locale }: { entry: AuditEntry; t: TranslateFn; locale: string }) {
  const [open, setOpen] = useState(false)
  const when = formatWhen(entry.ts, locale)
  const details = entry.details?.trim() ?? ''
  const hasMeta = Boolean(details)

  return (
    <div className="border-b border-border last:border-b-0">
      <button
        type="button"
        onClick={() => hasMeta && setOpen((v) => !v)}
        className={`flex w-full flex-wrap items-start gap-x-3 gap-y-2 px-4 py-3 text-left transition-colors ${
          hasMeta ? 'cursor-pointer hover:bg-surface-hover/60' : 'cursor-default'
        }`}
      >
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-foreground">{resolveActionLabel(entry.action, t)}</p>
          <p className="mt-0.5 text-xs text-muted">
            {entry.moderator_name}
            <span className="text-muted/60"> · </span>
            <span title={when.absolute}>{when.relative}</span>
          </p>
        </div>
        {hasMeta && (
          <span className="mt-1 text-xs text-muted">{open ? t('audit.hideDetails') : t('audit.showDetails')}</span>
        )}
      </button>
      {open && hasMeta && (
        <div className="space-y-1.5 border-t border-border/60 bg-background/40 px-4 py-3 text-xs text-muted">
          <p>
            <span className="text-muted/70">{t('audit.details')}: </span>
            <span className="text-foreground/90">{details}</span>
          </p>
          <p>
            <span className="text-muted/70">{t('audit.when')}: </span>
            {when.absolute}
          </p>
        </div>
      )}
    </div>
  )
}

function csvEscape(value: string): string {
  if (/[",\n\r]/.test(value)) return `"${value.replace(/"/g, '""')}"`
  return value
}

function downloadAuditCsv(entries: AuditEntry[], t: TranslateFn, locale: string) {
  const header = ['when', 'moderator', 'action', 'details']
  const lines = [
    header.join(','),
    ...entries.map((entry) => {
      const when = new Date(entry.ts * 1000).toLocaleString(locale)
      return [
        csvEscape(when),
        csvEscape(entry.moderator_name),
        csvEscape(resolveActionLabel(entry.action, t)),
        csvEscape(entry.details ?? ''),
      ].join(',')
    }),
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `audit-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

export function AuditPage() {
  const t = useT()
  const { lang } = useLanguage()
  const locale = lang === 'en' ? 'en-US' : 'ru-RU'
  const [page, setPage] = useState(1)
  const [moderator, setModerator] = useState('')
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [data, setData] = useState<AuditPage | null>(null)
  const [moderators, setModerators] = useState<AuditModerator[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query.trim()), 300)
    return () => clearTimeout(timer)
  }, [query])

  useEffect(() => {
    setPage(1)
  }, [debouncedQuery])

  useEffect(() => {
    let cancelled = false
    setBusy(true)
    setError('')
    fetchAudit(page, moderator || undefined, debouncedQuery || undefined)
      .then((result) => {
        if (cancelled) return
        setData(result)
        setModerators(result.moderators ?? [])
      })
      .catch((err) => {
        if (!cancelled) setError(formatApiError(err, t, 'audit.errorLoad'))
      })
      .finally(() => {
        if (!cancelled) setBusy(false)
      })
    return () => {
      cancelled = true
    }
  }, [page, moderator, debouncedQuery, t])

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1
  const entries = data?.entries ?? []

  const moderatorOptions = [
    { id: '', name: t('audit.filterAllModerators') },
    ...moderators.map((m) => ({ id: m.id, name: m.name })),
  ]

  const refresh = () => {
    setBusy(true)
    setError('')
    fetchAudit(page, moderator || undefined, debouncedQuery || undefined)
      .then((result) => {
        setData(result)
        setModerators(result.moderators ?? [])
      })
      .catch((err) => setError(formatApiError(err, t, 'audit.errorLoad')))
      .finally(() => setBusy(false))
  }

  const exportCsv = async () => {
    setExporting(true)
    setError('')
    try {
      const collected: AuditEntry[] = []
      let pageNum = 1
      let totalPagesToFetch = 1
      do {
        const result = await fetchAudit(pageNum, moderator || undefined, debouncedQuery || undefined)
        collected.push(...result.entries)
        totalPagesToFetch = Math.max(1, Math.ceil(result.total / result.page_size))
        pageNum += 1
      } while (pageNum <= totalPagesToFetch && pageNum <= 100)
      downloadAuditCsv(collected, t, locale)
    } catch (err) {
      setError(formatApiError(err, t, 'audit.errorExport'))
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="flex max-w-4xl flex-col gap-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <ClipboardText size={22} className="text-primary" />
            {t('audit.title')}
          </h1>
          <p className="mt-1 text-sm text-muted">{t('audit.intro', { total: data?.total ?? '…' })}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="ghost"
            disabled={busy || exporting || !data || data.total === 0}
            onClick={() => void exportCsv()}
            className="inline-flex items-center gap-1.5"
          >
            <DownloadSimple size={16} />
            {exporting ? t('audit.exporting') : t('audit.exportCsv')}
          </Button>
          <Button
            variant="ghost"
            disabled={busy}
            onClick={refresh}
            className="inline-flex items-center gap-1.5"
          >
            <ArrowClockwise size={16} className={busy ? 'animate-spin' : ''} />
            {t('audit.refresh')}
          </Button>
        </div>
      </div>

      <Card className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex min-w-0 flex-1 flex-col gap-1">
          <label className="text-xs text-muted" htmlFor="audit-search">
            {t('audit.search')}
          </label>
          <div className="relative">
            <MagnifyingGlass
              size={16}
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted"
            />
            <input
              id="audit-search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t('audit.searchPlaceholder')}
              className="w-full rounded-control border border-border bg-background py-2 pl-9 pr-3 text-sm text-foreground outline-none focus:border-primary"
            />
          </div>
        </div>
        <div className="flex w-full flex-col gap-1 sm:w-56">
          <label className="text-xs text-muted" htmlFor="audit-moderator">
            {t('audit.filterModerator')}
          </label>
          <Select
            id="audit-moderator"
            value={moderator}
            onChange={(id) => {
              setModerator(id)
              setPage(1)
            }}
            options={moderatorOptions}
            placeholder={t('audit.filterAllModerators')}
          />
        </div>
      </Card>

      {error && <p className="text-sm text-danger">{error}</p>}
      {!data && !error && <p className="text-sm text-muted">{t('common.loading')}</p>}

      {data && entries.length === 0 && (
        <Card>
          <p className="text-sm text-muted">
            {debouncedQuery ? t('audit.noMatches') : t('audit.empty')}
          </p>
        </Card>
      )}

      {entries.length > 0 && (
        <Card className="overflow-hidden p-0">
          {entries.map((entry, i) => (
            <EntryRow
              key={`${entry.ts}-${entry.moderator_id}-${entry.action}-${i}`}
              entry={entry}
              t={t}
              locale={locale}
            />
          ))}
        </Card>
      )}

      {data && totalPages > 1 && (
        <div className="flex items-center justify-center gap-3">
          <Button variant="ghost" disabled={page <= 1 || busy} onClick={() => setPage((p) => p - 1)}>
            {t('common.back')}
          </Button>
          <span className="text-sm text-muted">{t('audit.page', { page, total: totalPages })}</span>
          <Button
            variant="ghost"
            disabled={page >= totalPages || busy}
            onClick={() => setPage((p) => p + 1)}
          >
            {t('common.forward')}
          </Button>
        </div>
      )}
    </div>
  )
}
