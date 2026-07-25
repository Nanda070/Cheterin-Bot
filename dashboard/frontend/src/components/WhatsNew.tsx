import { Sparkle } from '@phosphor-icons/react'
import { useCallback, useState } from 'react'
import { useT } from '../context/LanguageContext'
import {
  LATEST_WHATS_NEW,
  dismissWhatsNew,
  isWhatsNewDismissed,
  type WhatsNewEntry,
} from '../whatsNew'
import { Button } from './ui/Button'
import { Card } from './ui/Card'
import { Modal } from './ui/Modal'

function WhatsNewBullets({ entry }: { entry: WhatsNewEntry }) {
  const t = useT()
  return (
    <ul className="mt-3 flex list-disc flex-col gap-1.5 pl-5 text-sm text-muted">
      {entry.itemKeys.map((key) => (
        <li key={key}>{t(`whatsNew.item.${key}`)}</li>
      ))}
    </ul>
  )
}

/** Compact Home card — always shows the latest entry. */
export function WhatsNewCard() {
  const t = useT()
  const entry = LATEST_WHATS_NEW

  return (
    <Card className="mb-4 animate-fade-in-up">
      <div className="flex items-center gap-2 text-foreground">
        <Sparkle size={20} weight="fill" className="text-primary" />
        <h2 className="font-semibold">{t('whatsNew.title')}</h2>
        <span className="ml-auto text-xs text-muted">{t('whatsNew.subtitle', { date: entry.date })}</span>
      </div>
      <WhatsNewBullets entry={entry} />
    </Card>
  )
}

/**
 * Auto-opens once per changelog version until dismissed.
 * localStorage key: `cheterin.whatsNew.dismissed.<version>`.
 */
export function WhatsNewModal() {
  const t = useT()
  const entry = LATEST_WHATS_NEW
  const [open, setOpen] = useState(() => !isWhatsNewDismissed(entry.version))

  const handleDismiss = useCallback(() => {
    dismissWhatsNew(entry.version)
    setOpen(false)
  }, [entry.version])

  return (
    <Modal open={open} title={t('whatsNew.title')} onClose={handleDismiss}>
      <p className="mb-1 text-sm text-muted">{t('whatsNew.subtitle', { date: entry.date })}</p>
      <WhatsNewBullets entry={entry} />
      <div className="mt-5 flex justify-end">
        <Button type="button" onClick={handleDismiss}>
          {t('whatsNew.gotIt')}
        </Button>
      </div>
    </Modal>
  )
}
