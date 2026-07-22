import { ArrowsClockwise, Headset, LockSimple, LockSimpleOpen, Trash, UsersThree } from '@phosphor-icons/react'

import { useEffect, useState } from 'react'

import { deleteVoiceRoom, fetchVoiceRooms, publishVoicePanel, type VoiceRoom } from '../api/client'
import { formatApiError } from '../api/errors'

import { ModuleConfigPanel } from '../components/ModuleConfigPanel'

import { Button } from '../components/ui/Button'

import { Card } from '../components/ui/Card'

import { Modal } from '../components/ui/Modal'

import { useT } from '../context/LanguageContext'



type Tab = 'rooms' | 'settings'



export function VoiceRoomsPage() {

  const t = useT()

  const [tab, setTab] = useState<Tab>('rooms')

  const [rooms, setRooms] = useState<VoiceRoom[] | null>(null)

  const [error, setError] = useState('')

  const [notice, setNotice] = useState('')

  const [busy, setBusy] = useState(false)

  const [deleting, setDeleting] = useState<VoiceRoom | null>(null)



  const reload = () => {

    fetchVoiceRooms()

      .then((data) => {

        setRooms(data)

        setError('')

      })

      .catch(() => setError(t('voiceRooms.errorLoad')))

  }



  useEffect(reload, [t])



  const confirmDelete = async () => {

    if (!deleting) return

    setBusy(true)

    setError('')

    try {

      await deleteVoiceRoom(deleting.channel_id)

      setDeleting(null)

      reload()

    } catch (err) {

      setError(formatApiError(err, t, 'voiceRooms.errorDelete'))

    } finally {

      setBusy(false)

    }

  }



  const republish = async () => {

    setBusy(true)

    setError('')

    setNotice('')

    try {

      await publishVoicePanel()

      setNotice(t('voiceRooms.published'))

    } catch (err) {

      setError(formatApiError(err, t, 'voiceRooms.errorPublish'))

    } finally {

      setBusy(false)

    }

  }



  const tabs = [

    { key: 'rooms' as const, label: t('voiceRooms.tab.rooms') },

    { key: 'settings' as const, label: t('voiceRooms.tab.settings') },

  ]



  return (

    <div className="flex max-w-3xl flex-col gap-6">

      <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">

        <Headset size={22} className="text-primary" />

        {t('voiceRooms.title')}

      </h1>



      <div className="flex gap-1 border-b border-border">

        {tabs.map(({ key, label }) => (

          <button

            key={key}

            type="button"

            onClick={() => setTab(key)}

            className={`border-b-2 px-3 py-2 text-sm transition-colors ${

              tab === key ? 'border-primary text-foreground' : 'border-transparent text-muted hover:text-foreground'

            }`}

          >

            {label}

          </button>

        ))}

      </div>



      {tab === 'settings' && (

        <ModuleConfigPanel variant="voice" title={t('config.section.voice')} intro={t('voiceRooms.settingsIntro')} />

      )}



      {tab === 'rooms' && !rooms && <p className="text-sm text-muted">{error || t('common.loading')}</p>}



      {tab === 'rooms' && rooms && (

        <>

      <div className="flex items-center justify-end gap-2">

          <Button variant="secondary" onClick={reload} disabled={busy}>

            <ArrowsClockwise size={16} />

            {t('voiceRooms.refresh')}

          </Button>

          <Button variant="primary" onClick={republish} disabled={busy}>

            {t('voiceRooms.publishPanel')}

          </Button>

      </div>



      {error && <p className="text-sm text-danger">{error}</p>}

      {notice && <p className="text-sm text-primary">{notice}</p>}



      {rooms.length === 0 && (

        <Card>

          <p className="text-sm text-muted">{t('voiceRooms.empty')}</p>

        </Card>

      )}



      {rooms.map((room) => (

        <Card key={room.channel_id} className="animate-fade-in-up">

          <div className="flex items-start justify-between gap-3">

            <div className="min-w-0">

              <p className="flex items-center gap-2 font-semibold text-foreground">

                {room.is_closed ? (

                  <LockSimple size={16} className="shrink-0 text-warning" />

                ) : (

                  <LockSimpleOpen size={16} className="shrink-0 text-success" />

                )}

                <span className="truncate">{room.name}</span>

              </p>

              <p className="mt-1 text-sm text-muted">

                {t('voiceRooms.owner', { name: room.owner_display })} ·{' '}

                {room.is_closed ? t('voiceRooms.closed') : t('voiceRooms.open')} · {t('game.limit')}{' '}

                {room.user_limit === 0 ? t('game.noLimit') : room.user_limit}

              </p>

              <p className="mt-1 flex items-center gap-1 text-sm text-muted">

                <UsersThree size={15} />

                {t('voiceRooms.inRoom', { count: room.member_count })}

                {!room.exists && <span className="text-danger"> · {t('voiceRooms.channelMissing')}</span>}

              </p>

            </div>

            <Button variant="danger" onClick={() => setDeleting(room)} disabled={busy}>

              <Trash size={16} />

              {t('common.delete')}

            </Button>

          </div>

        </Card>

      ))}



      <Modal open={deleting !== null} title={t('voiceRooms.deleteConfirm')} onClose={() => setDeleting(null)}>

        <p className="mb-4 text-sm text-muted">{t('voiceRooms.deleteWarning', { name: deleting?.name ?? '' })}</p>

        <div className="flex justify-end gap-2">

          <Button variant="ghost" onClick={() => setDeleting(null)} disabled={busy}>

            {t('common.cancel')}

          </Button>

          <Button variant="danger" onClick={confirmDelete} disabled={busy}>

            {busy ? t('common.deleting') : t('common.delete')}

          </Button>

        </div>

      </Modal>

        </>

      )}

    </div>

  )

}


