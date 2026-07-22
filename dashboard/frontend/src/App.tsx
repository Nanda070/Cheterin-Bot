import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { LanguageProvider } from './context/LanguageContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { LoginPage } from './pages/Login'
import { ServerSelectPage } from './pages/ServerSelect'
import { AccessDeniedPage } from './pages/AccessDenied'
import { DashboardShell } from './pages/DashboardShell'
import { HomePage } from './pages/Home'
import { MembersPage } from './pages/Members'
import { LockdownPage } from './pages/Lockdown'
import { MessageBuilderPage } from './pages/MessageBuilder'
import { FeedbackPage } from './pages/Feedback'
import { EventsPage } from './pages/Events'
import { BracketsPage } from './pages/Brackets'
import { BracketDetailPage } from './pages/BracketDetail'
import { PublicBracketPage } from './pages/PublicBracket'
import { SupplyPage } from './pages/Supply'
import { VoiceRoomsPage } from './pages/VoiceRooms'
import { NewsPage } from './pages/News'
import { DocsPage } from './pages/Docs'
import { TermsPage } from './pages/Terms'
import { PrivacyPage } from './pages/Privacy'
import { ServerLogPage } from './pages/ServerLog'
import { LevelsPage } from './pages/Levels'
import { VoiceStatsPage } from './pages/VoiceStats'
import { AuditPage } from './pages/Audit'
import { StreamsPage } from './pages/Streams'
import { LeaderboardPage } from './pages/Leaderboard'
import { NotFoundPage } from './pages/NotFound'
import { FamilyPage } from './pages/Family'
import { MafiaPage } from './pages/Mafia'
import { PublicMafiaActionPage } from './pages/PublicMafiaAction'
import { BunkerPage } from './pages/Bunker'
import { PublicBunkerActionPage } from './pages/PublicBunkerAction'
import { FunPage } from './pages/Fun'
import { CasinoPage } from './pages/Casino'
import { EconomyPage } from './pages/Economy'
import { SuperAdminPage } from './pages/SuperAdmin'
import { DailyTopicPage } from './pages/DailyTopic'
import { ServerSettingsPage } from './pages/ServerSettings'
import { AutoModPage } from './pages/AutoMod'
import { ServerEntryPage } from './pages/ServerEntry'

function App() {
  return (
    <BrowserRouter>
      <LanguageProvider>
        <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/servers"
            element={
              <ProtectedRoute requireGuild={false}>
                <ServerSelectPage />
              </ProtectedRoute>
            }
          />
          <Route path="/access-denied" element={<AccessDeniedPage />} />
          <Route path="/bracket/:token" element={<PublicBracketPage />} />
          <Route path="/mafia/:token" element={<PublicMafiaActionPage />} />
          <Route path="/bunker/:token" element={<PublicBunkerActionPage />} />
          <Route path="/docs" element={<DocsPage />} />
          <Route path="/docs/:sectionId" element={<DocsPage />} />
          <Route path="/terms" element={<TermsPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/leaderboard" element={<LeaderboardPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardShell />
              </ProtectedRoute>
            }
          >
            <Route index element={<HomePage />} />
            <Route path="members" element={<MembersPage />} />
            <Route path="lockdown" element={<LockdownPage />} />
            <Route path="reaction-roles" element={<MessageBuilderPage />} />
            <Route path="feedback" element={<FeedbackPage />} />
            <Route path="events" element={<EventsPage />} />
            <Route path="brackets" element={<BracketsPage />} />
            <Route path="brackets/:id" element={<BracketDetailPage />} />
            <Route path="supply" element={<SupplyPage />} />
            <Route path="family" element={<FamilyPage />} />
            <Route path="mafia" element={<MafiaPage />} />
            <Route path="bunker" element={<BunkerPage />} />
            <Route path="fun" element={<FunPage />} />
            <Route path="giveaways" element={<Navigate to="/events" replace />} />
            <Route path="daily-topic" element={<DailyTopicPage />} />
            <Route path="automod" element={<AutoModPage />} />
            <Route path="server-entry" element={<ServerEntryPage />} />
            <Route path="antiraid" element={<Navigate to="/lockdown" replace />} />
            <Route path="verification" element={<Navigate to="/lockdown" replace />} />
            <Route path="voice-rooms" element={<VoiceRoomsPage />} />
            <Route path="news" element={<NewsPage />} />
            <Route path="levels" element={<LevelsPage />} />
            <Route path="economy" element={<EconomyPage />} />
            <Route path="casino" element={<CasinoPage />} />
            <Route path="streams" element={<StreamsPage />} />
            <Route path="serverlog" element={<ServerLogPage />} />
            <Route path="voice-stats" element={<VoiceStatsPage />} />
            <Route path="audit" element={<AuditPage />} />
            <Route path="welcome" element={<Navigate to="/server-entry" replace />} />
            <Route path="auto-roles" element={<Navigate to="/server-entry" replace />} />
            <Route path="config" element={<Navigate to="/lockdown" replace />} />
            <Route path="settings" element={<ServerSettingsPage />} />
            <Route path="ctd" element={<CtdPage />} />
            <Route path="superadmin" element={<SuperAdminPage />} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
        </AuthProvider>
      </LanguageProvider>
    </BrowserRouter>
  )
}

export default App
