import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  deleteBracket,
  disableBracketShare,
  enableBracketShare,
  fetchBracketDetail,
  setBracketMatchWinner,
  type BracketDetail,
  type BracketFormat,
} from '../api/client'
import { BracketView, type PickHandler } from '../components/BracketView'
import { Button } from '../components/ui/Button'
import { Modal } from '../components/ui/Modal'
import { useT } from '../context/LanguageContext'

export function BracketDetailPage() {
  const t = useT()
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [bracket, setBracket] = useState<BracketDetail | null>(null)
  const [error, setError] = useState('')
  const [shareBusy, setShareBusy] = useState(false)
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [deleteBusy, setDeleteBusy] = useState(false)

  const formatLabel = (format: BracketFormat | string) => {
    const key = `brackets.format.${format === 'single_elim' ? 'singleElim' : format === 'double_elim' ? 'doubleElim' : 'roundRobin'}`
    return t(key)
  }

  const reload = () => {
    if (!id) return
    fetchBracketDetail(id)
      .then((b) => {
        setBracket(b)
        setError('')
      })
      .catch(() => setError(t('brackets.detail.errorLoad')))
  }

  useEffect(reload, [id, t])

  const pickWinner: PickHandler = async (segment, roundIndex, matchIndex, winner) => {
    if (!id) return
    try {
      const updated = await setBracketMatchWinner(id, roundIndex, matchIndex, winner, segment)
      setBracket(updated)
    } catch {
      setError(t('brackets.detail.errorSave'))
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
      setError(t('brackets.detail.errorShare'))
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
      setError(t('brackets.detail.errorDelete'))
      setDeleteBusy(false)
    }
  }

  if (!bracket) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  const shareUrl = bracket.share_token ? `${window.location.origin}/bracket/${bracket.share_token}` : null

  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <h1 className="text-lg font-semibold text-foreground">{bracket.title}</h1>
        <span className="rounded-full bg-primary-muted px-2.5 py-0.5 text-xs text-foreground">
          {formatLabel(bracket.format)}
        </span>
        <Button variant="secondary" onClick={toggleShare} disabled={shareBusy} className="ml-auto">
          {bracket.share_token ? t('brackets.detail.shareDisable') : t('brackets.detail.shareEnable')}
        </Button>
        <Button variant="danger" onClick={() => setConfirmingDelete(true)}>
          {t('common.delete')}
        </Button>
      </div>

      {shareUrl && (
        <p className="mb-4 text-sm text-muted">
          {t('brackets.detail.publicLink')} <span className="text-foreground">{shareUrl}</span>
        </p>
      )}

      {error && <p className="mb-4 text-sm text-danger">{error}</p>}

      <BracketView bracket={bracket} onPick={pickWinner} />

      <Modal open={confirmingDelete} title={t('brackets.detail.deleteConfirm')} onClose={() => setConfirmingDelete(false)}>
        <p className="mb-4 text-sm text-muted">{t('brackets.detail.deleteIrreversible')}</p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setConfirmingDelete(false)} disabled={deleteBusy}>
            {t('common.cancel')}
          </Button>
          <Button variant="danger" onClick={confirmDelete} disabled={deleteBusy}>
            {deleteBusy ? t('common.deleting') : t('common.confirm')}
          </Button>
        </div>
      </Modal>
    </div>
  )
}
