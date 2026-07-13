import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  deleteBracket,
  disableBracketShare,
  enableBracketShare,
  fetchBracketDetail,
  setBracketMatchWinner,
  type BracketDetail,
} from '../api/client'
import { BracketView, type PickHandler } from '../components/BracketView'
import { Button } from '../components/ui/Button'
import { Modal } from '../components/ui/Modal'

const FORMAT_LABEL: Record<string, string> = {
  single_elim: 'Single Elimination',
  double_elim: 'Double Elimination',
  round_robin: 'Round Robin',
}

export function BracketDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [bracket, setBracket] = useState<BracketDetail | null>(null)
  const [error, setError] = useState('')
  const [shareBusy, setShareBusy] = useState(false)
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [deleteBusy, setDeleteBusy] = useState(false)

  const reload = () => {
    if (!id) return
    fetchBracketDetail(id)
      .then((b) => {
        setBracket(b)
        setError('')
      })
      .catch(() => setError('Не удалось загрузить сетку'))
  }

  useEffect(reload, [id])

  const pickWinner: PickHandler = async (segment, roundIndex, matchIndex, winner) => {
    if (!id) return
    try {
      const updated = await setBracketMatchWinner(id, roundIndex, matchIndex, winner, segment)
      setBracket(updated)
    } catch {
      setError('Не удалось сохранить результат')
    }
  }

  const toggleShare = async () => {
    if (!id || !bracket) return
    setShareBusy(true)
    try {
      if (bracket.share_token) {
        await disableBracketShare(id)
        setBracket({ ...bracket, share_token: null })
      } else {
        const token = await enableBracketShare(id)
        setBracket({ ...bracket, share_token: token })
      }
    } catch {
      setError('Не удалось изменить доступ к ссылке')
    } finally {
      setShareBusy(false)
    }
  }

  const confirmDelete = async () => {
    if (!id) return
    setDeleteBusy(true)
    try {
      await deleteBracket(id)
      navigate('/brackets')
    } catch {
      setError('Не удалось удалить сетку')
      setDeleteBusy(false)
    }
  }

  if (!bracket) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
  }

  const shareUrl = bracket.share_token ? `${window.location.origin}/bracket/${bracket.share_token}` : null

  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <h1 className="text-lg font-semibold text-foreground">{bracket.title}</h1>
        <span className="rounded-full bg-primary-muted px-2.5 py-0.5 text-xs text-foreground">
          {FORMAT_LABEL[bracket.format] ?? bracket.format}
        </span>
        <Button variant="secondary" onClick={toggleShare} disabled={shareBusy} className="ml-auto">
          {bracket.share_token ? 'Отключить ссылку' : 'Поделиться ссылкой'}
        </Button>
        <Button variant="danger" onClick={() => setConfirmingDelete(true)}>
          Удалить
        </Button>
      </div>

      {shareUrl && (
        <p className="mb-4 text-sm text-muted">
          Публичная ссылка: <span className="text-foreground">{shareUrl}</span>
        </p>
      )}

      {error && <p className="mb-4 text-sm text-danger">{error}</p>}

      <BracketView bracket={bracket} onPick={pickWinner} />

      <Modal open={confirmingDelete} title="Удалить сетку?" onClose={() => setConfirmingDelete(false)}>
        <p className="mb-4 text-sm text-muted">Это действие необратимо.</p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setConfirmingDelete(false)} disabled={deleteBusy}>
            Отмена
          </Button>
          <Button variant="danger" onClick={confirmDelete} disabled={deleteBusy}>
            {deleteBusy ? 'Удаляем…' : 'Подтвердить'}
          </Button>
        </div>
      </Modal>
    </div>
  )
}
