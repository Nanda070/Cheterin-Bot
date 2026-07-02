import { ShieldCheck, ShieldWarning } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  activateLockdown,
  deactivateLockdown,
  fetchLockdownStatus,
  type LockdownStatus,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'

export function LockdownPage() {
  const [status, setStatus] = useState<LockdownStatus | null>(null)
  const [confirming, setConfirming] = useState<'activate' | 'deactivate' | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const reload = () => {
    fetchLockdownStatus()
      .then((s) => {
        setStatus(s)
        setError('')
      })
      .catch(() => setError('Не удалось получить статус'))
  }

  useEffect(reload, [])

  const confirm = async () => {
    setBusy(true)
    setError('')
    try {
      if (confirming === 'activate') await activateLockdown()
      if (confirming === 'deactivate') await deactivateLockdown()
      setConfirming(null)
      reload()
    } catch {
      setError('Операция не удалась — подробности в логах бота')
    } finally {
      setBusy(false)
    }
  }

  if (!status) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
  }

  return (
    <Card className="animate-fade-in-up max-w-xl">
      <div className="flex items-center gap-3">
        {status.active ? (
          <ShieldWarning size={28} weight="fill" className="text-danger" />
        ) : (
          <ShieldCheck size={28} weight="fill" className="text-success" />
        )}
        <div>
          <h1 className="font-semibold text-foreground">
            Антиспам-режим: {status.active ? 'ВКЛЮЧЁН' : 'ВЫКЛЮЧЕН'}
          </h1>
          <p className="text-sm text-muted">
            {status.active
              ? `Изменённых ролей в бэкапе: ${status.role_count}`
              : 'Все роли работают в обычном режиме.'}
          </p>
        </div>
      </div>

      {error && <p className="mt-3 text-sm text-danger">{error}</p>}

      <div className="mt-5 flex gap-2">
        {status.active ? (
          <Button variant="secondary" onClick={() => setConfirming('deactivate')} disabled={busy}>
            Выключить антиспам
          </Button>
        ) : (
          <Button variant="danger" onClick={() => setConfirming('activate')} disabled={busy}>
            Включить антиспам
          </Button>
        )}
      </div>

      <Modal
        open={confirming !== null}
        title={confirming === 'activate' ? 'Включить антиспам-режим?' : 'Выключить антиспам-режим?'}
        onClose={() => setConfirming(null)}
      >
        <p className="mb-4 text-sm text-muted">
          {confirming === 'activate'
            ? 'У всех не-исключённых ролей будут сняты права massive mention, текущее состояние сохранится в бэкап.'
            : 'Права ролей будут восстановлены из бэкапа.'}
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setConfirming(null)} disabled={busy}>
            Отмена
          </Button>
          <Button variant="danger" onClick={confirm} disabled={busy}>
            {busy ? 'Выполняем…' : 'Подтвердить'}
          </Button>
        </div>
      </Modal>
    </Card>
  )
}
