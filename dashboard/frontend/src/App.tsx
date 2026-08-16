import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { LanguageProvider } from './context/LanguageContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { PublicLandingOrDashboard } from './components/PublicLandingOrDashboard'
import { LoginPage } from './pages/Login'
import { LandingPage } from './pages/Landing'
import { ServerSelectPage } from './pages/ServerSelect'
import { AccessDeniedPage } from './pages/AccessDenied'
import { DashboardShell } from './pages/DashboardShell'
import { HomePage } from './pages/Home'
import { MembersPage } from './pages/Members'
import { LockdownPage } from './pages/Lockdown'
import { MessageBuilderPage } from './pages/MessageBuilder'
import { FeedbackPage } from './pages/Feedback'
import { EventsPage } from './pages/Events'
import { BracketDetailPage } from './pages/BracketDetail'
import { PublicBracketPage } from './pages/PublicBracket'
import { VoiceRoomsPage } from './pages/VoiceRooms'
import { NewsPage } from './pages/News'
import { DocsPage } from './pages/Docs'
import { TermsPage } from './pages/Terms'
import { PrivacyPage } from './pages/Privacy'
import { CreditsPage } from './pages/Credits'
import { SansPage } from './pages/Sans'
import { WaterfallRoomPage, CoreRoomPage, JudgmentRoomPage } from './pages/SecretRoom'
import { ServerLogPage } from './pages/ServerLog'
import { LevelsPage } from './pages/Levels'
import { VoiceStatsPage } from './pages/VoiceStats'
import { StreamsPage } from './pages/Streams'
import { LeaderboardPage } from './pages/Leaderboard'
import { NotFoundPage } from './pages/NotFound'
import { FamilyPage } from './pages/Family'
import { MafiaPage } from './pages/Mafia'
import { PublicMafiaActionPage } from './pages/PublicMafiaAction'
import { BunkerPage } from './pages/Bunker'
import { PublicBunkerActionPage } from './pages/PublicBunkerAction'
import { FunPage } from './pages/Fun'
import { EconomyPage } from './pages/Economy'
import { SuperAdminPage } from './pages/SuperAdmin'
import { ServerSettingsPage } from './pages/ServerSettings'
import { AutoModPage } from './pages/AutoMod'
import { ServerEntryPage } from './pages/ServerEntry'
import { CtdPage } from './pages/Ctd'
import { RedirectCustomCommands } from './pages/CustomCommands'
import { MessagesPage } from './pages/Messages'
import { BirthdaysCalendarPage } from './pages/BirthdaysCalendar'
import { RelationsPage } from './pages/Relations'
import { ValCheckerPage } from './pages/ValChecker'
import { CustomsPage } from './pages/Customs'
import { HealthPage } from './pages/Health'
import { BannerRotationPage } from './pages/BannerRotation'
import { ValorantPage } from './pages/Valorant'

function App() {
  return (
    <BrowserRouter>
      <LanguageProvider>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/about" element={<LandingPage />} />
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
            <Route path="/credits" element={<CreditsPage />} />
            <Route path="/sans" element={<SansPage />} />
            <Route path="/snowdin" element={<SansPage />} />
            <Route path="/waterfall" element={<WaterfallRoomPage />} />
            <Route path="/core" element={<CoreRoomPage />} />
            <Route path="/judgment" element={<JudgmentRoomPage />} />
            <Route path="/leaderboard/:guildId" element={<LeaderboardPage />} />
            <Route path="/leaderboard" element={<LeaderboardPage />} />
            <Route
              path="/"
              element={
                <PublicLandingOrDashboard>
                  <DashboardShell />
                </PublicLandingOrDashboard>
              }
            >
              <Route index element={<HomePage />} />
              <Route path="members" element={<MembersPage />} />
              <Route path="lockdown" element={<LockdownPage />} />
              <Route path="reaction-roles" element={<MessageBuilderPage />} />
              <Route path="feedback" element={<FeedbackPage />} />
              <Route path="events" element={<EventsPage />} />
              <Route path="brackets" element={<Navigate to="/events?tab=brackets" replace />} />
              <Route path="brackets/:id" element={<BracketDetailPage />} />
              <Route path="supply" element={<Navigate to="/family?tab=supply" replace />} />
              <Route path="family" element={<FamilyPage />} />
              <Route path="mafia" element={<MafiaPage />} />
              <Route path="bunker" element={<BunkerPage />} />
              <Route path="fun" element={<FunPage />} />
              <Route path="giveaways" element={<Navigate to="/events?tab=giveaways" replace />} />
              <Route path="daily-topic" element={<Navigate to="/fun?tab=dailyTopic" replace />} />
              <Route path="custom-commands" element={<RedirectCustomCommands />} />
              <Route path="messages" element={<MessagesPage />} />
              <Route path="scheduled-messages" element={<Navigate to="/messages?tab=scheduled" replace />} />
              <Route path="sticky" element={<Navigate to="/messages?tab=sticky" replace />} />
              <Route path="polls" element={<Navigate to="/events?tab=polls" replace />} />
              <Route path="preview" element={<Navigate to="/settings?tab=customCommands&view=preview" replace />} />
              <Route
                path="command-preview"
                element={<Navigate to="/settings?tab=customCommands&view=preview" replace />}
              />
              <Route path="invites" element={<Navigate to="/server-entry?tab=invites" replace />} />
              <Route path="timed-roles" element={<Navigate to="/members?tab=timedRoles" replace />} />
              <Route path="birthdays" element={<BirthdaysCalendarPage />} />
              <Route path="relations" element={<RelationsPage />} />
              <Route path="starboard" element={<Navigate to="/messages?tab=starboard" replace />} />
              <Route path="valchecker" element={<ValCheckerPage />} />
              <Route path="valorant" element={<ValorantPage />} />
              <Route path="customs" element={<CustomsPage />} />
              <Route path="auto-reactions" element={<Navigate to="/fun?tab=autoEmoji" replace />} />
              <Route path="bot-profile" element={<Navigate to="/settings?tab=botProfile" replace />} />
              <Route path="automod" element={<AutoModPage />} />
              <Route path="server-entry" element={<ServerEntryPage />} />
              <Route path="antiraid" element={<Navigate to="/lockdown?tab=antiraid" replace />} />
              <Route path="verification" element={<Navigate to="/lockdown?tab=verification" replace />} />
              <Route path="voice-rooms" element={<VoiceRoomsPage />} />
              <Route path="news" element={<NewsPage />} />
              <Route path="levels" element={<LevelsPage />} />
              <Route path="economy" element={<EconomyPage />} />
              <Route path="casino" element={<Navigate to="/economy?tab=casino" replace />} />
              <Route path="streams" element={<StreamsPage />} />
              <Route path="serverlog" element={<ServerLogPage />} />
              <Route path="voice-stats" element={<VoiceStatsPage />} />
              <Route path="audit" element={<Navigate to="/settings?tab=audit" replace />} />
              <Route path="welcome" element={<Navigate to="/server-entry" replace />} />
              <Route path="auto-roles" element={<Navigate to="/server-entry?tab=autoroles" replace />} />
              <Route path="config" element={<Navigate to="/lockdown" replace />} />
              <Route path="settings" element={<ServerSettingsPage />} />
              <Route path="ctd" element={<CtdPage />} />
              <Route path="superadmin" element={<SuperAdminPage />} />
              <Route path="health" element={<HealthPage />} />
              <Route path="banner-rotation" element={<BannerRotationPage />} />
            </Route>
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </AuthProvider>
      </LanguageProvider>
    </BrowserRouter>
  )
}

export default App
