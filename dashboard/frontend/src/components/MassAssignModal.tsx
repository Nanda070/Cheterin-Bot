import { useEffect, useState } from 'react'
import {
  fetchMassAssignStatus,
  fetchMembers,
  fetchRoles,
  startMassAssign,
  type MassAssignStatus,
  type MassAssignTarget,
  type MemberSummary,
  type RoleInfo,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { useT } from '../context/LanguageContext'
import { Button } from './ui/Button'
import { Checkbox } from './ui/Checkbox'
import { Modal } from './ui/Modal'
import { Select } from './ui/Select'

interface Props {
  open: boolean
  onClose: () => void
}

export function MassAssignModal({ open, onClose }: Props) {
  const t = useT()
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [roleId, setRoleId] = useState('')
  const [target, setTarget] = useState<MassAssignTarget>('all_except_bots')
  const [search, setSearch] = useState('')
  const [searchResults, setSearchResults] = useState<MemberSummary[]>([])
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [jobId, setJobId] = useState<string | null>(null)
  const [status, setStatus] = useState<MassAssignStatus | null>(null)
  const [error, setError] = useState('')
  const [starting, setStarting] = useState(false)

  useEffect(() => {
    if (!open) return
    fetchRoles()
      .then(setRoles)
      .catch((err) => setError(formatApiError(err, t, 'common.errorLoadRoles')))
  }, [open, t])

  useEffect(() => {
    if (!open || target !== 'selected' || !search) {
      setSearchResults([])
      return
    }
    const timer = setTimeout(() => {
      fetchMembers(search, 1)
        .then((page) => setSearchResults(page.members))
        .catch(() => {})
    }, 300)
    return () => clearTimeout(timer)
  }, [open, target, search])

  useEffect(() => {
    if (!jobId) return
    let cancelled = false
    let interval: ReturnType<typeof setInterval>
    const poll = () => {
      fetchMassAssignStatus(jobId)
        .then((result) => {
          if (cancelled) return
          setStatus(result)
          if (result.status !== 'running') clearInterval(interval)
        })
        .catch(() => {
          if (!cancelled) clearInterval(interval)
        })
    }
    poll()
    interval = setInterval(poll, 2000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [jobId])

  const toggleSelected = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleStart = async () => {
    if (!roleId) {
      setError(t('members.massAssign.errorRole'))
      return
    }
    if (target === 'selected' && selectedIds.size === 0) {
      setError(t('members.massAssign.errorMembers'))
      return
    }
    setStarting(true)
    setError('')
    try {
      const id = await startMassAssign(roleId, target, target === 'selected' ? Array.from(selectedIds) : undefined)
      setJobId(id)
    } catch {
      setError(t('members.massAssign.errorStart'))
    } finally {
      setStarting(false)
    }
  }

  const handleClose = () => {
    setJobId(null)
    setStatus(null)
    setSelectedIds(new Set())
    setSearch('')
    setError('')
    onClose()
  }

  return (
    <Modal open={open} title={t('members.massAssign.title')} onClose={handleClose}>
      {!jobId ? (
        <div className="flex flex-col gap-3">
          <label className="text-sm text-muted" htmlFor="mass-role">
            {t('members.massAssign.role')}
          </label>
          <Select
            id="mass-role"
            value={roleId}
            onChange={(id) => setRoleId(id)}
            options={roles}
            kind="role"
            placeholder={t('members.massAssign.selectRole')}
          />

          <div className="flex flex-col gap-1.5">
            <label className="flex items-center gap-2 text-sm text-foreground">
              <input
                type="radio"
                name="target"
                checked={target === 'selected'}
                onChange={() => setTarget('selected')}
                className="accent-primary"
              />
              {t('members.massAssign.targetSelected')}
            </label>
            <label className="flex items-center gap-2 text-sm text-foreground">
              <input
                type="radio"
                name="target"
                checked={target === 'all'}
                onChange={() => setTarget('all')}
                className="accent-primary"
              />
              {t('members.massAssign.targetAll')}
            </label>
            <label className="flex items-center gap-2 text-sm text-foreground">
              <input
                type="radio"
                name="target"
                checked={target === 'all_except_bots'}
                onChange={() => setTarget('all_except_bots')}
                className="accent-primary"
              />
              {t('members.massAssign.targetExceptBots')}
            </label>
          </div>

          {target === 'selected' && (
            <div className="flex flex-col gap-2">
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={t('members.massAssign.search')}
                className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              />
              <p className="text-xs text-muted">{t('members.massAssign.selectedCount', { count: selectedIds.size })}</p>
              <div className="flex max-h-40 flex-col gap-1.5 overflow-y-auto">
                {searchResults.map((member) => (
                  <Checkbox
                    key={member.id}
                    checked={selectedIds.has(member.id)}
                    onChange={() => toggleSelected(member.id)}
                    label={member.display_name}
                  />
                ))}
              </div>
            </div>
          )}

          {error && <p className="text-sm text-danger">{error}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={handleClose} disabled={starting}>
              {t('common.cancel')}
            </Button>
            <Button variant="primary" onClick={handleStart} disabled={starting}>
              {starting ? t('members.massAssign.starting') : t('members.massAssign.start')}
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          <p className="text-sm text-foreground">
            {t('members.massAssign.processed', {
              processed: status?.processed ?? 0,
              total: status?.total ?? '…',
            })}
          </p>
          <p className="text-xs text-muted">
            {t('members.massAssign.stats', {
              succeeded: status?.succeeded ?? 0,
              skipped: status?.skipped ?? 0,
              failed: status?.failed ?? 0,
            })}
          </p>
          {status?.errors && status.errors.length > 0 && (
            <div className="max-h-32 overflow-y-auto rounded-control border border-border bg-background p-2 text-xs text-danger">
              {status.errors.map((line, index) => (
                <p key={index}>{line}</p>
              ))}
            </div>
          )}
          {status?.status !== 'running' && (
            <div className="flex justify-end pt-2">
              <Button variant="primary" onClick={handleClose}>
                {t('members.massAssign.done')}
              </Button>
            </div>
          )}
        </div>
      )}
    </Modal>
  )
}
