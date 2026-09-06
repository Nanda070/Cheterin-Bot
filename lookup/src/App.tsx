import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { lookupFetch, type LookupConfig } from './api/client'
import { CaptchaGate } from './components/CaptchaGate'
import { LookupLayout } from './components/LookupLayout'
import { ScrollToTop } from './components/ScrollToTop'
import { LanguageProvider } from './context/LanguageContext'
import { AboutPage } from './pages/AboutPage'
import { AvatarsPage } from './pages/AvatarsPage'
import { BadgesPage } from './pages/BadgesPage'
import { BotPage } from './pages/BotPage'
import { DsaPage } from './pages/DsaPage'
import { HomePage } from './pages/HomePage'
import { PermissionsPage } from './pages/PermissionsPage'
import { PluginsPage } from './pages/PluginsPage'
import { ServerPage } from './pages/ServerPage'
import { SnowflakePage } from './pages/SnowflakePage'
import { TimestampPage } from './pages/TimestampPage'
import { UserPage } from './pages/UserPage'

// ---------------------------------------------------------------------------
// Lookup config + CAPTCHA context
// ---------------------------------------------------------------------------

type CaptchaContextType = {
  config: LookupConfig | null
  showCaptcha: (onVerified?: () => void) => void
}

export const LookupContext = createContext<CaptchaContextType>({
  config: null,
  showCaptcha: () => undefined,
})

export function useLookupContext() {
  return useContext(LookupContext)
}

function LookupProvider({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<LookupConfig | null>(null)
  const [captchaVisible, setCaptchaVisible] = useState(false)
  const [verifiedCb, setVerifiedCb] = useState<(() => void) | null>(null)

  useEffect(() => {
    lookupFetch<LookupConfig>('/config').then(setConfig).catch(() => null)
  }, [])

  const showCaptcha = (onVerified?: () => void) => {
    setVerifiedCb(onVerified ? () => onVerified : null)
    setCaptchaVisible(true)
  }

  return (
    <LookupContext.Provider value={{ config, showCaptcha }}>
      {children}
      {captchaVisible && (
        <CaptchaGate
          config={config}
          onVerified={() => {
            setCaptchaVisible(false)
            verifiedCb?.()
          }}
          onDismiss={() => setCaptchaVisible(false)}
        />
      )}
    </LookupContext.Provider>
  )
}

export default function App() {
  return (
    <LanguageProvider>
      <BrowserRouter basename="/lookup">
        <ScrollToTop />
        <LookupProvider>
          <LookupLayout>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/user/:id" element={<UserPage />} />
              <Route path="/bot/:id" element={<BotPage />} />
              <Route path="/server/:code" element={<ServerPage />} />
              <Route path="/snowflake" element={<SnowflakePage />} />
              <Route path="/snowflake/:id" element={<SnowflakePage />} />
              <Route path="/timestamp" element={<TimestampPage />} />
              <Route path="/permissions" element={<PermissionsPage />} />
              <Route path="/avatars" element={<AvatarsPage />} />
              <Route path="/badges" element={<BadgesPage />} />
              <Route path="/dsa" element={<DsaPage />} />
              <Route path="/dsa/:id" element={<DsaPage />} />
              <Route path="/plugins" element={<PluginsPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </LookupLayout>
        </LookupProvider>
      </BrowserRouter>
    </LanguageProvider>
  )
}
