# Graph Report - frontend  (2026-07-24)

## Corpus Check
- 189 files · ~198,858 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1010 nodes · 3397 edges · 54 communities (52 shown, 2 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5b181d71`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- react
- apiFetch
- client.ts
- renderWithLanguage.tsx
- ServerEntry.tsx
- devDependencies
- Lockdown.tsx
- types.ts
- Docs.tsx
- BracketDetail.tsx
- Bunker.tsx
- AutoMod.tsx
- compilerOptions
- ModuleConfigPanel.tsx
- Family.tsx
- compilerOptions
- FeedbackCategories.tsx
- useT
- useLanguage
- AuthContext.tsx
- LanguageContext.tsx
- Fun.tsx
- Members.tsx
- ServerSelect.tsx
- Casino.tsx
- Economy.tsx
- plugins
- VoiceStats.tsx
- DashboardShell.tsx
- Login.tsx
- Welcome.tsx
- tsconfig.json
- Toggle.tsx
- FeedbackCaseDetailPanel.tsx
- Home.tsx
- Card.tsx
- Mafia.tsx
- AntiRaid.tsx
- PublicMafiaAction.tsx
- Supply.tsx
- formatApiError
- ServerSettings.tsx
- Giveaways.tsx
- Streams.tsx
- ServerSelect.tsx
- ScheduledMessages.tsx
- StickyMessages.tsx
- Toggle.tsx
- VoiceRooms.tsx
- Polls.tsx
- Tempban.tsx

## God Nodes (most connected - your core abstractions)
1. `apiFetch()` - 173 edges
2. `useT()` - 147 edges
3. `jsonInit()` - 99 edges
4. `formatApiError()` - 93 edges
5. `react` - 83 edges
6. `Button()` - 52 edges
7. `Card()` - 51 edges
8. `fetchChannels()` - 50 edges
9. `Select()` - 34 edges
10. `fetchRoles()` - 31 edges

## Surprising Connections (you probably didn't know these)
- `HeadingAnchor()` --calls--> `useLanguage()`  [EXTRACTED]
  src/pages/docs/docPrimitives.tsx → src/context/LanguageContext.tsx
- `FilterExtraFields()` --calls--> `useT()`  [EXTRACTED]
  src/pages/AutoMod.tsx → src/context/LanguageContext.tsx
- `FeatureSection()` --calls--> `useT()`  [EXTRACTED]
  src/pages/Landing.tsx → src/context/LanguageContext.tsx
- `AuthProvider()` --calls--> `fetchCurrentUser()`  [EXTRACTED]
  src/context/AuthContext.tsx → src/api/client.ts
- `LandingPage()` --calls--> `loginUrl()`  [EXTRACTED]
  src/pages/Landing.tsx → src/api/client.ts

## Import Cycles
- None detected.

## Communities (54 total, 2 thin omitted)

### Community 0 - "react"
Cohesion: 0.25
Nodes (15): Code(), DocSection, H(), H3(), HeadingAnchor(), Note(), OL(), P() (+7 more)

### Community 1 - "apiFetch"
Cohesion: 0.13
Nodes (20): CustomEmoji, decideFamilyTicket(), deleteFamilyBirthday(), FamilyBirthday, FamilyRosterGroup, FamilySettings, FamilyTicket, FamilyTicketsPage (+12 more)

### Community 2 - "client.ts"
Cohesion: 0.04
Nodes (54): AutoRolesSettings, BirthdayEntry, BracketStandingsRow, BunkerAbilityAnnouncement, BunkerAdditionalInfo, BunkerAgeInfo, BunkerBodyType, BunkerGamePhase (+46 more)

### Community 3 - "renderWithLanguage.tsx"
Cohesion: 0.06
Nodes (32): decideFeedbackCase(), FeedbackCaseDetail, FeedbackCaseSummary, FeedbackPanelSettings, fetchFeedbackCaseDetail(), fetchFeedbackCases(), fetchFeedbackPanelSettings(), updateFeedbackPanelSettings() (+24 more)

### Community 4 - "ServerEntry.tsx"
Cohesion: 0.09
Nodes (35): createEmbedMessage(), deleteEmbedTemplate(), EmbedFieldSpec, EmbedMessagePayload, EmbedSpec, EmbedTemplate, fetchEmbedMessage(), fetchEmbedTemplates() (+27 more)

### Community 5 - "devDependencies"
Cohesion: 0.04
Nodes (46): jsdom, oxlint, dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, tailwindcss (+38 more)

### Community 6 - "Lockdown.tsx"
Cohesion: 0.31
Nodes (7): activateLockdown(), deactivateLockdown(), fetchLockdownStatus(), fetchModerationLog(), LockdownPage(), Tab, TYPE_ICON

### Community 7 - "types.ts"
Cohesion: 0.08
Nodes (32): fetchPublicMafia(), MafiaPublicState, submitMafiaAction(), submitMafiaVote(), LanguageContextValue, activity, admin, auth (+24 more)

### Community 8 - "Docs.tsx"
Cohesion: 0.18
Nodes (15): react, DocsBanner(), DocNavItem, DocsSearch(), DocsSearchProps, DocsSidebar(), DocsSidebarProps, GROUP_ICONS (+7 more)

### Community 9 - "BracketDetail.tsx"
Cohesion: 0.07
Nodes (33): BracketDetail, BracketFormat, BracketMatch, BracketSummary, createBracket(), createEvent(), CreateEventSpec, deleteBracket() (+25 more)

### Community 10 - "Bunker.tsx"
Cohesion: 0.07
Nodes (43): applyBunkerAbility(), BunkerCardPools, BunkerCharacter, BunkerGameDetail, BunkerGameSummary, BunkerPlayerRef, BunkerSettings, deleteCardBg() (+35 more)

### Community 11 - "AutoMod.tsx"
Cohesion: 0.08
Nodes (31): AutomodFilter, AutomodPunishment, AutomodSettings, createEscalationRule(), deleteEscalationRule(), EscalationAction, EscalationRule, fetchAutomod() (+23 more)

### Community 12 - "compilerOptions"
Cohesion: 0.08
Nodes (23): DOM, src, vite/client, compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx (+15 more)

### Community 13 - "ModuleConfigPanel.tsx"
Cohesion: 0.18
Nodes (16): banMember(), createMemberWarn(), deleteWarn(), fetchMemberDetail(), fetchMemberWarns(), grantRole(), kickMember(), MemberDetail (+8 more)

### Community 14 - "Family.tsx"
Cohesion: 0.23
Nodes (11): createCustomCommand(), CustomCommandsSettings, deleteCustomCommand(), fetchCustomCommands(), previewTemplate(), setCustomCommandsEnabled(), updateCustomCommand(), CommandPreviewPage() (+3 more)

### Community 15 - "compilerOptions"
Cohesion: 0.10
Nodes (19): node, vite.config.ts, compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection (+11 more)

### Community 16 - "FeedbackCategories.tsx"
Cohesion: 0.06
Nodes (54): BirthdaysPayload, ChannelInfo, createFeedbackCategory(), createReactionRole(), CtdConfig, deleteBirthday(), deleteFeedbackCategory(), deleteReactionRole() (+46 more)

### Community 17 - "useT"
Cohesion: 0.20
Nodes (14): AuditEntry, AuditModerator, AuditPage, fetchAudit(), AuditPage(), csvEscape(), downloadAuditCsv(), EntryRow() (+6 more)

### Community 18 - "useLanguage"
Cohesion: 0.14
Nodes (9): fetchPublicLeaderboard(), loginUrl(), PublicLeaderboardEntry, PublicLayout(), LeaderboardPage(), MEDAL, PrivacyPage(), TABLE_ROW_KEYS (+1 more)

### Community 19 - "AuthContext.tsx"
Cohesion: 0.26
Nodes (10): fetchSuperAdminGuilds(), selectGuild(), SuperAdminGuild, App(), PublicLandingOrDashboard(), useAuth(), LandingPage(), AUTH_ERROR_KEYS (+2 more)

### Community 20 - "LanguageContext.tsx"
Cohesion: 0.15
Nodes (9): DashboardUser, ProtectedRoute(), AuthContext, AuthContextValue, AuthProvider(), fallbackValue, LanguageContext, LanguageProvider() (+1 more)

### Community 21 - "Fun.tsx"
Cohesion: 0.39
Nodes (7): fetchFunSettings(), fetchWordleSettings(), FunSettings, updateFunSettings(), updateWordleSettings(), WordleSettings, FunPage()

### Community 22 - "Members.tsx"
Cohesion: 0.24
Nodes (10): LanguageToggle(), useLanguage(), useT(), AccessDeniedPage(), NAV_GROUPS, NavGroup, Section, SidebarNav() (+2 more)

### Community 23 - "ServerSelect.tsx"
Cohesion: 0.18
Nodes (11): fetchMassAssignStatus(), fetchMembers(), MassAssignStatus, MassAssignTarget, MembersPage, startMassAssign(), MassAssignModal(), Props (+3 more)

### Community 24 - "Casino.tsx"
Cohesion: 0.14
Nodes (19): CasinoLeaderboardEntry, CasinoSettings, EconomySettings, EconomyTopEntry, EconomyWeeklyReportRow, fetchCasinoLeaderboard(), fetchCasinoSettings(), fetchEconomySettings() (+11 more)

### Community 25 - "Economy.tsx"
Cohesion: 0.29
Nodes (8): BotConfig, fetchConfig(), updateConfig(), sampleConfig, ModuleConfigPanel(), ModuleConfigPanelProps, EMPTY_BOT_CONFIG, ModuleConfigVariant

### Community 26 - "plugins"
Cohesion: 0.31
Nodes (9): announceBunkerAbility(), BUNKER_FIELD_KEYS, BunkerFieldKey, BunkerPublicState, fetchPublicBunker(), revealBunkerFields(), submitBunkerVote(), PublicBunkerActionPage() (+1 more)

### Community 27 - "VoiceStats.tsx"
Cohesion: 0.28
Nodes (6): fetchVoiceStats(), VoiceStats, formatVoiceDuration(), PERIODS, VoiceStatsPage(), WEEKDAY_KEYS

### Community 28 - "DashboardShell.tsx"
Cohesion: 0.24
Nodes (6): AccountLink(), FeatureDef, FEATURES, FeatureSection(), GhostButton(), isSpaPath()

### Community 29 - "Login.tsx"
Cohesion: 0.22
Nodes (8): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, typescript, warn

### Community 35 - "Toggle.tsx"
Cohesion: 0.27
Nodes (7): fetchServerLog(), ServerLogEventConfig, updateServerLog(), Card(), CardProps, NotFoundPage(), ServerLogPage()

### Community 36 - "FeedbackCaseDetailPanel.tsx"
Cohesion: 0.29
Nodes (7): GiveawayOverview, LockdownStatus, ModerationLogEntry, SetupHealth, HomePage(), modlogLabel(), TYPE_ICON

### Community 37 - "Home.tsx"
Cohesion: 0.60
Nodes (4): AntiRaidSettings, fetchAntiRaidSettings(), updateAntiRaidSettings(), AntiRaidPage()

### Community 38 - "Card.tsx"
Cohesion: 0.60
Nodes (4): fetchSpamSettings(), SpamSettings, updateSpamSettings(), AntiSpamPage()

### Community 39 - "Mafia.tsx"
Cohesion: 0.25
Nodes (8): fetchMafiaGames(), fetchMafiaSettings(), MafiaGameSummary, MafiaSettings, updateMafiaSettings(), MafiaPage(), Tab, emptySettings

### Community 40 - "AntiRaid.tsx"
Cohesion: 0.21
Nodes (11): closeEvent(), deleteEvent(), EventDetail, EventParticipantTeamCode, EventSummary, fetchEventDetail(), notifyEventParticipants(), EventDetailPanel() (+3 more)

### Community 41 - "PublicMafiaAction.tsx"
Cohesion: 0.27
Nodes (9): createDailyTopic(), DailyTopicSettings, deleteDailyTopic(), fetchDailyTopic(), postDailyTopicNow(), updateDailyTopic(), updateDailyTopicSettings(), DailyTopicPage() (+1 more)

### Community 42 - "Supply.tsx"
Cohesion: 0.29
Nodes (8): cancelSupply(), closeSupply(), createSupply(), fetchSupplyOverview(), Supply, SupplyOverview, SupplyPage(), Tab

### Community 43 - "formatApiError"
Cohesion: 0.60
Nodes (4): deleteTimedRole(), fetchTimedRoles(), TimedRoleEntry, TimedRolesPage()

### Community 44 - "ServerSettings.tsx"
Cohesion: 0.28
Nodes (14): apiFetch(), fetchLanguage(), fetchOwnerAlerts(), fetchSetupHealth(), fetchTimezone(), OwnerAlertsSettings, ServerLanguage, testOwnerAlerts() (+6 more)

### Community 45 - "Giveaways.tsx"
Cohesion: 0.23
Nodes (9): createGiveaway(), endGiveaway(), fetchGiveawayOverview(), Giveaway, rerollGiveaway(), Modal(), ModalProps, SIZE_CLASS (+1 more)

### Community 46 - "Streams.tsx"
Cohesion: 0.36
Nodes (7): createStreamSubscription(), deleteStreamSubscription(), fetchStreams(), StreamSubscription, testStreamSubscription(), updateStreamSubscription(), StreamsPage()

### Community 47 - "ServerSelect.tsx"
Cohesion: 0.27
Nodes (9): fetchCurrentUser(), fetchInviteUrl(), fetchManageableGuilds(), logout(), ManageableGuild, isForbiddenError(), DashboardShell(), guildIconUrl() (+1 more)

### Community 48 - "ScheduledMessages.tsx"
Cohesion: 0.36
Nodes (9): createScheduledMessage(), deleteScheduledMessage(), fetchScheduledMessages(), jsonInit(), ScheduledMessagesSettings, setScheduledMessagesEnabled(), updateEscalationRule(), updateScheduledMessage() (+1 more)

### Community 49 - "StickyMessages.tsx"
Cohesion: 0.24
Nodes (10): deleteSticky(), fetchSticky(), setStickyEnabled(), StickySettings, testSticky(), upsertSticky(), MessagesPage(), MessagesTab (+2 more)

### Community 50 - "Toggle.tsx"
Cohesion: 0.16
Nodes (15): fetchNewsSettings(), fetchVerificationSettings(), NewsSettings, TemplatePreviewResult, updateNewsSettings(), updateVerificationSettings(), VerificationSettings, Button() (+7 more)

### Community 51 - "VoiceRooms.tsx"
Cohesion: 0.43
Nodes (6): deleteVoiceRoom(), fetchVoiceRooms(), publishVoicePanel(), VoiceRoom, Tab, VoiceRoomsPage()

### Community 52 - "Polls.tsx"
Cohesion: 0.23
Nodes (8): ApiError, endPoll(), fetchPolls(), PollEntry, API_ERROR_KEYS, formatApiError(), Translate, PollsPage()

### Community 53 - "Tempban.tsx"
Cohesion: 0.60
Nodes (4): fetchTempbanSettings(), TempbanSettings, updateTempbanSettings(), TempbanPage()

## Knowledge Gaps
- **220 isolated node(s):** `$schema`, `typescript`, `oxc`, `react/rules-of-hooks`, `warn` (+215 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `useT()` connect `Members.tsx` to `apiFetch`, `renderWithLanguage.tsx`, `ServerEntry.tsx`, `Lockdown.tsx`, `BracketDetail.tsx`, `Bunker.tsx`, `AutoMod.tsx`, `ModuleConfigPanel.tsx`, `Family.tsx`, `FeedbackCategories.tsx`, `useT`, `useLanguage`, `AuthContext.tsx`, `LanguageContext.tsx`, `Fun.tsx`, `ServerSelect.tsx`, `Casino.tsx`, `Economy.tsx`, `VoiceStats.tsx`, `DashboardShell.tsx`, `Toggle.tsx`, `FeedbackCaseDetailPanel.tsx`, `Home.tsx`, `Card.tsx`, `Mafia.tsx`, `AntiRaid.tsx`, `PublicMafiaAction.tsx`, `Supply.tsx`, `formatApiError`, `ServerSettings.tsx`, `Giveaways.tsx`, `Streams.tsx`, `ServerSelect.tsx`, `ScheduledMessages.tsx`, `StickyMessages.tsx`, `Toggle.tsx`, `VoiceRooms.tsx`, `Polls.tsx`, `Tempban.tsx`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `react` connect `Docs.tsx` to `react`, `apiFetch`, `renderWithLanguage.tsx`, `ServerEntry.tsx`, `Lockdown.tsx`, `types.ts`, `BracketDetail.tsx`, `Bunker.tsx`, `AutoMod.tsx`, `ModuleConfigPanel.tsx`, `Family.tsx`, `FeedbackCategories.tsx`, `useT`, `useLanguage`, `AuthContext.tsx`, `LanguageContext.tsx`, `Fun.tsx`, `Members.tsx`, `ServerSelect.tsx`, `Casino.tsx`, `Economy.tsx`, `plugins`, `VoiceStats.tsx`, `DashboardShell.tsx`, `Login.tsx`, `Toggle.tsx`, `FeedbackCaseDetailPanel.tsx`, `Home.tsx`, `Card.tsx`, `Mafia.tsx`, `AntiRaid.tsx`, `PublicMafiaAction.tsx`, `Supply.tsx`, `formatApiError`, `ServerSettings.tsx`, `Giveaways.tsx`, `Streams.tsx`, `ServerSelect.tsx`, `ScheduledMessages.tsx`, `StickyMessages.tsx`, `Toggle.tsx`, `VoiceRooms.tsx`, `Polls.tsx`, `Tempban.tsx`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Why does `apiFetch()` connect `ServerSettings.tsx` to `apiFetch`, `client.ts`, `renderWithLanguage.tsx`, `ServerEntry.tsx`, `Lockdown.tsx`, `types.ts`, `BracketDetail.tsx`, `Bunker.tsx`, `AutoMod.tsx`, `ModuleConfigPanel.tsx`, `Family.tsx`, `FeedbackCategories.tsx`, `useT`, `useLanguage`, `AuthContext.tsx`, `Fun.tsx`, `ServerSelect.tsx`, `Casino.tsx`, `Economy.tsx`, `plugins`, `VoiceStats.tsx`, `Toggle.tsx`, `Home.tsx`, `Card.tsx`, `Mafia.tsx`, `AntiRaid.tsx`, `PublicMafiaAction.tsx`, `Supply.tsx`, `formatApiError`, `Giveaways.tsx`, `Streams.tsx`, `ScheduledMessages.tsx`, `StickyMessages.tsx`, `Toggle.tsx`, `VoiceRooms.tsx`, `Polls.tsx`, `Tempban.tsx`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **What connects `$schema`, `typescript`, `oxc` to the rest of the system?**
  _220 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `apiFetch` be split into smaller, more focused modules?**
  _Cohesion score 0.12648221343873517 - nodes in this community are weakly interconnected._
- **Should `client.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.037037037037037035 - nodes in this community are weakly interconnected._
- **Should `renderWithLanguage.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.05656565656565657 - nodes in this community are weakly interconnected._