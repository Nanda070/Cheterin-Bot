import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { WhatsNewCard, WhatsNewModal } from './components/WhatsNew'
import { LanguageProvider } from './context/LanguageContext'
import {
  LATEST_WHATS_NEW,
  dismissWhatsNew,
  isWhatsNewDismissed,
  whatsNewDismissKey,
} from './whatsNew'

function memoryStorage() {
  const store: Record<string, string> = {}
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = value
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      for (const key of Object.keys(store)) delete store[key]
    },
  }
}

describe('whatsNew dismiss persistence', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', memoryStorage())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('is not dismissed by default', () => {
    expect(isWhatsNewDismissed(LATEST_WHATS_NEW.version)).toBe(false)
  })

  it('persists dismiss per version key', () => {
    dismissWhatsNew(LATEST_WHATS_NEW.version)
    expect(localStorage.getItem(whatsNewDismissKey(LATEST_WHATS_NEW.version))).toBe('1')
    expect(isWhatsNewDismissed(LATEST_WHATS_NEW.version)).toBe(true)
    expect(isWhatsNewDismissed('2099.01')).toBe(false)
  })
})

describe('WhatsNewModal', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', memoryStorage())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('opens when the current version is not dismissed', () => {
    render(
      <LanguageProvider>
        <WhatsNewModal />
      </LanguageProvider>,
    )
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Что нового')).toBeInTheDocument()
  })

  it('stays closed when the version was already dismissed', () => {
    dismissWhatsNew(LATEST_WHATS_NEW.version)
    render(
      <LanguageProvider>
        <WhatsNewModal />
      </LanguageProvider>,
    )
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('writes dismiss on Got it and closes', () => {
    render(
      <LanguageProvider>
        <WhatsNewModal />
      </LanguageProvider>,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Понятно' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(isWhatsNewDismissed(LATEST_WHATS_NEW.version)).toBe(true)
  })
})

describe('WhatsNewCard', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', memoryStorage())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders the latest changelog bullets', () => {
    render(
      <LanguageProvider>
        <WhatsNewCard />
      </LanguageProvider>,
    )
    expect(screen.getByText('Что нового')).toBeInTheDocument()
    expect(screen.getByText(LATEST_WHATS_NEW.date)).toBeInTheDocument()
    expect(screen.getByText(/окно активности в днях/)).toBeInTheDocument()
    expect(screen.getByText(/ручное назначение команд A \/ B/)).toBeInTheDocument()
    expect(screen.getByText(/Premier-заявки, панели ролей/)).toBeInTheDocument()
  })
})
