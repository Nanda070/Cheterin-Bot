import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { LanguageProvider } from './context/LanguageContext'
import { LookupLayout } from './components/LookupLayout'
import { HomePage } from './pages/HomePage'
import { AboutPage } from './pages/AboutPage'
import { UserPage } from './pages/UserPage'
import { BotPage } from './pages/BotPage'
import { ServerPage } from './pages/ServerPage'
import { SnowflakePage } from './pages/SnowflakePage'
import { PermissionsPage } from './pages/PermissionsPage'
import { AvatarsPage } from './pages/AvatarsPage'
import { BadgesPage } from './pages/BadgesPage'
import { DsaPage } from './pages/DsaPage'
import { PluginsPage } from './pages/PluginsPage'

export default function App() {
  return (
    <LanguageProvider>
      <BrowserRouter basename="/lookup">
        <LookupLayout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/user/:id" element={<UserPage />} />
            <Route path="/bot/:id" element={<BotPage />} />
            <Route path="/server/:code" element={<ServerPage />} />
            <Route path="/snowflake" element={<SnowflakePage />} />
            <Route path="/snowflake/:id" element={<SnowflakePage />} />
            <Route path="/permissions" element={<PermissionsPage />} />
            <Route path="/avatars" element={<AvatarsPage />} />
            <Route path="/badges" element={<BadgesPage />} />
            <Route path="/dsa" element={<DsaPage />} />
            <Route path="/dsa/:id" element={<DsaPage />} />
            <Route path="/plugins" element={<PluginsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </LookupLayout>
      </BrowserRouter>
    </LanguageProvider>
  )
}
