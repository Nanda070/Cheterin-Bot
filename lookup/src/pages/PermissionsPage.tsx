import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { lookupFetch, type LookupConfig } from '../api/client'
import { CopyButton, PageHeader, Panel, controlClass } from '../components/ui'
import { useT } from '../context/LanguageContext'
import { buildAuthorizeUrl, PERMISSION_FLAGS } from '../lib/permissions'

const DEFAULT_SCOPES = ['bot', 'applications.commands']

export function PermissionsPage() {
  const t = useT()
  const [params] = useSearchParams()
  const [mask, setMask] = useState<bigint>(() => {
    const raw = params.get('permissions')
    try {
      return raw ? BigInt(raw) : 0n
    } catch {
      return 0n
    }
  })
  const [clientId, setClientId] = useState(params.get('client_id') || '')
  const [scopes, setScopes] = useState(DEFAULT_SCOPES.join(' '))
  const [config, setConfig] = useState<LookupConfig | null>(null)

  useEffect(() => {
    void lookupFetch<LookupConfig>('/config').then(setConfig).catch(() => setConfig(null))
  }, [])

  const groups = useMemo(() => {
    const map = new Map<string, typeof PERMISSION_FLAGS>()
    for (const flag of PERMISSION_FLAGS) {
      const list = map.get(flag.group) ?? []
      list.push(flag)
      map.set(flag.group, list)
    }
    return [...map.entries()]
  }, [])

  const inviteUrl = buildAuthorizeUrl(
    clientId,
    mask,
    scopes
      .split(/[,\s]+/)
      .map((s) => s.trim())
      .filter(Boolean),
  )

  const toggle = (bit: bigint) => {
    setMask((prev) => ((prev & bit) === bit ? prev ^ bit : prev | bit))
  }

  return (
    <div className="space-y-7 lookup-rise">
      <PageHeader title={t('permissions.title')} lead={t('permissions.lead')} />

      <div className="grid gap-6 lg:grid-cols-[1.45fr_1fr]">
        <div className="space-y-3">
          {groups.map(([group, flags]) => (
            <Panel key={group} className="p-4 sm:p-5">
              <div className="mb-3 flex items-center justify-between gap-2">
                <h2 className="font-display font-semibold">{group}</h2>
                <button
                  type="button"
                  className="cursor-pointer text-xs font-medium text-primary-hover hover:underline"
                  onClick={() => {
                    const all = flags.reduce((acc, f) => acc | f.bit, 0n)
                    const selected = flags.every((f) => (mask & f.bit) === f.bit)
                    setMask((prev) => (selected ? prev & ~all : prev | all))
                  }}
                >
                  {t('permissions.selectAll')}
                </button>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                {flags.map((flag) => {
                  const checked = (mask & flag.bit) === flag.bit
                  return (
                    <label
                      key={flag.key}
                      className={`flex cursor-pointer items-center gap-2.5 rounded-[10px] border px-2.5 py-2 text-sm transition-colors ${
                        checked
                          ? 'border-primary/40 bg-primary-muted text-foreground'
                          : 'border-transparent hover:bg-surface-hover'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggle(flag.bit)}
                        className="accent-primary"
                      />
                      <span>{flag.key}</span>
                    </label>
                  )
                })}
              </div>
            </Panel>
          ))}
          <button
            type="button"
            onClick={() => setMask(0n)}
            className="cursor-pointer rounded-[10px] border border-border px-3 py-2 text-sm text-muted transition-colors hover:bg-surface-hover hover:text-foreground"
          >
            {t('permissions.clear')}
          </button>
        </div>

        <aside className="space-y-3 lg:sticky lg:top-24 lg:self-start">
          <Panel raised className="p-4">
            <p className="text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-muted">
              {t('permissions.integer')}
            </p>
            <p className="mt-1.5 break-all font-mono text-sm">{mask.toString()}</p>
            <p className="mt-3 text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-muted">
              {t('permissions.hex')}
            </p>
            <p className="mt-1.5 font-mono text-sm">0x{mask.toString(16)}</p>
          </Panel>

          <Panel raised className="p-4">
            <label className="text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-muted" htmlFor="client-id">
              {t('permissions.clientId')}
            </label>
            <input
              id="client-id"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              className={`mt-1.5 ${controlClass}`}
            />
            <p className="mt-1.5 text-xs text-muted">{t('permissions.clientId.hint')}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {config?.lookup_client_id ? (
                <button
                  type="button"
                  className="cursor-pointer rounded-full border border-border px-3 py-1 text-xs hover:bg-surface-hover"
                  onClick={() => setClientId(config.lookup_client_id)}
                >
                  {t('permissions.preset.lookup')}
                </button>
              ) : null}
              {config?.cheterin_client_id ? (
                <button
                  type="button"
                  className="cursor-pointer rounded-full border border-border px-3 py-1 text-xs hover:bg-surface-hover"
                  onClick={() => setClientId(config.cheterin_client_id)}
                >
                  {t('permissions.preset.cheterin')}
                </button>
              ) : null}
            </div>
          </Panel>

          <Panel raised className="p-4">
            <label className="text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-muted" htmlFor="scopes">
              {t('permissions.scopes')}
            </label>
            <input
              id="scopes"
              value={scopes}
              onChange={(e) => setScopes(e.target.value)}
              className={`mt-1.5 ${controlClass}`}
            />
          </Panel>

          <Panel raised className="p-4">
            <div className="mb-2 flex items-center justify-between gap-2">
              <h2 className="font-display text-sm font-semibold">{t('permissions.inviteUrl')}</h2>
              <CopyButton value={inviteUrl} />
            </div>
            <p className="break-all font-mono text-xs leading-relaxed text-muted">{inviteUrl}</p>
          </Panel>

          <Panel raised className="p-4">
            <h2 className="mb-3 font-display text-sm font-semibold">{t('permissions.preview')}</h2>
            <div className="flex items-center gap-3 rounded-[12px] border border-border bg-background-deep px-3 py-3.5">
              <span className="h-4 w-4 rounded-full bg-primary shadow-[0_0_0_3px_#a8283c33]" aria-hidden />
              <div>
                <p className="text-sm font-semibold text-primary-hover">{t('permissions.preview.name')}</p>
                <p className="text-xs text-muted">
                  {t('permissions.preview.bits', { count: mask.toString() })}
                </p>
              </div>
            </div>
          </Panel>
        </aside>
      </div>
    </div>
  )
}
