import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation, useParams } from 'react-router-dom'
import { lookupFetch, type LookupConfig } from './api/client'
import { CaptchaGate } from './components/CaptchaGate'
import { LookupLayout } from './components/LookupLayout'
import { PluginsLayout } from './components/PluginsLayout'
import { ScrollToTop } from './components/ScrollToTop'
import { LanguageProvider } from './context/LanguageContext'
import { AboutPage } from './pages/AboutPage'
import { AvatarsPage } from './pages/AvatarsPage'
import { BadgesPage } from './pages/BadgesPage'
import { BotPage } from './pages/BotPage'
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

function DsaRedirect() {
  const { id } = useParams()
  const qs = new URLSearchParams({ mode: 'dsa' })
  if (id) qs.set('id', id)
  return <Navigate to={`/?${qs.toString()}`} replace />
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

              <Route path="/plugins" element={<PluginsLayout />}>
                <Route index element={<PluginsPage />} />
                <Route path="snowflake" element={<SnowflakePage />} />
                <Route path="snowflake/:id" element={<SnowflakePage />} />
                <Route path="timestamp" element={<TimestampPage />} />
                <Route path="permissions" element={<PermissionsPage />} />
                <Route path="avatars" element={<AvatarsPage />} />
                <Route path="badges" element={<BadgesPage />} />
              </Route>

              {/* Legacy tool URLs → nested under /plugins */}
              <Route path="/snowflake" element={<Navigate to="/plugins/snowflake" replace />} />
              <Route path="/snowflake/:id" element={<SnowflakeLegacyRedirect />} />
              <Route path="/timestamp" element={<Navigate to="/plugins/timestamp" replace />} />
              <Route path="/permissions" element={<PermissionsLegacyRedirect />} />
              <Route path="/avatars" element={<Navigate to="/plugins/avatars" replace />} />
              <Route path="/badges" element={<Navigate to="/plugins/badges" replace />} />

              {/* DSA is a home mode — no standalone page */}
              <Route path="/dsa" element={<DsaRedirect />} />
              <Route path="/dsa/:id" element={<DsaRedirect />} />

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </LookupLayout>
        </LookupProvider>
      </BrowserRouter>
    </LanguageProvider>
  )
}

function SnowflakeLegacyRedirect() {
  const { id } = useParams()
  return <Navigate to={id ? `/plugins/snowflake/${id}` : '/plugins/snowflake'} replace />
}

function PermissionsLegacyRedirect() {
  const { search } = useLocation()
  return <Navigate to={`/plugins/permissions${search}`} replace />
}
