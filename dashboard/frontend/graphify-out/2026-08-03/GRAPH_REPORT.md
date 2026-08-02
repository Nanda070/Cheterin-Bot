# Graph Report - frontend  (2026-08-02)

## Corpus Check
- 208 files · ~220,183 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1131 nodes · 3806 edges · 61 communities (58 shown, 3 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `735ed236`
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
- FeedbackCaseDetailPanel.tsx
- Mafia.tsx
- useT
- AntiRaid.tsx
- PublicMafiaAction.tsx
- Supply.tsx
- Toggle.tsx
- ServerSettings.tsx
- EventDetailPanel.tsx
- Streams.tsx
- ServerSelect.tsx
- ScheduledMessages.tsx
- StickyMessages.tsx
- Toggle.tsx
- Credits.tsx
- Giveaways.tsx
- Fun.tsx
- Button.tsx
- AutoReactions.tsx
- ValChecker.tsx
- fetchProfileCardPreview
- Bunker.test.tsx
- MessageBuilder.tsx
- Fun.test.tsx

## God Nodes (most connected - your core abstractions)
1. `apiFetch()` - 192 edges
2. `useT()` - 164 edges
3. `jsonInit()` - 112 edges
4. `formatApiError()` - 101 edges
5. `react` - 89 edges
6. `fetchChannels()` - 58 edges
7. `Button()` - 57 edges
8. `Card()` - 54 edges
9. `Select()` - 40 edges
10. `Toggle()` - 33 edges

## Surprising Connections (you probably didn't know these)
- `WhatsNewBullets()` --calls--> `useT()`  [EXTRACTED]
  src/components/WhatsNew.tsx → src/context/LanguageContext.tsx
- `FilterExtraFields()` --calls--> `useT()`  [EXTRACTED]
  src/pages/AutoMod.tsx → src/context/LanguageContext.tsx
- `FeatureSection()` --calls--> `useT()`  [EXTRACTED]
  src/pages/Landing.tsx → src/context/LanguageContext.tsx
- `DashboardShell()` --calls--> `logout()`  [EXTRACTED]
  src/pages/DashboardShell.tsx → src/api/client.ts
- `LandingPage()` --calls--> `loginUrl()`  [EXTRACTED]
  src/pages/Landing.tsx → src/api/client.ts

## Import Cycles
- None detected.

## Communities (61 total, 3 thin omitted)

### Community 0 - "react"
Cohesion: 0.29
Nodes (5): createEmbedMessage(), EmbedMessagePayload, fetchEmbedMessage(), updateEmbedMessage(), samplePayload

### Community 1 - "apiFetch"
Cohesion: 0.13
Nodes (19): CustomEmoji, decideFamilyTicket(), deleteFamilyBirthday(), FamilyBirthday, FamilyRosterGroup, FamilySettings, FamilyTicket, FamilyTicketsPage (+11 more)

### Community 2 - "client.ts"
Cohesion: 0.03
Nodes (60): AutoRolesSettings, BirthdayEntry, BotProfileSettings, BracketStandingsRow, BunkerAbilityAnnouncement, BunkerAdditionalInfo, BunkerAgeInfo, BunkerBodyType (+52 more)

### Community 3 - "renderWithLanguage.tsx"
Cohesion: 0.21
Nodes (7): emptySettings, summary, baseState, renderAt(), baseState, renderAt(), renderWithLanguage()

### Community 4 - "ServerEntry.tsx"
Cohesion: 0.08
Nodes (34): BotConfig, deleteVoiceRoom(), fetchAutoRoles(), fetchConfig(), fetchVoiceRooms(), fetchWelcomeSettings(), MemberSummary, publishVoicePanel() (+26 more)

### Community 5 - "devDependencies"
Cohesion: 0.04
Nodes (46): jsdom, oxlint, dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, tailwindcss (+38 more)

### Community 6 - "Lockdown.tsx"
Cohesion: 0.07
Nodes (32): createFeedbackCategory(), deleteFeedbackCategory(), deleteTimedRole(), FeedbackCategoryFieldSpec, FeedbackCategorySpec, fetchFeedbackCategories(), fetchMassAssignStatus(), fetchMembers() (+24 more)

### Community 7 - "types.ts"
Cohesion: 0.09
Nodes (27): activity, admin, auth, common, community, credits, docsShell, en (+19 more)

### Community 8 - "Docs.tsx"
Cohesion: 0.10
Nodes (31): CommandPalette(), CommandPaletteItem, CommandPaletteProps, DocsBanner(), DocNavItem, DocsSearch(), DocsSearchProps, DocsSidebar() (+23 more)

### Community 9 - "BracketDetail.tsx"
Cohesion: 0.08
Nodes (24): BracketDetail, BracketFormat, BracketMatch, BracketSummary, createBracket(), deleteBracket(), disableBracketShare(), enableBracketShare() (+16 more)

### Community 10 - "Bunker.tsx"
Cohesion: 0.06
Nodes (48): announceBunkerAbility(), BUNKER_FIELD_KEYS, BunkerCardPools, BunkerCharacter, BunkerFieldKey, BunkerPlayerRef, BunkerPublicState, fetchPublicBunker() (+40 more)

### Community 11 - "AutoMod.tsx"
Cohesion: 0.11
Nodes (26): AutomodFilter, AutomodPunishment, AutomodSettings, createEscalationRule(), deleteEscalationRule(), EscalationAction, EscalationRule, fetchAutomod() (+18 more)

### Community 12 - "compilerOptions"
Cohesion: 0.08
Nodes (23): DOM, src, vite/client, compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx (+15 more)

### Community 13 - "ModuleConfigPanel.tsx"
Cohesion: 0.14
Nodes (19): banMember(), CaseTimeline, CaseTimelineItem, createMemberWarn(), deleteWarn(), fetchMemberDetail(), fetchMemberWarns(), grantRole() (+11 more)

### Community 14 - "Family.tsx"
Cohesion: 0.29
Nodes (9): createCustomCommand(), CustomCommandsSettings, deleteCustomCommand(), fetchCustomCommands(), setCustomCommandsEnabled(), updateCustomCommand(), CustomCommandsPage(), parseTab() (+1 more)

### Community 15 - "compilerOptions"
Cohesion: 0.10
Nodes (19): node, vite.config.ts, compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection (+11 more)

### Community 16 - "FeedbackCategories.tsx"
Cohesion: 0.25
Nodes (12): createReactionRole(), deleteReactionRole(), fetchChannels(), fetchEmojis(), fetchReactionRoles(), ReactionRoleEntry, ReactionRolePair, updateReactionRole() (+4 more)

### Community 17 - "useT"
Cohesion: 0.20
Nodes (14): AuditEntry, AuditModerator, AuditPage, fetchAudit(), AuditPage(), csvEscape(), downloadAuditCsv(), EntryRow() (+6 more)

### Community 18 - "useLanguage"
Cohesion: 0.12
Nodes (13): react, fetchPublicLeaderboard(), loginUrl(), PublicLeaderboardEntry, App(), PublicLayout(), useLanguage(), HeadingAnchor() (+5 more)

### Community 19 - "AuthContext.tsx"
Cohesion: 0.18
Nodes (15): DashboardUser, fetchCurrentUser(), fetchSuperAdminGuilds(), selectGuild(), SuperAdminGuild, ProtectedRoute(), PublicLandingOrDashboard(), AuthContext (+7 more)

### Community 20 - "LanguageContext.tsx"
Cohesion: 0.31
Nodes (7): fallbackValue, LanguageContext, LanguageContextValue, LanguageProvider(), readStoredLang(), Lang, NotFoundPage()

### Community 21 - "Fun.tsx"
Cohesion: 0.18
Nodes (11): ApiError, fetchStarboard(), previewTemplate(), StarboardSettings, TemplatePreviewResult, updateStarboard(), API_ERROR_KEYS, formatApiError() (+3 more)

### Community 22 - "Members.tsx"
Cohesion: 0.20
Nodes (10): fetchModules(), Dropdown(), DropdownItem(), DropdownProps, DashboardShell(), NAV_GROUPS, NavGroup, navItemActive() (+2 more)

### Community 23 - "ServerSelect.tsx"
Cohesion: 0.09
Nodes (30): BotProfileResponse, deleteCardBg(), fetchBotProfile(), fetchVoiceStats(), fetchXpLeaderboard(), fetchXpOverview(), resetAllXp(), resetMemberXp() (+22 more)

### Community 24 - "Casino.tsx"
Cohesion: 0.19
Nodes (12): CasinoLeaderboardEntry, CasinoSettings, fetchCasinoLeaderboard(), fetchCasinoSettings(), fetchEconomySettings(), updateCasinoSettings(), updateEconomySettings(), CasinoPage() (+4 more)

### Community 25 - "Economy.tsx"
Cohesion: 0.43
Nodes (7): BirthdaysPayload, deleteBirthday(), fetchBirthdays(), setBirthday(), testBirthdayAnnounce(), updateBirthdaySettings(), BirthdaysCalendarPage()

### Community 26 - "plugins"
Cohesion: 0.22
Nodes (12): CtdConfig, fetchCtdConfig(), fetchRoles(), fetchStickyRoles(), RoleChip, RoleInfo, StickyRolesSettings, updateCtdConfig() (+4 more)

### Community 27 - "VoiceStats.tsx"
Cohesion: 0.24
Nodes (13): deleteEmbedTemplate(), EmbedFieldSpec, EmbedSpec, EmbedTemplate, fetchEmbedTemplates(), saveEmbedTemplate(), Props, EmbedPreview() (+5 more)

### Community 28 - "DashboardShell.tsx"
Cohesion: 0.24
Nodes (6): AccountLink(), FeatureDef, FEATURES, FeatureSection(), GhostButton(), isSpaPath()

### Community 29 - "Login.tsx"
Cohesion: 0.22
Nodes (8): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, typescript, warn

### Community 35 - "Toggle.tsx"
Cohesion: 0.22
Nodes (15): advanceBunkerGamePhase(), applyBunkerAbility(), BunkerGameDetail, BunkerGameSummary, endBunkerGame(), fetchBunkerCardPools(), fetchBunkerGameDetail(), fetchBunkerGames() (+7 more)

### Community 36 - "FeedbackCaseDetailPanel.tsx"
Cohesion: 0.27
Nodes (8): WhatsNewBullets(), WhatsNewCard(), WhatsNewModal(), dismissWhatsNew(), isWhatsNewDismissed(), WHATS_NEW, whatsNewDismissKey(), WhatsNewEntry

### Community 37 - "FeedbackCaseDetailPanel.tsx"
Cohesion: 0.20
Nodes (10): decideFeedbackCase(), FeedbackCaseDetail, FeedbackCaseSummary, fetchFeedbackCaseDetail(), fetchFeedbackCases(), FeedbackCaseDetailPanel(), Props, sampleDetail (+2 more)

### Community 38 - "Mafia.tsx"
Cohesion: 0.20
Nodes (12): advanceMafiaGamePhase(), endMafiaGame(), fetchMafiaGameDetail(), fetchMafiaGames(), fetchMafiaSettings(), MafiaGameDetail, MafiaGameSummary, MafiaSettings (+4 more)

### Community 39 - "useT"
Cohesion: 0.25
Nodes (10): FeedbackPanelSettings, fetchFeedbackPanelSettings(), updateFeedbackPanelSettings(), EmbedEditor(), LanguageToggle(), useT(), AccessDeniedPage(), FeedbackPage() (+2 more)

### Community 40 - "AntiRaid.tsx"
Cohesion: 0.19
Nodes (13): createEvent(), CreateEventSpec, endPoll(), fetchPolls(), PollEntry, buildEventEmbedPreview(), emptyCreateSpec(), EventsPage() (+5 more)

### Community 41 - "PublicMafiaAction.tsx"
Cohesion: 0.24
Nodes (16): apiFetch(), createDailyTopic(), DailyTopicSettings, deleteDailyTopic(), deleteSticky(), fetchDailyTopic(), fetchSticky(), postDailyTopicNow() (+8 more)

### Community 42 - "Supply.tsx"
Cohesion: 0.23
Nodes (11): cancelSupply(), closeSupply(), createSupply(), fetchSupplyOverview(), jsonInit(), Supply, SupplyOverview, untimeoutMember() (+3 more)

### Community 43 - "Toggle.tsx"
Cohesion: 0.22
Nodes (11): ChannelInfo, fetchNewsSettings(), fetchServerLog(), NewsSettings, ServerLogEventConfig, updateNewsSettings(), updateServerLog(), Toggle() (+3 more)

### Community 44 - "ServerSettings.tsx"
Cohesion: 0.24
Nodes (12): fetchLanguage(), fetchOwnerAlerts(), fetchTimezone(), OwnerAlertsSettings, ServerLanguage, testOwnerAlerts(), updateLanguage(), updateOwnerAlerts() (+4 more)

### Community 45 - "EventDetailPanel.tsx"
Cohesion: 0.26
Nodes (9): closeEvent(), deleteEvent(), EventParticipantTeamCode, fetchEventDetail(), notifyEventParticipants(), EventDetailPanel(), Props, pollDetail (+1 more)

### Community 46 - "Streams.tsx"
Cohesion: 0.22
Nodes (10): createStreamSubscription(), deleteStreamSubscription(), fetchStreams(), StreamSubscription, testStreamSubscription(), updateStreamSubscription(), Modal(), ModalProps (+2 more)

### Community 47 - "ServerSelect.tsx"
Cohesion: 0.29
Nodes (7): fetchInviteUrl(), fetchManageableGuilds(), logout(), ManageableGuild, isForbiddenError(), guildIconUrl(), ServerSelectPage()

### Community 48 - "ScheduledMessages.tsx"
Cohesion: 0.24
Nodes (10): createScheduledMessage(), deleteScheduledMessage(), fetchScheduledMessages(), ScheduledMessagesSettings, setScheduledMessagesEnabled(), updateScheduledMessage(), MessagesPage(), MessagesTab (+2 more)

### Community 49 - "StickyMessages.tsx"
Cohesion: 0.22
Nodes (10): EconomySettings, EconomyTopEntry, EconomyWeeklyReportRow, fetchEconomyTop(), fetchEconomyWeeklyReport(), resetAllEconomyBalances(), setEconomyBalance(), EconomyPage() (+2 more)

### Community 50 - "Toggle.tsx"
Cohesion: 0.06
Nodes (43): activateLockdown(), AntiRaidSettings, deactivateLockdown(), fetchAntiRaidSettings(), fetchLockdownStatus(), fetchModerationLog(), fetchSetupHealth(), fetchSpamSettings() (+35 more)

### Community 51 - "Credits.tsx"
Cohesion: 0.17
Nodes (7): ASTRA_PROJECTS, CreditsPage(), OTHER_PROJECTS, Project, SERVER_OVERLAY, TEAM, TeamMember

### Community 52 - "Giveaways.tsx"
Cohesion: 0.24
Nodes (8): createGiveaway(), endGiveaway(), fetchGiveawayOverview(), Giveaway, GiveawayOverview, rerollGiveaway(), GiveawaysPage(), emptyOverview

### Community 53 - "Fun.tsx"
Cohesion: 0.29
Nodes (10): fetchFunSettings(), fetchQuoteSettings(), fetchWordleSettings(), FunSettings, QuoteSettings, updateFunSettings(), updateQuoteSettings(), updateWordleSettings() (+2 more)

### Community 54 - "Button.tsx"
Cohesion: 0.28
Nodes (7): fetchInvites(), InvitesSettings, updateInvitesSettings(), ButtonProps, Variant, VARIANT_CLASSES, InvitesTrackerPage()

### Community 55 - "AutoReactions.tsx"
Cohesion: 0.43
Nodes (6): AutoReactionRule, AutoReactionsSettings, fetchAutoReactions(), updateAutoReactions(), AutoReactionsPage(), newRule()

### Community 56 - "ValChecker.tsx"
Cohesion: 0.53
Nodes (5): fetchValCheckerSettings(), saveValCheckerSettings(), ValCheckerSettings, clampPoll(), ValCheckerPage()

### Community 57 - "fetchProfileCardPreview"
Cohesion: 0.40
Nodes (5): fetchPreviewBlobUrl(), fetchProfileCardPreview(), fetchProfileCardPreviewGif(), profileCardPreviewGifUrl(), profileCardPreviewUrl()

### Community 58 - "Bunker.test.tsx"
Cohesion: 0.40
Nodes (3): baseGameSummary, emptySettings, mockPools

### Community 59 - "MessageBuilder.tsx"
Cohesion: 0.60
Nodes (3): MessageBuilderPage(), parseTab(), Tab

## Knowledge Gaps
- **243 isolated node(s):** `$schema`, `typescript`, `oxc`, `react/rules-of-hooks`, `warn` (+238 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `react` connect `useLanguage` to `apiFetch`, `renderWithLanguage.tsx`, `ServerEntry.tsx`, `Lockdown.tsx`, `Docs.tsx`, `BracketDetail.tsx`, `Bunker.tsx`, `AutoMod.tsx`, `ModuleConfigPanel.tsx`, `Family.tsx`, `FeedbackCategories.tsx`, `useT`, `AuthContext.tsx`, `LanguageContext.tsx`, `Fun.tsx`, `Members.tsx`, `ServerSelect.tsx`, `Casino.tsx`, `Economy.tsx`, `plugins`, `VoiceStats.tsx`, `DashboardShell.tsx`, `Login.tsx`, `Toggle.tsx`, `FeedbackCaseDetailPanel.tsx`, `FeedbackCaseDetailPanel.tsx`, `Mafia.tsx`, `useT`, `AntiRaid.tsx`, `PublicMafiaAction.tsx`, `Supply.tsx`, `Toggle.tsx`, `ServerSettings.tsx`, `EventDetailPanel.tsx`, `Streams.tsx`, `ServerSelect.tsx`, `ScheduledMessages.tsx`, `StickyMessages.tsx`, `Toggle.tsx`, `Credits.tsx`, `Giveaways.tsx`, `Fun.tsx`, `Button.tsx`, `AutoReactions.tsx`, `ValChecker.tsx`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Why does `useT()` connect `useT` to `apiFetch`, `ServerEntry.tsx`, `Lockdown.tsx`, `BracketDetail.tsx`, `Bunker.tsx`, `AutoMod.tsx`, `ModuleConfigPanel.tsx`, `Family.tsx`, `FeedbackCategories.tsx`, `useT`, `useLanguage`, `AuthContext.tsx`, `LanguageContext.tsx`, `Fun.tsx`, `Members.tsx`, `ServerSelect.tsx`, `Casino.tsx`, `Economy.tsx`, `plugins`, `VoiceStats.tsx`, `DashboardShell.tsx`, `Toggle.tsx`, `FeedbackCaseDetailPanel.tsx`, `FeedbackCaseDetailPanel.tsx`, `Mafia.tsx`, `AntiRaid.tsx`, `PublicMafiaAction.tsx`, `Supply.tsx`, `Toggle.tsx`, `ServerSettings.tsx`, `EventDetailPanel.tsx`, `Streams.tsx`, `ServerSelect.tsx`, `ScheduledMessages.tsx`, `StickyMessages.tsx`, `Toggle.tsx`, `Giveaways.tsx`, `Fun.tsx`, `Button.tsx`, `AutoReactions.tsx`, `ValChecker.tsx`, `MessageBuilder.tsx`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Why does `apiFetch()` connect `PublicMafiaAction.tsx` to `react`, `apiFetch`, `client.ts`, `ServerEntry.tsx`, `Lockdown.tsx`, `BracketDetail.tsx`, `Bunker.tsx`, `AutoMod.tsx`, `ModuleConfigPanel.tsx`, `Family.tsx`, `FeedbackCategories.tsx`, `useT`, `useLanguage`, `AuthContext.tsx`, `Fun.tsx`, `ServerSelect.tsx`, `Casino.tsx`, `Economy.tsx`, `plugins`, `VoiceStats.tsx`, `Toggle.tsx`, `FeedbackCaseDetailPanel.tsx`, `Mafia.tsx`, `useT`, `AntiRaid.tsx`, `Supply.tsx`, `Toggle.tsx`, `ServerSettings.tsx`, `EventDetailPanel.tsx`, `Streams.tsx`, `ScheduledMessages.tsx`, `StickyMessages.tsx`, `Toggle.tsx`, `Giveaways.tsx`, `Fun.tsx`, `Button.tsx`, `AutoReactions.tsx`, `ValChecker.tsx`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **What connects `$schema`, `typescript`, `oxc` to the rest of the system?**
  _243 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `apiFetch` be split into smaller, more focused modules?**
  _Cohesion score 0.1341991341991342 - nodes in this community are weakly interconnected._
- **Should `client.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.033879781420765025 - nodes in this community are weakly interconnected._
- **Should `ServerEntry.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.08309178743961353 - nodes in this community are weakly interconnected._