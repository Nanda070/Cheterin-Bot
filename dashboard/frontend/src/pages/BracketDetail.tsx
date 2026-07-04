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
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'

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

  const pickWinner = async (roundIndex: number, matchIndex: number, winner: 'a' | 'b') => {
    if (!id) return
    try {
      const updated = await setBracketMatchWinner(id, roundIndex, matchIndex, winner)
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

      <div className="flex gap-6 overflow-x-auto">
        {bracket.rounds.map((round, roundIndex) => (
          <div key={roundIndex} className="flex flex-col justify-around gap-4">
            <p className="text-xs font-medium uppercase tracking-wide text-muted">
              {roundIndex === bracket.rounds.length - 1 ? 'Финал' : `Раунд ${roundIndex + 1}`}
            </p>
            {round.map((match, matchIndex) => {
              const ready = match.slot_a !== null && match.slot_b !== null
              return (
                <Card key={matchIndex} className="!p-2 w-48">
                  <button
                    type="button"
                    disabled={!ready}
                    onClick={() => ready && pickWinner(roundIndex, matchIndex, 'a')}
                    className={`block w-full rounded-control px-2 py-1 text-left text-sm ${
                      match.winner === 'a' ? 'font-semibold text-foreground' : 'text-muted'
                    } ${ready ? 'cursor-pointer hover:bg-surface-hover' : ''}`}
                  >
                    {match.slot_a ?? '—'}
                  </button>
                  <button
                    type="button"
                    disabled={!ready}
                    onClick={() => ready && pickWinner(roundIndex, matchIndex, 'b')}
                    className={`block w-full rounded-control px-2 py-1 text-left text-sm ${
                      match.winner === 'b' ? 'font-semibold text-foreground' : 'text-muted'
                    } ${ready ? 'cursor-pointer hover:bg-surface-hover' : ''}`}
                  >
                    {match.slot_b ?? '—'}
                  </button>
                </Card>
              )
            })}
          </div>
        ))}
      </div>

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
