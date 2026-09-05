import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { lookupFetch, type LookupConfig } from '../api/client'
import { CopyButton } from '../components/ui'
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
    <div className="space-y-6">
      <header className="max-w-3xl">
        <h1 className="text-3xl font-bold">{t('permissions.title')}</h1>
        <p className="mt-2 text-muted">{t('permissions.lead')}</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-4">
          {groups.map(([group, flags]) => (
            <section key={group} className="rounded-[14px] border border-border bg-surface/80 p-4">
              <div className="mb-3 flex items-center justify-between gap-2">
                <h2 className="font-semibold">{group}</h2>
                <button
                  type="button"
                  className="cursor-pointer text-xs text-primary-hover hover:underline"
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
                    <label key={flag.key} className="flex cursor-pointer items-center gap-2 text-sm">
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
            </section>
          ))}
          <button
            type="button"
            onClick={() => setMask(0n)}
            className="cursor-pointer rounded-[10px] border border-border px-3 py-2 text-sm hover:bg-surface-hover"
          >
            {t('permissions.clear')}
          </button>
        </div>

        <aside className="space-y-4 lg:sticky lg:top-20 lg:self-start">
          <section className="rounded-[14px] border border-border bg-surface p-4">
            <label className="block text-xs uppercase tracking-wide text-muted">{t('permissions.integer')}</label>
            <p className="mt-1 font-mono text-sm break-all">{mask.toString()}</p>
            <label className="mt-3 block text-xs uppercase tracking-wide text-muted">{t('permissions.hex')}</label>
            <p className="mt-1 font-mono text-sm">0x{mask.toString(16)}</p>
          </section>

          <section className="rounded-[14px] border border-border bg-surface p-4">
            <label className="text-xs uppercase tracking-wide text-muted" htmlFor="client-id">
              {t('permissions.clientId')}
            </label>
            <input
              id="client-id"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              className="mt-1 w-full rounded-[10px] border border-border bg-background px-3 py-2 outline-none focus:border-primary"
            />
            <p className="mt-1 text-xs text-muted">{t('permissions.clientId.hint')}</p>
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
          </section>

          <section className="rounded-[14px] border border-border bg-surface p-4">
            <label className="text-xs uppercase tracking-wide text-muted" htmlFor="scopes">
              {t('permissions.scopes')}
            </label>
            <input
              id="scopes"
              value={scopes}
              onChange={(e) => setScopes(e.target.value)}
              className="mt-1 w-full rounded-[10px] border border-border bg-background px-3 py-2 outline-none focus:border-primary"
            />
          </section>

          <section className="rounded-[14px] border border-border bg-surface p-4">
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-sm font-semibold">{t('permissions.inviteUrl')}</h2>
              <CopyButton value={inviteUrl} />
            </div>
            <p className="mt-2 break-all font-mono text-xs text-muted">{inviteUrl}</p>
          </section>

          <section className="rounded-[14px] border border-border bg-surface p-4">
            <h2 className="text-sm font-semibold">{t('permissions.preview')}</h2>
            <div className="mt-3 flex items-center gap-3 rounded-[12px] border border-border bg-background-deep px-3 py-3">
              <span className="h-4 w-4 rounded-full bg-primary" aria-hidden />
              <div>
                <p className="text-sm font-medium text-primary-hover">{t('permissions.preview.name')}</p>
                <p className="text-xs text-muted">{mask.toString()} bits</p>
              </div>
            </div>
          </section>
        </aside>
      </div>
    </div>
  )
}
