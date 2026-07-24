# Graph Report - frontend  (2026-07-23)

## Corpus Check
- 184 files · ~123,713 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 981 nodes · 3281 edges · 56 communities (52 shown, 4 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `834ffeeb`
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
- Messages.tsx
- MessageBuilder.tsx

## God Nodes (most connected - your core abstractions)
1. `apiFetch()` - 166 edges
2. `useT()` - 140 edges
3. `jsonInit()` - 97 edges
4. `formatApiError()` - 91 edges
5. `react` - 80 edges
6. `Button()` - 51 edges
7. `Card()` - 51 edges
8. `fetchChannels()` - 50 edges
9. `Select()` - 34 edges
10. `fetchRoles()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `HeadingAnchor()` --calls--> `useLanguage()`  [EXTRACTED]
  src/pages/docs/docPrimitives.tsx → src/context/LanguageContext.tsx
- `FilterExtraFields()` --calls--> `useT()`  [EXTRACTED]
  src/pages/AutoMod.tsx → src/context/LanguageContext.tsx
- `renderPage()` --calls--> `renderWithI18n()`  [EXTRACTED]
  src/pages/SuperAdmin.test.tsx → src/test/renderWithI18n.tsx
- `AuthProvider()` --calls--> `fetchCurrentUser()`  [EXTRACTED]
  src/context/AuthContext.tsx → src/api/client.ts
- `ServerSelectPage()` --calls--> `logout()`  [EXTRACTED]
  src/pages/ServerSelect.tsx → src/api/client.ts

## Import Cycles
- None detected.

## Communities (56 total, 4 thin omitted)

### Community 0 - "react"
Cohesion: 0.17
Nodes (17): ChannelInfo, createReactionRole(), CustomEmoji, deleteReactionRole(), fetchChannels(), fetchInvites(), fetchReactionRoles(), InvitesSettings (+9 more)

### Community 1 - "apiFetch"
Cohesion: 0.16
Nodes (18): decideFamilyTicket(), deleteFamilyBirthday(), FamilyBirthday, FamilyRosterGroup, FamilySettings, FamilyTicket, FamilyTicketsPage, FamilyTicketStatus (+10 more)

### Community 2 - "client.ts"
Cohesion: 0.04
Nodes (55): AutoRolesSettings, BirthdayEntry, BracketStandingsRow, BunkerAbilityAnnouncement, BunkerAdditionalInfo, BunkerAgeInfo, BunkerBodyType, BunkerGamePhase (+47 more)

### Community 3 - "renderWithLanguage.tsx"
Cohesion: 0.06
Nodes (30): decideFeedbackCase(), FeedbackCaseDetail, FeedbackCaseSummary, fetchFeedbackCaseDetail(), fetchFeedbackCases(), fetchPublicMafia(), MafiaPublicState, submitMafiaAction() (+22 more)

### Community 4 - "ServerEntry.tsx"
Cohesion: 0.06
Nodes (50): BotConfig, deleteCardBg(), EmbedFieldSpec, EmbedSpec, FeedbackPanelSettings, fetchConfig(), fetchFeedbackPanelSettings(), fetchWelcomeSettings() (+42 more)

### Community 5 - "devDependencies"
Cohesion: 0.04
Nodes (46): jsdom, oxlint, dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, tailwindcss (+38 more)

### Community 6 - "Lockdown.tsx"
Cohesion: 0.11
Nodes (21): activateLockdown(), AntiRaidSettings, deactivateLockdown(), fetchAntiRaidSettings(), fetchLockdownStatus(), fetchMembers(), fetchModerationLog(), LockdownStatus (+13 more)

### Community 7 - "types.ts"
Cohesion: 0.08
Nodes (31): announceBunkerAbility(), BUNKER_FIELD_KEYS, BunkerFieldKey, BunkerPublicState, fetchPublicBunker(), revealBunkerFields(), submitBunkerVote(), activity (+23 more)

### Community 8 - "Docs.tsx"
Cohesion: 0.08
Nodes (38): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, react, typescript (+30 more)

### Community 9 - "BracketDetail.tsx"
Cohesion: 0.13
Nodes (14): BracketDetail, BracketMatch, deleteBracket(), disableBracketShare(), enableBracketShare(), fetchBracketDetail(), fetchPublicBracket(), setBracketMatchWinner() (+6 more)

### Community 10 - "Bunker.tsx"
Cohesion: 0.11
Nodes (27): applyBunkerAbility(), BunkerCardPools, BunkerCharacter, BunkerGameDetail, BunkerGameSummary, BunkerPlayerRef, BunkerSettings, fetchBunkerCardPools() (+19 more)

### Community 11 - "AutoMod.tsx"
Cohesion: 0.11
Nodes (26): AutomodFilter, AutomodPunishment, AutomodSettings, createEscalationRule(), deleteEscalationRule(), EscalationAction, EscalationRule, fetchAutomod() (+18 more)

### Community 12 - "compilerOptions"
Cohesion: 0.08
Nodes (23): DOM, src, vite/client, compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx (+15 more)

### Community 13 - "ModuleConfigPanel.tsx"
Cohesion: 0.23
Nodes (15): banMember(), createMemberWarn(), deleteWarn(), fetchMemberDetail(), fetchMemberWarns(), grantRole(), jsonInit(), kickMember() (+7 more)

### Community 14 - "Family.tsx"
Cohesion: 0.19
Nodes (12): createCustomCommand(), CustomCommandsSettings, deleteCustomCommand(), fetchCustomCommands(), setCustomCommandsEnabled(), updateCustomCommand(), Modal(), ModalProps (+4 more)

### Community 15 - "compilerOptions"
Cohesion: 0.10
Nodes (19): node, vite.config.ts, compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection (+11 more)

### Community 16 - "FeedbackCategories.tsx"
Cohesion: 0.05
Nodes (49): ApiError, createEmbedMessage(), createFeedbackCategory(), CtdConfig, deleteEmbedTemplate(), deleteFeedbackCategory(), EmbedMessagePayload, EmbedTemplate (+41 more)

### Community 17 - "useT"
Cohesion: 0.20
Nodes (13): AuditEntry, AuditModerator, AuditPage, fetchAudit(), csvEscape(), downloadAuditCsv(), EntryRow(), formatWhen() (+5 more)

### Community 18 - "useLanguage"
Cohesion: 0.20
Nodes (6): App(), useLanguage(), AuditPage(), PrivacyPage(), TABLE_ROW_KEYS, TermsPage()

### Community 19 - "AuthContext.tsx"
Cohesion: 0.23
Nodes (11): DashboardUser, fetchSuperAdminGuilds(), selectGuild(), SuperAdminGuild, ProtectedRoute(), AuthContext, AuthContextValue, AuthProvider() (+3 more)

### Community 20 - "LanguageContext.tsx"
Cohesion: 0.15
Nodes (10): MembersPage, fallbackValue, LanguageContext, LanguageContextValue, LanguageProvider(), readStoredLang(), Lang, MembersPage() (+2 more)

### Community 21 - "Fun.tsx"
Cohesion: 0.24
Nodes (9): fetchFunSettings(), fetchWordleSettings(), FunSettings, updateFunSettings(), updateWordleSettings(), WordleSettings, FunPage(), emptySettings (+1 more)

### Community 22 - "Members.tsx"
Cohesion: 0.25
Nodes (11): fetchPublicLeaderboard(), loginUrl(), LanguageToggle(), PublicLayout(), useT(), AccessDeniedPage(), LeaderboardPage(), MEDAL (+3 more)

### Community 23 - "ServerSelect.tsx"
Cohesion: 0.60
Nodes (4): fetchServerLog(), ServerLogEventConfig, updateServerLog(), ServerLogPage()

### Community 24 - "Casino.tsx"
Cohesion: 0.31
Nodes (9): CasinoLeaderboardEntry, CasinoSettings, fetchCasinoLeaderboard(), fetchCasinoSettings(), fetchEconomySettings(), updateCasinoSettings(), updateEconomySettings(), CasinoPage() (+1 more)

### Community 25 - "Economy.tsx"
Cohesion: 0.29
Nodes (9): EconomySettings, EconomyTopEntry, EconomyWeeklyReportRow, fetchEconomyTop(), fetchEconomyWeeklyReport(), resetAllEconomyBalances(), setEconomyBalance(), EconomyPage() (+1 more)

### Community 26 - "plugins"
Cohesion: 0.20
Nodes (11): BracketFormat, BracketSummary, createBracket(), EventDetail, EventSummary, fetchBrackets(), fetchEventEntries(), BracketsPage() (+3 more)

### Community 27 - "VoiceStats.tsx"
Cohesion: 0.29
Nodes (5): fetchVoiceStats(), VoiceStats, PERIODS, VoiceStatsPage(), WEEKDAY_KEYS

### Community 28 - "DashboardShell.tsx"
Cohesion: 0.19
Nodes (10): fetchCurrentUser(), logout(), Dropdown(), DropdownItem(), DropdownProps, DashboardShell(), NAV_GROUPS, NavGroup (+2 more)

### Community 35 - "Toggle.tsx"
Cohesion: 0.27
Nodes (7): fetchNewsSettings(), NewsSettings, updateNewsSettings(), Card(), CardProps, NewsPage(), NotFoundPage()

### Community 36 - "FeedbackCaseDetailPanel.tsx"
Cohesion: 0.23
Nodes (10): BirthdaysPayload, deleteBirthday(), fetchBirthdays(), setBirthday(), updateBirthdaySettings(), ChipPickerProps, Option, Select() (+2 more)

### Community 37 - "Home.tsx"
Cohesion: 0.26
Nodes (10): createEvent(), CreateEventSpec, fetchEvents(), buildEventEmbedPreview(), emptyCreateSpec(), EventsPage(), EventsTab, modeLabel() (+2 more)

### Community 38 - "Card.tsx"
Cohesion: 0.28
Nodes (7): fetchSpamSettings(), SpamSettings, updateSpamSettings(), ButtonProps, Variant, VARIANT_CLASSES, AntiSpamPage()

### Community 39 - "Mafia.tsx"
Cohesion: 0.25
Nodes (8): fetchMafiaGames(), fetchMafiaSettings(), MafiaGameSummary, MafiaSettings, updateMafiaSettings(), MafiaPage(), Tab, emptySettings

### Community 40 - "AntiRaid.tsx"
Cohesion: 0.26
Nodes (9): closeEvent(), deleteEvent(), EventParticipantTeamCode, fetchEventDetail(), notifyEventParticipants(), EventDetailPanel(), Props, pollDetail (+1 more)

### Community 41 - "PublicMafiaAction.tsx"
Cohesion: 0.44
Nodes (9): apiFetch(), createDailyTopic(), DailyTopicSettings, deleteDailyTopic(), fetchDailyTopic(), postDailyTopicNow(), updateDailyTopic(), updateDailyTopicSettings() (+1 more)

### Community 42 - "Supply.tsx"
Cohesion: 0.29
Nodes (8): cancelSupply(), closeSupply(), createSupply(), fetchSupplyOverview(), Supply, SupplyOverview, SupplyPage(), Tab

### Community 43 - "formatApiError"
Cohesion: 0.31
Nodes (8): deleteTimedRole(), fetchTimedRoles(), previewTemplate(), TemplatePreviewResult, TimedRoleEntry, formatApiError(), CommandPreviewPage(), TimedRolesPage()

### Community 44 - "ServerSettings.tsx"
Cohesion: 0.29
Nodes (9): fetchLanguage(), fetchOwnerAlerts(), OwnerAlertsSettings, ServerLanguage, updateLanguage(), updateOwnerAlerts(), defaultAlerts, LANGUAGE_OPTIONS (+1 more)

### Community 45 - "Giveaways.tsx"
Cohesion: 0.33
Nodes (7): createGiveaway(), endGiveaway(), fetchGiveawayOverview(), Giveaway, GiveawayOverview, rerollGiveaway(), GiveawaysPage()

### Community 46 - "Streams.tsx"
Cohesion: 0.36
Nodes (7): createStreamSubscription(), deleteStreamSubscription(), fetchStreams(), StreamSubscription, testStreamSubscription(), updateStreamSubscription(), StreamsPage()

### Community 47 - "ServerSelect.tsx"
Cohesion: 0.36
Nodes (5): fetchInviteUrl(), fetchManageableGuilds(), isForbiddenError(), guildIconUrl(), ServerSelectPage()

### Community 48 - "ScheduledMessages.tsx"
Cohesion: 0.43
Nodes (7): createScheduledMessage(), deleteScheduledMessage(), fetchScheduledMessages(), ScheduledMessagesSettings, setScheduledMessagesEnabled(), updateScheduledMessage(), ScheduledMessagesPage()

### Community 49 - "StickyMessages.tsx"
Cohesion: 0.43
Nodes (7): deleteSticky(), fetchSticky(), setStickyEnabled(), StickySettings, testSticky(), upsertSticky(), StickyMessagesPage()

### Community 50 - "Toggle.tsx"
Cohesion: 0.36
Nodes (6): fetchVerificationSettings(), updateVerificationSettings(), VerificationSettings, Toggle(), ToggleProps, VerificationPage()

### Community 51 - "VoiceRooms.tsx"
Cohesion: 0.43
Nodes (6): deleteVoiceRoom(), fetchVoiceRooms(), publishVoicePanel(), VoiceRoom, Tab, VoiceRoomsPage()

### Community 52 - "Polls.tsx"
Cohesion: 0.60
Nodes (4): endPoll(), fetchPolls(), PollEntry, PollsPage()

### Community 53 - "Tempban.tsx"
Cohesion: 0.60
Nodes (4): fetchTempbanSettings(), TempbanSettings, updateTempbanSettings(), TempbanPage()

### Community 54 - "Messages.tsx"
Cohesion: 0.50
Nodes (3): MessagesPage(), MessagesTab, parseMessagesTab()

## Knowledge Gaps
- **218 isolated node(s):** `$schema`, `typescript`, `oxc`, `react/rules-of-hooks`, `warn` (+213 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `react` connect `Docs.tsx` to `react`, `apiFetch`, `renderWithLanguage.tsx`, `ServerEntry.tsx`, `Lockdown.tsx`, `types.ts`, `BracketDetail.tsx`, `Bunker.tsx`, `AutoMod.tsx`, `ModuleConfigPanel.tsx`, `Family.tsx`, `FeedbackCategories.tsx`, `useT`, `useLanguage`, `AuthContext.tsx`, `LanguageContext.tsx`, `Fun.tsx`, `Members.tsx`, `ServerSelect.tsx`, `Casino.tsx`, `Economy.tsx`, `plugins`, `VoiceStats.tsx`, `DashboardShell.tsx`, `Login.tsx`, `Toggle.tsx`, `FeedbackCaseDetailPanel.tsx`, `Home.tsx`, `Card.tsx`, `Mafia.tsx`, `AntiRaid.tsx`, `PublicMafiaAction.tsx`, `Supply.tsx`, `formatApiError`, `ServerSettings.tsx`, `Giveaways.tsx`, `Streams.tsx`, `ServerSelect.tsx`, `ScheduledMessages.tsx`, `StickyMessages.tsx`, `Toggle.tsx`, `VoiceRooms.tsx`, `Polls.tsx`, `Tempban.tsx`, `MessageBuilder.tsx`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `useT()` connect `Members.tsx` to `react`, `apiFetch`, `renderWithLanguage.tsx`, `ServerEntry.tsx`, `Lockdown.tsx`, `BracketDetail.tsx`, `Bunker.tsx`, `AutoMod.tsx`, `ModuleConfigPanel.tsx`, `Family.tsx`, `FeedbackCategories.tsx`, `useT`, `useLanguage`, `AuthContext.tsx`, `LanguageContext.tsx`, `Fun.tsx`, `ServerSelect.tsx`, `Casino.tsx`, `Economy.tsx`, `plugins`, `VoiceStats.tsx`, `DashboardShell.tsx`, `Login.tsx`, `Toggle.tsx`, `FeedbackCaseDetailPanel.tsx`, `Home.tsx`, `Card.tsx`, `Mafia.tsx`, `AntiRaid.tsx`, `PublicMafiaAction.tsx`, `Supply.tsx`, `formatApiError`, `ServerSettings.tsx`, `Giveaways.tsx`, `Streams.tsx`, `ServerSelect.tsx`, `ScheduledMessages.tsx`, `StickyMessages.tsx`, `Toggle.tsx`, `VoiceRooms.tsx`, `Polls.tsx`, `Tempban.tsx`, `Messages.tsx`, `MessageBuilder.tsx`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Why does `apiFetch()` connect `PublicMafiaAction.tsx` to `react`, `apiFetch`, `client.ts`, `renderWithLanguage.tsx`, `ServerEntry.tsx`, `Lockdown.tsx`, `types.ts`, `BracketDetail.tsx`, `Bunker.tsx`, `AutoMod.tsx`, `ModuleConfigPanel.tsx`, `Family.tsx`, `FeedbackCategories.tsx`, `useT`, `AuthContext.tsx`, `Fun.tsx`, `Members.tsx`, `ServerSelect.tsx`, `Casino.tsx`, `Economy.tsx`, `plugins`, `VoiceStats.tsx`, `Toggle.tsx`, `FeedbackCaseDetailPanel.tsx`, `Home.tsx`, `Card.tsx`, `Mafia.tsx`, `AntiRaid.tsx`, `Supply.tsx`, `formatApiError`, `ServerSettings.tsx`, `Giveaways.tsx`, `Streams.tsx`, `ScheduledMessages.tsx`, `StickyMessages.tsx`, `Toggle.tsx`, `VoiceRooms.tsx`, `Polls.tsx`, `Tempban.tsx`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **What connects `$schema`, `typescript`, `oxc` to the rest of the system?**
  _218 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `client.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.03636363636363636 - nodes in this community are weakly interconnected._
- **Should `renderWithLanguage.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.05878084179970972 - nodes in this community are weakly interconnected._
- **Should `ServerEntry.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.06041986687147977 - nodes in this community are weakly interconnected._