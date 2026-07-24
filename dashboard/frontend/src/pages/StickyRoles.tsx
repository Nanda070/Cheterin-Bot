import { ArrowCounterClockwise } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  fetchRoles,
  fetchStickyRoles,
  updateStickyRoles,
  type RoleInfo,
  type StickyRolesSettings,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Checkbox } from '../components/ui/Checkbox'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

export function StickyRolesPage({ embedded = false }: { embedded?: boolean }) {
  const t = useT()
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [settings, setSettings] = useState<StickyRolesSettings | null>(null)
  const [enabled, setEnabled] = useState(false)
  const [tracked, setTracked] = useState<string[]>([])
  const [ignored, setIgnored] = useState<string[]>([])
  const [error, setError] = useState('')
  const [savedMessage, setSavedMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([fetchRoles(), fetchStickyRoles()])
      .then(([roleList, sticky]) => {
        setRoles(roleList.filter((r) => r.id !== '0'))
        setSettings(sticky)
        setEnabled(sticky.enabled)
        setTracked(sticky.tracked_role_ids)
        setIgnored(sticky.ignored_role_ids)
      })
      .catch((err) => setError(formatApiError(err, t, 'stickyRoles.errorLoad')))
      .finally(() => setLoading(false))
  }, [t])

  const toggleList = (list: string[], id: string, setter: (v: string[]) => void) => {
    setter(list.includes(id) ? list.filter((x) => x !== id) : [...list, id])
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSavedMessage('')
    try {
      const updated = await updateStickyRoles({
        enabled,
        tracked_role_ids: tracked,
        ignored_role_ids: ignored,
      })
      setSettings(updated)
      setEnabled(updated.enabled)
      setTracked(updated.tracked_role_ids)
      setIgnored(updated.ignored_role_ids)
      setSavedMessage(t('common.saved'))
    } catch (err) {
      setError(formatApiError(err, t, 'stickyRoles.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  if (loading || !settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  return (
    <div className="flex max-w-xl flex-col gap-4">
      {!embedded && (
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <ArrowCounterClockwise size={22} className="text-primary" />
          {t('stickyRoles.title')}
        </h1>
      )}
      {embedded && (
        <h2 className="flex items-center gap-2 font-semibold text-foreground">
          <ArrowCounterClockwise size={20} className="text-primary" />
          {t('stickyRoles.title')}
        </h2>
      )}

      <p className="text-sm text-muted">{t('stickyRoles.intro')}</p>

      {error && <p className="text-sm text-danger">{error}</p>}
      {savedMessage && <p className="text-sm text-success">{savedMessage}</p>}

      <Card className="flex flex-col gap-3">
        <Toggle checked={enabled} onChange={setEnabled} label={t('stickyRoles.enable')} disabled={busy} />
        <p className="text-xs text-muted">{t('stickyRoles.trackedHint')}</p>
        <div className="flex flex-wrap gap-3">
          {roles.map((r) => (
            <Checkbox
              key={`tracked-${r.id}`}
              checked={tracked.includes(r.id)}
              onChange={() => toggleList(tracked, r.id, setTracked)}
              label={r.name}
            />
          ))}
        </div>
        {roles.length === 0 && <p className="text-sm text-muted">{t('stickyRoles.noRoles')}</p>}
      </Card>

      <Card className="flex flex-col gap-3">
        <p className="text-sm font-medium text-foreground">{t('stickyRoles.ignored')}</p>
        <p className="text-xs text-muted">{t('stickyRoles.ignoredHint')}</p>
        <div className="flex flex-wrap gap-3">
          {roles.map((r) => (
            <Checkbox
              key={`ignored-${r.id}`}
              checked={ignored.includes(r.id)}
              onChange={() => toggleList(ignored, r.id, setIgnored)}
              label={r.name}
            />
          ))}
        </div>
      </Card>

      <div>
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? t('common.saving') : t('common.save')}
        </Button>
      </div>
    </div>
  )
}
