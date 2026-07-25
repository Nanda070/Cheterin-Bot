# Graph Report - frontend  (2026-07-24)

## Corpus Check
- 195 files · ~200,163 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1027 nodes · 3468 edges · 46 communities (44 shown, 2 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `03302ef2`
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
- AntiRaid.tsx
- PublicMafiaAction.tsx
- Supply.tsx
- ServerSettings.tsx
- Streams.tsx
- ServerSelect.tsx
- ScheduledMessages.tsx
- StickyMessages.tsx
- Toggle.tsx

## God Nodes (most connected - your core abstractions)
1. `apiFetch()` - 173 edges
2. `useT()` - 155 edges
3. `jsonInit()` - 99 edges
4. `formatApiError()` - 93 edges
5. `react` - 84 edges
6. `Button()` - 53 edges
7. `Card()` - 52 edges
8. `fetchChannels()` - 50 edges
9. `Select()` - 37 edges
10. `fetchRoles()` - 31 edges

## Surprising Connections (you probably didn't know these)
- `WhatsNewBullets()` --calls--> `useT()`  [EXTRACTED]
  src/components/WhatsNew.tsx → src/context/LanguageContext.tsx
- `FilterExtraFields()` --calls--> `useT()`  [EXTRACTED]
  src/pages/AutoMod.tsx → src/context/LanguageContext.tsx
- `FeatureSection()` --calls--> `useT()`  [EXTRACTED]
  src/pages/Landing.tsx → src/context/LanguageContext.tsx
- `ServerSelectPage()` --calls--> `logout()`  [EXTRACTED]
  src/pages/ServerSelect.tsx → src/api/client.ts
- `LandingPage()` --calls--> `loginUrl()`  [EXTRACTED]
  src/pages/Landing.tsx → src/api/client.ts

## Import Cycles
- None detected.

## Communities (46 total, 2 thin omitted)

### Community 0 - "react"
Cohesion: 0.17
Nodes (14): createEmbedMessage(), deleteEmbedTemplate(), EmbedMessagePayload, EmbedTemplate, fetchEmbedMessage(), fetchEmbedTemplates(), saveEmbedTemplate(), updateEmbedMessage() (+6 more)

### Community 1 - "apiFetch"
Cohesion: 0.13
Nodes (19): decideFamilyTicket(), deleteFamilyBirthday(), FamilyBirthday, FamilyRosterGroup, FamilySettings, FamilyTicket, FamilyTicketsPage, FamilyTicketStatus (+11 more)

### Community 2 - "client.ts"
Cohesion: 0.03
Nodes (74): AntiRaidSettings, AutoRolesSettings, BirthdayEntry, BracketStandingsRow, BunkerAbilityAnnouncement, BunkerAdditionalInfo, BunkerAgeInfo, BunkerBodyType (+66 more)

### Community 3 - "renderWithLanguage.tsx"
Cohesion: 0.06
Nodes (30): fetchFeedbackCases(), fetchMafiaGames(), fetchMafiaSettings(), MafiaGameSummary, MafiaSettings, updateMafiaSettings(), baseGameSummary, emptySettings (+22 more)

### Community 4 - "ServerEntry.tsx"
Cohesion: 0.09
Nodes (30): BotConfig, EmbedFieldSpec, EmbedSpec, fetchAutoRoles(), fetchConfig(), fetchWelcomeSettings(), testWelcomeSettings(), updateAutoRoles() (+22 more)

### Community 5 - "devDependencies"
Cohesion: 0.04
Nodes (46): jsdom, oxlint, dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, tailwindcss (+38 more)

### Community 6 - "Lockdown.tsx"
Cohesion: 0.20
Nodes (13): createFeedbackCategory(), deleteFeedbackCategory(), FeedbackCategoryFieldSpec, FeedbackCategorySpec, fetchFeedbackCategories(), publishFeedbackPanel(), updateFeedbackCategory(), sampleSpec (+5 more)

### Community 7 - "types.ts"
Cohesion: 0.06
Nodes (43): announceBunkerAbility(), BUNKER_FIELD_KEYS, BunkerFieldKey, BunkerPublicState, fetchPublicBunker(), fetchPublicMafia(), MafiaPublicState, revealBunkerFields() (+35 more)

### Community 8 - "Docs.tsx"
Cohesion: 0.11
Nodes (28): DocsBanner(), DocNavItem, DocsSearch(), DocsSearchProps, DocsSidebar(), DocsSidebarProps, GROUP_ICONS, DocsToc() (+20 more)

### Community 9 - "BracketDetail.tsx"
Cohesion: 0.13
Nodes (14): BracketDetail, BracketMatch, deleteBracket(), disableBracketShare(), enableBracketShare(), fetchBracketDetail(), fetchPublicBracket(), setBracketMatchWinner() (+6 more)

### Community 10 - "Bunker.tsx"
Cohesion: 0.12
Nodes (29): applyBunkerAbility(), BunkerCardPools, BunkerCharacter, BunkerGameDetail, BunkerGameSummary, BunkerPlayerRef, BunkerSettings, fetchBunkerCardPools() (+21 more)

### Community 11 - "AutoMod.tsx"
Cohesion: 0.08
Nodes (31): AutomodFilter, AutomodPunishment, AutomodSettings, createEscalationRule(), deleteEscalationRule(), EscalationAction, EscalationRule, fetchAutomod() (+23 more)

### Community 12 - "compilerOptions"
Cohesion: 0.08
Nodes (23): DOM, src, vite/client, compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx (+15 more)

### Community 13 - "ModuleConfigPanel.tsx"
Cohesion: 0.23
Nodes (15): banMember(), createMemberWarn(), deleteWarn(), fetchMemberDetail(), fetchMemberWarns(), grantRole(), jsonInit(), kickMember() (+7 more)

### Community 14 - "Family.tsx"
Cohesion: 0.29
Nodes (9): createCustomCommand(), CustomCommandsSettings, deleteCustomCommand(), fetchCustomCommands(), setCustomCommandsEnabled(), updateCustomCommand(), CustomCommandsPage(), parseTab() (+1 more)

### Community 15 - "compilerOptions"
Cohesion: 0.10
Nodes (19): node, vite.config.ts, compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection (+11 more)

### Community 16 - "FeedbackCategories.tsx"
Cohesion: 0.22
Nodes (14): ChannelInfo, createReactionRole(), CustomEmoji, deleteReactionRole(), fetchChannels(), fetchEmojis(), fetchReactionRoles(), ReactionRoleEntry (+6 more)

### Community 17 - "useT"
Cohesion: 0.20
Nodes (14): AuditEntry, AuditModerator, AuditPage, fetchAudit(), AuditPage(), csvEscape(), downloadAuditCsv(), EntryRow() (+6 more)

### Community 18 - "useLanguage"
Cohesion: 0.16
Nodes (9): loginUrl(), LanguageToggle(), PublicLayout(), useLanguage(), AccessDeniedPage(), HeadingAnchor(), PrivacyPage(), TABLE_ROW_KEYS (+1 more)

### Community 19 - "AuthContext.tsx"
Cohesion: 0.31
Nodes (7): App(), ProtectedRoute(), PublicLandingOrDashboard(), useAuth(), LandingPage(), AUTH_ERROR_KEYS, LoginPage()

### Community 20 - "LanguageContext.tsx"
Cohesion: 0.18
Nodes (7): fallbackValue, LanguageContext, LanguageProvider(), readStoredLang(), MembersPage(), parseMembersTab(), NotFoundPage()

### Community 21 - "Fun.tsx"
Cohesion: 0.21
Nodes (9): DashboardUser, fetchCurrentUser(), fetchSuperAdminGuilds(), selectGuild(), SuperAdminGuild, AuthContext, AuthContextValue, AuthProvider() (+1 more)

### Community 22 - "Members.tsx"
Cohesion: 0.21
Nodes (9): logout(), Dropdown(), DropdownItem(), DropdownProps, DashboardShell(), NAV_GROUPS, NavGroup, Section (+1 more)

### Community 23 - "ServerSelect.tsx"
Cohesion: 0.22
Nodes (14): deleteCardBg(), fetchXpLeaderboard(), fetchXpOverview(), resetAllXp(), resetMemberXp(), setMemberXp(), updateXpSettings(), uploadCardBg() (+6 more)

### Community 24 - "Casino.tsx"
Cohesion: 0.11
Nodes (22): CasinoLeaderboardEntry, CasinoSettings, EconomySettings, EconomyTopEntry, EconomyWeeklyReportRow, fetchCasinoLeaderboard(), fetchCasinoSettings(), fetchEconomySettings() (+14 more)

### Community 25 - "Economy.tsx"
Cohesion: 0.31
Nodes (9): BirthdaysPayload, deleteBirthday(), fetchBirthdays(), RoleChip, RoleInfo, setBirthday(), testBirthdayAnnounce(), updateBirthdaySettings() (+1 more)

### Community 26 - "plugins"
Cohesion: 0.43
Nodes (6): CtdConfig, fetchCtdConfig(), fetchRoles(), updateCtdConfig(), CtdPage(), EMPTY

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
Cohesion: 0.50
Nodes (4): fetchPublicLeaderboard(), PublicLeaderboardEntry, LeaderboardPage(), MEDAL

### Community 36 - "FeedbackCaseDetailPanel.tsx"
Cohesion: 0.11
Nodes (24): createGiveaway(), endGiveaway(), fetchGiveawayOverview(), fetchLockdownStatus(), fetchMembers(), fetchModerationLog(), Giveaway, GiveawayOverview (+16 more)

### Community 40 - "AntiRaid.tsx"
Cohesion: 0.10
Nodes (28): BracketFormat, BracketSummary, closeEvent(), createBracket(), createEvent(), CreateEventSpec, deleteEvent(), EventDetail (+20 more)

### Community 41 - "PublicMafiaAction.tsx"
Cohesion: 0.39
Nodes (8): createDailyTopic(), DailyTopicSettings, deleteDailyTopic(), fetchDailyTopic(), postDailyTopicNow(), updateDailyTopic(), updateDailyTopicSettings(), DailyTopicPage()

### Community 42 - "Supply.tsx"
Cohesion: 0.33
Nodes (9): activateLockdown(), apiFetch(), cancelSupply(), closeSupply(), createSupply(), deactivateLockdown(), fetchSupplyOverview(), LockdownPage() (+1 more)

### Community 44 - "ServerSettings.tsx"
Cohesion: 0.23
Nodes (13): fetchLanguage(), fetchOwnerAlerts(), fetchSetupHealth(), fetchTimezone(), OwnerAlertsSettings, ServerLanguage, testOwnerAlerts(), updateLanguage() (+5 more)

### Community 46 - "Streams.tsx"
Cohesion: 0.36
Nodes (7): createStreamSubscription(), deleteStreamSubscription(), fetchStreams(), StreamSubscription, testStreamSubscription(), updateStreamSubscription(), StreamsPage()

### Community 47 - "ServerSelect.tsx"
Cohesion: 0.31
Nodes (6): fetchInviteUrl(), fetchManageableGuilds(), ManageableGuild, isForbiddenError(), guildIconUrl(), ServerSelectPage()

### Community 48 - "ScheduledMessages.tsx"
Cohesion: 0.24
Nodes (10): createScheduledMessage(), deleteScheduledMessage(), fetchScheduledMessages(), ScheduledMessagesSettings, setScheduledMessagesEnabled(), updateScheduledMessage(), MessagesPage(), MessagesTab (+2 more)

### Community 49 - "StickyMessages.tsx"
Cohesion: 0.24
Nodes (10): deleteSticky(), fetchSticky(), setStickyEnabled(), StickySettings, testSticky(), upsertSticky(), Modal(), ModalProps (+2 more)

### Community 50 - "Toggle.tsx"
Cohesion: 0.06
Nodes (79): react, ApiError, decideFeedbackCase(), deleteTimedRole(), deleteVoiceRoom(), endPoll(), fetchAntiRaidSettings(), fetchFeedbackCaseDetail() (+71 more)

## Knowledge Gaps
- **219 isolated node(s):** `$schema`, `typescript`, `oxc`, `react/rules-of-hooks`, `warn` (+214 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `react` connect `Toggle.tsx` to `react`, `apiFetch`, `renderWithLanguage.tsx`, `ServerEntry.tsx`, `Lockdown.tsx`, `types.ts`, `Docs.tsx`, `BracketDetail.tsx`, `Bunker.tsx`, `AutoMod.tsx`, `ModuleConfigPanel.tsx`, `Family.tsx`, `FeedbackCategories.tsx`, `useT`, `useLanguage`, `AuthContext.tsx`, `LanguageContext.tsx`, `Fun.tsx`, `Members.tsx`, `ServerSelect.tsx`, `Casino.tsx`, `Economy.tsx`, `plugins`, `VoiceStats.tsx`, `DashboardShell.tsx`, `Login.tsx`, `Toggle.tsx`, `FeedbackCaseDetailPanel.tsx`, `AntiRaid.tsx`, `PublicMafiaAction.tsx`, `ServerSettings.tsx`, `Streams.tsx`, `ServerSelect.tsx`, `ScheduledMessages.tsx`, `StickyMessages.tsx`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `useT()` connect `Toggle.tsx` to `react`, `apiFetch`, `renderWithLanguage.tsx`, `ServerEntry.tsx`, `Lockdown.tsx`, `BracketDetail.tsx`, `Bunker.tsx`, `AutoMod.tsx`, `ModuleConfigPanel.tsx`, `Family.tsx`, `FeedbackCategories.tsx`, `useT`, `useLanguage`, `AuthContext.tsx`, `LanguageContext.tsx`, `Fun.tsx`, `Members.tsx`, `ServerSelect.tsx`, `Casino.tsx`, `Economy.tsx`, `plugins`, `VoiceStats.tsx`, `DashboardShell.tsx`, `Toggle.tsx`, `FeedbackCaseDetailPanel.tsx`, `AntiRaid.tsx`, `PublicMafiaAction.tsx`, `Supply.tsx`, `ServerSettings.tsx`, `Streams.tsx`, `ServerSelect.tsx`, `ScheduledMessages.tsx`, `StickyMessages.tsx`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `apiFetch()` connect `Supply.tsx` to `react`, `apiFetch`, `client.ts`, `renderWithLanguage.tsx`, `ServerEntry.tsx`, `Lockdown.tsx`, `types.ts`, `BracketDetail.tsx`, `Bunker.tsx`, `AutoMod.tsx`, `ModuleConfigPanel.tsx`, `Family.tsx`, `FeedbackCategories.tsx`, `useT`, `Fun.tsx`, `ServerSelect.tsx`, `Casino.tsx`, `Economy.tsx`, `plugins`, `VoiceStats.tsx`, `Toggle.tsx`, `FeedbackCaseDetailPanel.tsx`, `AntiRaid.tsx`, `PublicMafiaAction.tsx`, `ServerSettings.tsx`, `Streams.tsx`, `ScheduledMessages.tsx`, `StickyMessages.tsx`, `Toggle.tsx`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **What connects `$schema`, `typescript`, `oxc` to the rest of the system?**
  _219 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `apiFetch` be split into smaller, more focused modules?**
  _Cohesion score 0.1341991341991342 - nodes in this community are weakly interconnected._
- **Should `client.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.02738738738738739 - nodes in this community are weakly interconnected._
- **Should `renderWithLanguage.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.05520614954577219 - nodes in this community are weakly interconnected._