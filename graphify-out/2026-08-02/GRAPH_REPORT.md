# Graph Report - Cheterin_Bot_Dashboard  (2026-08-02)

## Corpus Check
- 646 files · ~459,906 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 6652 nodes · 18759 edges · 243 communities (232 shown, 11 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 259 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0be5b2db`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Game Settings & Bunker DB
- Supply Module
- Dashboard App Bootstrap
- Test Fake Channels
- API Client Types
- Test Fake Bot
- Automod Route Tests
- Tournament Brackets
- Feedback Cases
- Giveaways Routes
- Automod Cog
- Server Event Logging
- Automod Filter Core
- Test Fake Members
- Daily Topic Module
- API Client Functions
- Bunker Game Core
- Moderation Routes
- Bunker Discord Cog
- Mass Role Assignment
- Embed Builder Routes
- Bot Entrypoint & Auth Middleware
- Frontend Package Deps
- Lockdown API Client
- Mafia DB Tests
- Mafia Core Tests
- Stream Notifications
- Feedback Panel Tests
- Reaction Roles Tests
- Streams API Client
- Voice Rooms Routes
- XP API Client
- Mafia Discord Cog
- Feedback API Client
- Family DB Tests
- Events & Embeds Client
- Lockdown Routes
- Events Route Tests
- Mafia Public Route Tests
- Family Tickets
- Button Forms
- Audit Log & Stats DB
- Giveaway Cog
- Brackets Client Tests
- Bunker API Client
- Automod API Client
- Event Builder UI
- Family Core Tests
- XP Core Tests
- Event Publish Tests
- TypeScript Config
- Bot Config Store
- Family Birthdays
- Anti-Spam Cog
- news.py
- events.py
- test_feedback_routes.py
- FeedbackCategories.tsx
- Docs.tsx
- voice_rooms.py
- XPCog
- auth.py
- resolve_guild_member()
- xp.py
- test_feedback_category_routes.py
- Supply.tsx
- MassAssignModal.tsx
- compilerOptions
- .__init__()
- VoiceTracker
- Interaction
- ensure_owner()
- family.py
- test_family_routes.py
- test_access.py
- test_config_routes.py
- RosterCog
- reaction_roles.py
- PublicBunkerAction.tsx
- Leaderboard.tsx
- VoiceManager
- mafia.py
- events.py
- ChetBot
- ChannelInfo
- MafiaLobbyView
- voice_logs.py
- test_auto_roles_routes.py
- Giveaways.tsx
- renderWithI18n.tsx
- Welcome
- access_middleware.py
- test_mafia_routes.py
- test_warns_routes.py
- test_xp_routes.py
- CTD
- setup_static_routes()
- FakeAsset
- plugins
- DocsSearch.tsx
- access_middleware.py
- auto_roles.py
- icons.svg
- format_voice_time()
- DocsToc.tsx
- FakeVoiceChannel
- favicon.svg
- Hero Image Graphic
- tsconfig.json
- React Logo Image
- DocsSearch.tsx
- test_fun_routes.py
- Vite Logo
- DocsSearch.tsx
- test_members_list.py
- test_member_detail.py
- DocsToc.tsx
- init
- Request
- EmbedBuilder.tsx
- Button.tsx
- events.py
- wordle_card.py
- events.py
- load_events
- test_supply_routes.py
- ru.ts
- wordle.py
- test_warns_routes.py
- Supply.tsx
- .__init__
- Docs.tsx
- EventDetailPanel.tsx
- format_voice_time
- test_feedback_panel_routes.py
- setup_session
- FakeResponse
- FakeResponse
- test_news_routes.py
- test_auto_roles_routes.py
- test_supply_routes.py
- lockdown.py
- test_xp_routes.py
- mafia.py
- format_voice_time
- FakeVoiceChannel
- Fun.tsx
- InvitesCog
- _FakeMember
- Casino.tsx
- lang_for
- Fun.tsx
- resolve_ticket
- welcome.py
- test_auto_roles_routes.py
- load_dashboard_config
- EventDetailPanel.tsx
- test_members_list.py
- test_button_config.py
- test_supply_routes.py
- test_ctd_routes.py
- test_news_routes.py
- birthdays_db.py
- test_feedback_panel_routes.py
- test_roles.py
- test_access.py
- test_wordle_routes.py
- casino_db.py
- Mafia.tsx
- custom_commands.py
- test_warns_routes.py
- Welcome.tsx
- __init__.py
- moderation_log.py
- save_config
- test_news_routes.py
- test_members_list.py
- VerificationCog
- test_voice_panel_state.py
- Mafia.tsx
- embed_builder.py
- test_feedback_panel_routes.py
- test_supply_routes.py
- test_auto_roles_routes.py
- VerificationCog
- setup_session
- build_game_started_embed
- Mafia.tsx
- test_module_test_send.py
- voice_logs.py
- test_welcome_routes.py
- test_news_routes.py
- auto_reactions.py
- SupplyView
- embed_style.py
- test_ctd_routes.py
- localize_character
- guild_context.py
- test_news_routes.py
- test_voice_stats_routes.py
- pick_bunker_conditions
- resolve_ticket
- HelpView
- spam_core.py
- test_auto_roles_routes.py
- test_welcome_routes.py
- adminPanel.js
- SupplyView
- README.md
- starboard_db.py
- test_xp_rank_cog.py
- aiohttp Dependency
- aiohttp-session Dependency
- StickyMessages.tsx
- Interaction
- Pillow Dependency
- warns_db.py
- test_voice_panel_state.py
- python-dotenv Dependency
- language_core.py
- test_verification_routes.py
- voice_logs.py
- setup_session
- test_ctd_routes.py
- owner_alerts.py
- owner_alerts.py
- test_feedback_panel_routes.py
- xp.py
- test_tempban_routes.py
- auto_roles.py
- welcome.py
- test_fun_routes.py
- VoiceManager
- test_antiraid_routes.py
- test_timeout_routes.py

## God Nodes (most connected - your core abstractions)
1. `force_login()` - 430 edges
2. `FakeMember` - 384 edges
3. `FakeGuild` - 314 edges
4. `FakeBot` - 281 edges
5. `apiFetch()` - 192 edges
6. `useT()` - 165 edges
7. `FakeChannel` - 159 edges
8. `t()` - 139 edges
9. `make_moderation_app()` - 127 edges
10. `FakeRole` - 119 edges

## Surprising Connections (you probably didn't know these)
- `FakeInteraction` --uses--> `BlackjackView`  [INFERRED]
  dashboard/backend/tests/test_blackjack_cog.py → blackjack.py
- `FakeMessage` --uses--> `BlackjackView`  [INFERRED]
  dashboard/backend/tests/test_blackjack_cog.py → blackjack.py
- `FakeResponse` --uses--> `BlackjackView`  [INFERRED]
  dashboard/backend/tests/test_blackjack_cog.py → blackjack.py
- `test_active_game_is_isolated_per_guild()` --indirect_call--> `BlackjackView`  [INFERRED]
  dashboard/backend/tests/test_blackjack_cog.py → blackjack.py
- `test_cooldown_is_per_guild()` --indirect_call--> `BlackjackView`  [INFERRED]
  dashboard/backend/tests/test_blackjack_cog.py → blackjack.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **External Platform and Social Icons Set** — dashboard_frontend_public_icons_bluesky_icon, dashboard_frontend_public_icons_discord_icon, dashboard_frontend_public_icons_github_icon, dashboard_frontend_public_icons_x_icon, dashboard_frontend_public_icons_social_icon [INFERRED 0.85]
- **Dashboard UI Icon Asset Set** — dashboard_frontend_public_icons_bluesky_icon, dashboard_frontend_public_icons_discord_icon, dashboard_frontend_public_icons_documentation_icon, dashboard_frontend_public_icons_github_icon, dashboard_frontend_public_icons_social_icon, dashboard_frontend_public_icons_x_icon [EXTRACTED 1.00]
- **Docs Page User Interface** — dashboard_frontend_src_pages_docs, dashboard_frontend_src_components_docs_docsbanner, dashboard_frontend_src_assets_docs_banner [INFERRED 0.90]
- **Hero Page Visual Branding Elements** — dashboard_frontend_src_assets_hero, dashboard_frontend_src_assets_hero_branding, dashboard_frontend_src_assets_hero_layered_stack [INFERRED 0.85]

## Communities (243 total, 11 thin omitted)

### Community 0 - "Game Settings & Bunker DB"
Cohesion: 0.13
Nodes (40): build(), Fake-lobby bots use negative user ids; vote + roster must accept them., Night actions must accept synthetic negative bot seat ids., _setup_game(), test_action_dead_player(), test_action_deadline_passed(), test_action_game_not_active(), test_action_happy_path_and_resubmit() (+32 more)

### Community 1 - "Supply Module"
Cohesion: 0.11
Nodes (43): _display_name(), _finalize(), Request, Response, _serialize_supply(), supply_cancel(), supply_close(), supply_create() (+35 more)

### Community 2 - "Dashboard App Bootstrap"
Cohesion: 0.04
Nodes (87): apiFetch(), banMember(), cancelSupply(), CaseTimeline, CaseTimelineItem, closeSupply(), createCustomCommand(), createDailyTopic() (+79 more)

### Community 3 - "Test Fake Channels"
Cohesion: 0.10
Nodes (25): activateLockdown(), deactivateLockdown(), fetchLockdownStatus(), fetchModerationLog(), GiveawayOverview, LockdownStatus, ModerationLogEntry, SetupHealth (+17 more)

### Community 4 - "API Client Types"
Cohesion: 0.03
Nodes (101): advanceMafiaGamePhase(), AutoRolesSettings, BirthdayEntry, BotProfileSettings, BracketStandingsRow, BunkerAbilityAnnouncement, BunkerAdditionalInfo, BunkerAgeInfo (+93 more)

### Community 5 - "Test Fake Bot"
Cohesion: 0.04
Nodes (119): DashboardConfig, FakeBot, FakeGuild, make_moderation_app(), make_client_app(), test_guild_unavailable_gets_503(), test_member_not_in_guild_gets_403(), test_member_with_access_reaches_handler() (+111 more)

### Community 6 - "Automod Route Tests"
Cohesion: 0.10
Nodes (20): BlackjackCog, BlackjackView, build_embed(), GameResult, Bot, Button, Color, Embed (+12 more)

### Community 7 - "Tournament Brackets"
Cohesion: 0.06
Nodes (64): create_bracket(), create_bracket_v2(), _de_get_match(), _de_match(), _de_recompute_match(), _de_resolve(), extract_entries_from_event(), find_by_share_token() (+56 more)

### Community 8 - "Feedback Cases"
Cohesion: 0.20
Nodes (22): isolated_config(), test_load_categories_returns_empty_dict_when_file_missing(), test_migrate_from_env_if_needed_creates_config_from_env(), test_migrate_from_env_if_needed_skips_when_env_vars_missing(), test_migrate_from_env_if_needed_skips_when_file_already_exists(), test_save_then_load_round_trip(), test_validate_category_spec_accepts_valid_spec(), test_validate_category_spec_allows_own_case_prefix_on_edit() (+14 more)

### Community 9 - "Giveaways Routes"
Cohesion: 0.08
Nodes (55): _display_name(), giveaways_create(), giveaways_end(), giveaways_overview(), giveaways_reroll(), Request, Response, _serialize_giveaway() (+47 more)

### Community 10 - "Automod Cog"
Cohesion: 0.06
Nodes (48): Attachment, Request, Response, quote_get(), quote_put(), _isolate(), Quote settings and mention/reply gate., test_bot_is_mentioned() (+40 more)

### Community 11 - "Server Event Logging"
Cohesion: 0.07
Nodes (37): AuditLogAction, AuditLogEntry, Request, Response, serverlog_get(), serverlog_put(), _Role, test_format_stay_duration() (+29 more)

### Community 12 - "Automod Filter Core"
Cohesion: 0.08
Nodes (41): _default_filter(), _default_notify_template(), detect_bad_words(), detect_caps_lock(), detect_emoji_spam(), detect_invites(), detect_links(), detect_mentions() (+33 more)

### Community 13 - "Test Fake Members"
Cohesion: 0.06
Nodes (27): decideFeedbackCase(), FeedbackCaseDetail, FeedbackCaseSummary, fetchFeedbackCaseDetail(), fetchFeedbackCases(), baseGameSummary, emptySettings, mockPools (+19 more)

### Community 14 - "Daily Topic Module"
Cohesion: 0.10
Nodes (45): add_topic(), already_posted_today(), delete_topic(), get_settings(), get_today_post_time(), is_valid_time(), mark_posted_today(), _normalized() (+37 more)

### Community 15 - "API Client Functions"
Cohesion: 0.09
Nodes (32): BlackjackGame, _build_deck(), can_double(), card_rank(), card_suit(), _deal_card(), dealer_play(), format_hand() (+24 more)

### Community 16 - "Bunker Game Core"
Cohesion: 0.13
Nodes (26): add_escalation_rule(), delete_escalation_rule(), update_escalation_rule(), get_settings(), mark_announced(), Birthday calendar settings: channel + optional ping role., save_settings(), test_escalation_crud() (+18 more)

### Community 17 - "Moderation Routes"
Cohesion: 0.22
Nodes (28): _assignable_roles(), ban_member(), dashboard_reason(), _get_guild_or_none(), get_moderation_log(), _get_target_or_response(), grant_role(), kick_member() (+20 more)

### Community 18 - "Bunker Discord Cog"
Cohesion: 0.10
Nodes (29): Documentation Banner Image, DocsBanner(), DocNavItem, DocsSearch(), DocsSearchProps, DocsSidebar(), DocsSidebarProps, GROUP_ICONS (+21 more)

### Community 19 - "Mass Role Assignment"
Cohesion: 0.04
Nodes (81): DashboardUser, fetchCurrentUser(), fetchInviteUrl(), fetchManageableGuilds(), fetchModules(), fetchPublicBracket(), fetchPublicLeaderboard(), fetchSuperAdminGuilds() (+73 more)

### Community 20 - "Embed Builder Routes"
Cohesion: 0.11
Nodes (36): test_build_embed_omits_color_when_absent(), test_build_embed_sets_author_footer_image_thumbnail(), test_build_embed_sets_basic_fields(), test_build_embed_sets_fields(), test_build_embed_sets_timestamp(), test_delete_template_missing_returns_false(), test_delete_template_removes_only_target_and_guild(), test_embed_to_spec_returns_empty_color_when_absent() (+28 more)

### Community 21 - "Bot Entrypoint & Auth Middleware"
Cohesion: 0.18
Nodes (12): test_supply_config_is_per_guild(), Messageable, _config_int(), generate_embed(), get_reminder_minutes(), Bot, Color, Embed (+4 more)

### Community 22 - "Frontend Package Deps"
Cohesion: 0.04
Nodes (46): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, tailwindcss, @tailwindcss/vite, devDependencies (+38 more)

### Community 23 - "Lockdown API Client"
Cohesion: 0.10
Nodes (36): AppRunner, create_app(), json_error_middleware(), Application, Path, start_dashboard(), ConfigError, load_dashboard_config() (+28 more)

### Community 24 - "Mafia DB Tests"
Cohesion: 0.11
Nodes (24): AutomodFilter, AutomodPunishment, AutomodSettings, createEscalationRule(), deleteEscalationRule(), EscalationAction, EscalationRule, fetchAutomod() (+16 more)

### Community 25 - "Mafia Core Tests"
Cohesion: 0.08
Nodes (37): _FakeMember, _FakePermissions, isolated_config(), test_assign_roles_matches_scale_and_covers_all_players(), test_check_win_condition_mafia_wins_at_parity(), test_check_win_condition_no_winner_yet(), test_check_win_condition_town_wins_when_no_mafia(), test_get_settings_defaults() (+29 more)

### Community 26 - "Stream Notifications"
Cohesion: 0.09
Nodes (26): _public_sub(), Request, Response, streams_create(), streams_delete(), streams_list(), streams_test(), streams_update() (+18 more)

### Community 27 - "Feedback Panel Tests"
Cohesion: 0.10
Nodes (33): bet_error(), flip_coin(), get_settings(), payout_amount(), Ядро модуля «Казино»: слоты, монетка и блэкджек на серверную валюту.  Без импорт, Настройки модуля сервера с дефолтами (выключен по умолчанию)., None — ставка допустима, иначе текст ошибки для игрока., Выигрыш с учётом преимущества казино (округление вниз). (+25 more)

### Community 28 - "Reaction Roles Tests"
Cohesion: 0.09
Nodes (38): _bot_channel_flags(), create_reaction_role(), delete_reaction_role(), _get_guild_or_none(), _is_role_assignable(), list_channels(), list_emojis(), list_reaction_roles() (+30 more)

### Community 29 - "Streams API Client"
Cohesion: 0.06
Nodes (55): FakeAuditLogEntry, FakeMember, Одна запись аудита для guild.audit_logs() — только то, что нужно     serverlog., build(), _StubForbidden, _StubNotFound, test_ban_calls_discord_and_logs(), test_ban_discord_not_found_maps_to_404() (+47 more)

### Community 30 - "Voice Rooms Routes"
Cohesion: 0.11
Nodes (35): Request, Response, voice_panel_publish(), voice_room_delete(), voice_rooms_list(), build(), FakeVoiceChannel, isolated_db() (+27 more)

### Community 31 - "XP API Client"
Cohesion: 0.07
Nodes (61): isolated_db(), _create_legacy_schema(), isolated_db(), Тесты stats_db: per-guild изоляция XP/войс/аудита и миграция старой схемы.  Фаза, Схема до Фазы 2.2а: без guild_id (как в проде на мейн-сервере)., После миграции один user_id может существовать на разных серверах., test_audit_add_list_count_scoped_per_guild(), test_audit_list_and_count_filter_by_search() (+53 more)

### Community 32 - "Mafia Discord Cog"
Cohesion: 0.14
Nodes (32): build(), _poll_create_spec(), _poll_event(), test_close_event_route_404(), test_close_event_route_requires_auth(), test_close_event_route_success(), test_create_event_404_when_channel_missing(), test_create_event_404_when_role_reward_missing() (+24 more)

### Community 33 - "Feedback API Client"
Cohesion: 0.07
Nodes (31): ago(), build_fingerprint_map(), create_session(), diff_status_items(), find_player(), form_strip_inline(), form_strip_spaced(), format_delta() (+23 more)

### Community 34 - "Family DB Tests"
Cohesion: 0.10
Nodes (49): _create_legacy_schema(), isolated_db(), _main(), Тесты family_db: per-guild ростер/заявки/дни рождения + миграция старой схемы., Схема до Фазы 2.2б: синглтоны roster_msg/birthday_msg (id=1), single-PK     pen, test_birthday_message_roundtrip_and_isolation(), test_birthday_roundtrip_and_queries(), test_list_and_count_tickets_scoped_and_filtered() (+41 more)

### Community 35 - "Events & Embeds Client"
Cohesion: 0.12
Nodes (31): _cmd(), _grp(), _key(), Any, Apply slash command localizations for every cog (Phase 3.2(3))., register_automod(), register_birthdays(), register_blackjack() (+23 more)

### Community 36 - "Lockdown Routes"
Cohesion: 0.18
Nodes (38): eliminate_player(), update_game(), build(), _character(), Fake-lobby bots use negative user ids; vote + roster must accept them., _setup_game(), test_ability_already_used(), test_ability_dead_player() (+30 more)

### Community 37 - "Events Route Tests"
Cohesion: 0.13
Nodes (35): callback(), _frontend(), invite_url(), list_guilds(), login(), logout(), me(), Request (+27 more)

### Community 38 - "Mafia Public Route Tests"
Cohesion: 0.24
Nodes (17): get(), load_config(), migrate_from_env_if_needed(), Invite link for tempban DM and other modules (no hardcoded fallback)., resolve_server_invite_link(), save_config(), isolated_settings_db(), test_get_returns_default_when_key_missing() (+9 more)

### Community 39 - "Family Tickets"
Cohesion: 0.11
Nodes (19): can_manage_guild_permissions(), has_dashboard_access(), has_manage_server(), has_super_admin_access(), manageable_guilds(), Контроль доступа к дашборду (модель MEE6, Фаза 2.3).  Доступ к серверу = право, DEPRECATED (Фаза 1, роль-модель). Оставлено до перевода auth/middleware на, Доступ к настройкам сервера: Manage Server или Administrator на этой гильдии. (+11 more)

### Community 40 - "Button Forms"
Cohesion: 0.12
Nodes (12): ButtonCreate, DynamicQuestionsModal, _get_allowed_role_ids(), _load_buttons_config(), BaseException, Interaction, Удаляет устаревшие записи кулдаунов., Возвращает оставшиеся секунды если кулдаун активен, иначе None. (+4 more)

### Community 41 - "Audit Log & Stats DB"
Cohesion: 0.06
Nodes (44): isolated_config(), Тесты ядра Вордла: целостность словаря, оценка догадок, слово дня, настройки., test_board_lines_pads_empty_rows(), test_day_number_epoch(), test_evaluate_all_green(), test_evaluate_duplicate_letters_consume_stock(), test_evaluate_green_priority_over_yellow(), test_evaluate_yellow_and_gray() (+36 more)

### Community 42 - "Giveaway Cog"
Cohesion: 0.05
Nodes (53): BracketSummary, closeEvent(), createBracket(), createEvent(), CreateEventSpec, createGiveaway(), deleteEvent(), deleteVoiceRoom() (+45 more)

### Community 43 - "Brackets Client Tests"
Cohesion: 0.14
Nodes (24): FakeAsset, test_get_settings_voice_new_fields_defaults(), test_settings_defaults(), build(), test_leaderboard_guild_unavailable(), test_leaderboard_keeps_members_who_left(), test_leaderboard_pagination_over_merged_roster(), test_leaderboard_search_filters_by_display_name() (+16 more)

### Community 44 - "Bunker API Client"
Cohesion: 0.05
Nodes (67): AntiRaidSettings, ApiError, AutoReactionRule, AutoReactionsSettings, BotProfileResponse, deleteTimedRole(), endPoll(), fetchAntiRaidSettings() (+59 more)

### Community 45 - "Automod API Client"
Cohesion: 0.14
Nodes (10): AutoMod, _consecutive_run_length(), BaseException, Bot, Guild, Interaction, Message, User (+2 more)

### Community 47 - "Event Builder UI"
Cohesion: 0.06
Nodes (50): BotConfig, createEmbedMessage(), deleteEmbedTemplate(), EmbedFieldSpec, EmbedMessagePayload, EmbedSpec, EmbedTemplate, FeedbackPanelSettings (+42 more)

### Community 48 - "Family Core Tests"
Cohesion: 0.13
Nodes (17): _FakeGuild, _FakeGuildRef, _FakeMember, isolated_config(), test_build_birthday_text_groups_by_month_and_resolves_mentions(), test_can_manage_tickets_requires_configured_role(), test_has_staff_access_admin_bypasses_role_check(), test_has_staff_access_via_role() (+9 more)

### Community 49 - "XP Core Tests"
Cohesion: 0.10
Nodes (27): isolated_config(), test_deserved_roles(), test_format_voice_time(), test_level_formula_monotonic(), test_level_from_xp_roundtrip(), test_level_progress(), test_render_announce(), test_roll_text_xp_respects_multiplier() (+19 more)

### Community 50 - "Event Publish Tests"
Cohesion: 0.26
Nodes (17): _poll_spec(), test_validate_event_spec_accepts_valid_poll_spec(), test_validate_event_spec_accepts_valid_tournament_spec(), test_validate_event_spec_allows_missing_team_size_check_for_solo_mode(), test_validate_event_spec_rejects_description_too_long(), test_validate_event_spec_rejects_empty_description(), test_validate_event_spec_rejects_empty_title(), test_validate_event_spec_rejects_invalid_mode_for_tournament() (+9 more)

### Community 51 - "TypeScript Config"
Cohesion: 0.08
Nodes (23): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+15 more)

### Community 52 - "Bot Config Store"
Cohesion: 0.11
Nodes (22): CasinoLeaderboardEntry, CasinoSettings, EconomySettings, EconomyTopEntry, EconomyWeeklyReportRow, fetchCasinoLeaderboard(), fetchCasinoSettings(), fetchEconomySettings() (+14 more)

### Community 53 - "Family Birthdays"
Cohesion: 0.12
Nodes (13): generate_embed(), GiveawayCog, GiveawayView, Bot, Button, Embed, Interaction, Range (+5 more)

### Community 54 - "Anti-Spam Cog"
Cohesion: 0.10
Nodes (34): preview_template(), Request, Response, Dry-run placeholder substitution for text/embed templates. Does not send to Disc, test_preview_text_and_slash(), test_build_goodbye_uses_custom_text(), test_default_dm_embed_uses_channel_placeholders(), test_resolve_dm_footer_uses_custom_text() (+26 more)

### Community 55 - "news.py"
Cohesion: 0.15
Nodes (18): _is_id_like(), news_get(), news_put(), Request, Response, get_channel_map(), get_settings(), _main_guild_id() (+10 more)

### Community 56 - "events.py"
Cohesion: 0.19
Nodes (9): casino_top_command(), CasinoLeaderboardView, Bot, Button, Embed, Guild, Interaction, Ког «Казино»: /слоты и /монетка на серверную валюту.  Требует включённой «Эконом (+1 more)

### Community 57 - "test_feedback_routes.py"
Cohesion: 0.06
Nodes (58): _auto_emoji_config(), build(), enable_economy(), FakeInteraction, FakeMsg, FakeResponse, Тесты кога «Развлечения»: русская рулетка (исходы, таймаут, кулдаун) и эмодзи-ру, test_auto_emoji_channel_interval_limits_frequency() (+50 more)

### Community 58 - "FeedbackCategories.tsx"
Cohesion: 0.36
Nodes (4): LeaderboardView, Button, Interaction, Интерактивный лидерборд: сортировка по Опыту / Голосу + пагинация.

### Community 59 - "Docs.tsx"
Cohesion: 0.07
Nodes (56): add(), connect(), get_by_user(), get_db_path(), init(), list_all(), _now(), Connection (+48 more)

### Community 60 - "voice_rooms.py"
Cohesion: 0.14
Nodes (21): _Deck, _pick_additional_info(), _pick_backpack_item(), _pick_health(), _pick_hobby(), _pick_large_item(), _pick_phobia(), _pick_profession() (+13 more)

### Community 61 - "XPCog"
Cohesion: 0.18
Nodes (6): _Member, Embed, Guild, Пересчитывает уровень, синхронизирует роли-награды, шлёт уведомление., Приводит роли-награды участника в соответствие с его прогрессом., Assemble stats + cosmetics + optional economy fields for card renderers.

### Community 62 - "auth.py"
Cohesion: 0.09
Nodes (33): announceBunkerAbility(), BUNKER_FIELD_KEYS, BunkerFieldKey, BunkerPublicState, fetchPublicBunker(), fetchPublicMafia(), MafiaPublicState, MafiaRole (+25 more)

### Community 63 - "resolve_guild_member()"
Cohesion: 0.15
Nodes (8): CTD, CTDCloseView, CTDView, _is_main_guild(), BaseException, Interaction, setup(), CTD create-ticket callback must accept only interaction (discord.py Button API).

### Community 64 - "xp.py"
Cohesion: 0.15
Nodes (31): _equipped_cosmetics(), _int_in(), _is_id_list(), _profile_card_args(), _public_leaderboard_payload(), Request, Response, Вкладка «Участники» дашборда: весь ростер гильдии, а не только те,     кто уже г (+23 more)

### Community 65 - "test_feedback_category_routes.py"
Cohesion: 0.12
Nodes (25): reset_settings_db(), isolated_db(), Тесты settings_migration: перенос плоских JSON в settings_db, идемпотентность., test_migrate_all_is_idempotent_across_two_runs(), test_migrate_all_migrates_existing_files_only(), test_migrate_one_missing_file_is_noop(), test_migrate_one_moves_data_and_renames_file(), test_migrate_one_skips_when_already_migrated() (+17 more)

### Community 66 - "Supply.tsx"
Cohesion: 0.13
Nodes (36): get_player_by_token(), list_alive_players(), list_players(), Row, Полная перезапись карточки — используется админ-панелью при ручном применении сп, _row_to_player(), set_player_character(), _avatar_url() (+28 more)

### Community 67 - "MassAssignModal.tsx"
Cohesion: 0.08
Nodes (43): BirthdaysPayload, ChannelInfo, createReactionRole(), createStreamSubscription(), CtdConfig, deleteBirthday(), deleteReactionRole(), deleteStreamSubscription() (+35 more)

### Community 68 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+11 more)

### Community 69 - ".__init__()"
Cohesion: 0.14
Nodes (9): OwnerAlertsCog, Bot, Embed, Guild, User, Owner alerts: DM/channel notify on missing perms, mass bans, module errors, plus, Callable from other modules when they hit repeated failures., Send an owner alert. Returns True if at least one delivery succeeded. (+1 more)

### Community 70 - "VoiceTracker"
Cohesion: 0.14
Nodes (8): is_active(), BaseException, Bot, VoiceState, Войс-трекер: единый учёт голосовых сессий.  Кормит сразу два модуля: - статис, setup(), VoiceSession, VoiceTracker

### Community 71 - "Interaction"
Cohesion: 0.08
Nodes (28): createFeedbackCategory(), deleteFeedbackCategory(), FeedbackCategoryFieldSpec, FeedbackCategorySpec, fetchFeedbackCategories(), fetchMassAssignStatus(), fetchMembers(), MassAssignStatus (+20 more)

### Community 72 - "ensure_owner()"
Cohesion: 0.08
Nodes (43): Тесты ядра экономики: курс от XP, комиссии, валидация ставок, хук award_for_xp., test_award_for_xp_disabled_gives_nothing(), test_bet_error_cases(), test_bet_error_unlimited_when_max_zero(), test_claim_daily_bonus_consecutive_day_extends_streak(), test_claim_daily_bonus_first_time(), test_claim_daily_bonus_gap_resets_streak(), test_claim_daily_bonus_same_day_rejected() (+35 more)

### Community 73 - "family.py"
Cohesion: 0.14
Nodes (11): BirthdayCog, build_birthday_embed(), BaseException, Bot, Embed, Guild, Interaction, User (+3 more)

### Community 74 - "test_family_routes.py"
Cohesion: 0.07
Nodes (59): _create_legacy_schema(), isolated_db(), _main_guild(), Тесты economy_db: атомарные списания, переводы, топ, журнал, per-guild изоляция., Данные, ошибочно записанные на guild_id=404, восстанавливаются на мейн., test_add_ignores_non_positive(), test_cosmetics_isolated_per_guild(), test_daily_bonus_default_when_missing() (+51 more)

### Community 75 - "test_access.py"
Cohesion: 0.22
Nodes (15): Request, Response, sticky_roles_get(), sticky_roles_put(), connect(), filter_member_roles(), get_db_path(), get_settings() (+7 more)

### Community 76 - "test_config_routes.py"
Cohesion: 0.12
Nodes (40): _make_game(), test_add_player_rejects_duplicate(), test_assign_player_role_and_get_by_token(), test_create_and_get_game(), test_get_active_game_in_channel_filters_by_status(), test_get_day_vote_single_row(), test_get_game_by_lobby_and_vote_message(), test_get_night_actions_filters_by_role() (+32 more)

### Community 77 - "RosterCog"
Cohesion: 0.21
Nodes (8): generate_roster_text(), Bot, Guild, Interaction, Live-ростер семьи: список участников по настроенным ролям.  Портировано из FamQ, Debounce: аккумулирует изменения и обновляет сообщение через 10 секунд., RosterCog, setup()

### Community 78 - "reaction_roles.py"
Cohesion: 0.21
Nodes (23): _avatar_url(), _display_name(), _game_for_guild(), _is_id(), mafia_game_advance_phase(), mafia_game_detail(), mafia_game_end(), mafia_games_list() (+15 more)

### Community 79 - "PublicBunkerAction.tsx"
Cohesion: 0.10
Nodes (19): test_build_board_embed_finished_loss_reveals_answer(), File, _avatar_bytes(), BoardView, build_board_embed(), _card_file(), GuessModal, PlayNowView (+11 more)

### Community 80 - "Leaderboard.tsx"
Cohesion: 0.19
Nodes (7): build_topic_message(), DailyTopicCog, BaseException, Bot, Ког «Ежедневная рубрика»: раз в день публикует тему/вопрос дня в заданный канал,, Публикует тему дня немедленно (используется циклом и ручным триггером         из, setup()

### Community 81 - "VoiceManager"
Cohesion: 0.12
Nodes (11): BaseException, Guild, Interaction, Message, View, Удаляет сообщения участника за последние 20 минут во всех каналах и тредах., Удаляет устаревшие записи из кэша спам-детектора., Обработка кнопок спам-инцидентов — работает и после перезапуска бота. (+3 more)

### Community 82 - "mafia.py"
Cohesion: 0.15
Nodes (23): isolated_config(), Тесты ядра верификации: настройки (выключена по умолчанию), проверка конфигураци, test_clamp_reverify_days(), test_consent_expiry(), test_is_configured_does_not_require_unverified_role(), test_is_configured_requires_verified_role(), test_rules_panel_text_when_rules_consent_enabled(), test_settings_disabled_by_default() (+15 more)

### Community 83 - "events.py"
Cohesion: 0.22
Nodes (19): create_embed_message(), create_embed_template(), delete_embed_template(), get_embed_message(), _get_guild_or_none(), _is_role_assignable(), list_embed_templates(), _parse_body() (+11 more)

### Community 84 - "ChetBot"
Cohesion: 0.67
Nodes (3): Web Dashboard Index HTML, React Root Mount Element, React Entry Point Script

### Community 85 - "ChannelInfo"
Cohesion: 0.04
Nodes (83): FakeChannel, FakeColor, FakeComponentRow, FakeCustomEmoji, FakeMessage, FakePermissions, FakeRole, test_parse_role_button_ids_extracts_matching_custom_ids() (+75 more)

### Community 86 - "MafiaLobbyView"
Cohesion: 0.13
Nodes (18): pick_bunker_conditions(), pick_catastrophe(), Данные для игры «Бункер»: возраст, телосложение, профессии, хобби, здоровье, стр, get_card_pools(), localize_character(), localize_game_scenario(), merge_bunker_conditions(), merge_catastrophe() (+10 more)

### Community 87 - "voice_logs.py"
Cohesion: 0.10
Nodes (39): isolated_state(), isolated_db(), Тесты wordle_db: игры дня, статистика со стриками, мета сервера (per-guild)., test_add_guess_accumulates_and_finishes(), test_daily_games_isolated_per_guild(), test_group_streak_gap_resets(), test_group_streak_grows_and_resets(), test_group_streak_isolated_per_guild() (+31 more)

### Community 88 - "test_auto_roles_routes.py"
Cohesion: 0.23
Nodes (17): build(), build_with_guild(), _full_config(), PUT /api/config не должен затирать ключи других разделов (авто-роли, приветствия, test_get_config_requires_auth(), test_get_config_returns_defaults_when_file_missing(), test_get_config_returns_stored_values(), test_put_config_preserves_foreign_keys() (+9 more)

### Community 89 - "Giveaways.tsx"
Cohesion: 0.22
Nodes (17): build(), FakeChoice, FakeInteraction, FakeResponse, Тесты кога «Казино»: /слоты и /монетка — через .callback(), паттерн test_fun_cog, test_coinflip_disabled_module(), test_coinflip_house_edge_reduces_payout(), test_coinflip_loss() (+9 more)

### Community 90 - "renderWithI18n.tsx"
Cohesion: 0.20
Nodes (21): add_command(), delete_command(), get_settings(), match_message(), _normalized(), Per-guild custom commands / auto-replies (exact or contains match)., Return first matching enabled command for message content, or None., update_command() (+13 more)

### Community 91 - "Welcome"
Cohesion: 0.12
Nodes (8): _game(), Тесты ядра блэкджека: очки руки, ход дилера, итоги, выплаты, форматирование., test_resolve_both_naturals_push(), test_resolve_compare_values(), test_resolve_dealer_bust_wins(), test_resolve_natural_blackjack(), test_resolve_player_bust_loses_even_if_dealer_busts(), test_twenty_one_from_three_cards_beats_dealer_twenty()

### Community 93 - "test_mafia_routes.py"
Cohesion: 0.08
Nodes (36): AutoReactionsCog, channel_matches_rule(), get_settings(), guild_emoji_tokens(), is_valid_emoji_token(), keywords_match(), matching_rules_for_message(), new_rule_id() (+28 more)

### Community 94 - "test_warns_routes.py"
Cohesion: 0.13
Nodes (20): Modal, VCTheme, apply_owner_permissions(), ChannelControlView, ensure_owner(), is_room_owner(), Bot, Interaction (+12 more)

### Community 95 - "test_xp_routes.py"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does SelectOption connect Mafia Game Engine to Discord Embed Builder, Supply Cog Tests?, Source Nodes

### Community 96 - "CTD"
Cohesion: 0.05
Nodes (83): force_login(), Log in for dashboard tests. Default active guild is 1 (app main).      Pass ``, build(), isolated_config(), test_get_defaults(), test_put_all_guild_emoji_mode(), test_put_include_requires_channels(), test_put_rules() (+75 more)

### Community 97 - "setup_static_routes()"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does force_login() connect Mock Services & Unit Tests to a wide array of system modules and tests?, Source Nodes

### Community 98 - "FakeAsset"
Cohesion: 0.30
Nodes (20): get_game(), build(), _cleanup_timer(), _make_lobby(), Тесты игрового цикла кога «Бункер»: старт игры (раздача карточек, голосовой кана, force_advance + _finish_discussion must not double-transition discussion→vote., Полный цикл: старт (4 игрока, вместимость 2) -> два раунда голосований -> игра з, test_concurrent_phase_advance_runs_once() (+12 more)

### Community 99 - "plugins"
Cohesion: 0.22
Nodes (8): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, typescript, warn

### Community 100 - "DocsSearch.tsx"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Are the inferred relationships involving mock objects (FakeMember, FakeGuild, FakeBot, FakeRole) with DashboardConfig and _StubForbidden correct?, Source Nodes

### Community 101 - "access_middleware.py"
Cohesion: 0.12
Nodes (19): publish_feedback_panel(), Embed, Message, upsert_embed_field(), add_reviewers(), build_mentions(), close_case(), create_feedback_case() (+11 more)

### Community 102 - "auto_roles.py"
Cohesion: 0.07
Nodes (33): build_game_started_embed(), build_lobby_cancelled_embed(), build_lobby_embed(), build_lynch_result_embed(), build_morning_embed(), build_result_embed(), build_vote_embed(), _display_name() (+25 more)

### Community 103 - "icons.svg"
Cohesion: 0.38
Nodes (6): Bluesky Icon, Discord Icon, Documentation Icon, GitHub Icon, Social Icon, X Icon

### Community 104 - "format_voice_time()"
Cohesion: 0.15
Nodes (23): get_stats(), build(), FakeInteraction, FakeMessage, FakeResponse, make_game(), Тесты кога «Блэкджек»: гейты, ставки, натуральный BJ, кнопки Ещё/Стоп/Удвоить., start_view_game() (+15 more)

### Community 105 - "DocsToc.tsx"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: What connects schema, typescript, oxc to the rest of the system?, Source Nodes

### Community 106 - "FakeVoiceChannel"
Cohesion: 0.21
Nodes (20): build(), build_with_channels(), _case(), test_decide_feedback_case_404_when_unknown(), test_decide_feedback_case_409_when_already_decided(), test_decide_feedback_case_409_when_category_deleted(), test_decide_feedback_case_approves_and_persists(), test_decide_feedback_case_rejects_non_boolean_approved() (+12 more)

### Community 108 - "Hero Image Graphic"
Cohesion: 1.00
Nodes (3): Hero Image Graphic, Cheterin Isometric Branding Concept, Layered Isometric Architecture Illustration

### Community 111 - "DocsSearch.tsx"
Cohesion: 0.32
Nodes (16): build(), Choice, FakeInteraction, Тесты команд /xp (add/set/clear) и /leaders в XPCog — вызов через .callback(), т, test_leaders_disabled_module(), test_leaders_empty_leaderboard(), test_leaders_footer_shows_page_and_total(), test_leaders_shows_ranked_members() (+8 more)

### Community 112 - "test_fun_routes.py"
Cohesion: 0.10
Nodes (30): Тесты рендера карточки ранга / профиля: PNG, GIF, косметика., test_hex_to_rgb(), test_render_profile_card_gif_is_gif(), test_render_profile_card_with_economy_stats(), test_render_rank_card_long_title_does_not_crash(), test_render_rank_card_with_custom_frame_and_title(), test_render_rank_card_without_cosmetics_produces_png(), _background() (+22 more)

### Community 120 - "DocsSearch.tsx"
Cohesion: 0.11
Nodes (16): test_load_events_reads_fresh_after_external_write(), test_load_events_returns_empty_events_dict_when_file_missing(), test_save_then_load_roundtrips(), create_participation_view(), CreateTeamCodeModal, EventManageSelect, EventNotifyModal, Events (+8 more)

### Community 121 - "test_members_list.py"
Cohesion: 0.10
Nodes (40): get_tempban_settings(), publish_tempban_warning(), Request, Response, update_tempban_settings(), _isolate(), Tempban / honeypot settings: action modes, counter, templates., test_action_modes() (+32 more)

### Community 122 - "test_member_detail.py"
Cohesion: 0.06
Nodes (35): build_expulsion_result_embed(), build_game_started_embed(), build_lobby_cancelled_embed(), build_lobby_embed(), build_result_embed(), build_vote_embed(), BunkerCog, BunkerLobbyView (+27 more)

### Community 123 - "DocsToc.tsx"
Cohesion: 0.25
Nodes (22): build(), FakeInteraction, Тесты кога Вордла — вызов через .callback()/методы кога, паттерн test_xp_command, test_announce_nobody_played(), test_announce_nobody_won_reveals_word(), test_announce_with_winner_crowns_best_and_streak(), test_commands_disabled_module(), test_daily_guess_edits_existing_live_card() (+14 more)

### Community 124 - "init"
Cohesion: 0.16
Nodes (18): generate_characters(), Раздаёт полную карточку персонажа каждому игроку.      unique_cards=True (по умо, Большинство голосов за исключение; ничья среди лидеров — никто не исключён., resolve_expulsion_vote(), isolated_config(), test_generate_characters_covers_all_players_with_full_field_set(), test_generate_characters_health_severity_matches_disease_presence(), test_generate_characters_relationship_card_links_to_another_player() (+10 more)

### Community 125 - "Request"
Cohesion: 0.06
Nodes (13): command_reason(), format_duration(), normalize_reason(), parse_duration(), parse_mute_duration(), Ядро команд модерации (/ban /kick /unban /clear): парсинг и форматирование срока, Ephemeral success reply; appends reason suffix only when a reason was given., Секунды из строки вида 10m/2h/7d/30s. ValueError с понятным текстом при неверном (+5 more)

### Community 126 - "EmbedBuilder.tsx"
Cohesion: 0.14
Nodes (21): get_settings(), normalize_nick(), parse_image_data_uri(), Per-guild bot profile (nick / avatar / banner) settings., Return nick string, empty string to clear, or None if omitted., Parse avatar/banner field.      Returns:       (payload_for_api, raw_bytes), save_settings(), _asset_url() (+13 more)

### Community 127 - "Button.tsx"
Cohesion: 0.09
Nodes (17): BALANCE_ADMIN_MAX, CosmeticsView, EconomyCog, _item_label(), Bot, Embed, Guild, Interaction (+9 more)

### Community 128 - "events.py"
Cohesion: 0.15
Nodes (20): test_localize_command_sets_english_base_and_locale_str(), test_slash_locale_keys_exist_in_both_languages(), test_translator_returns_russian_command_name(), test_translator_returns_russian_description(), Group, Locale, locale_str, _apply_name_localizations() (+12 more)

### Community 129 - "wordle_card.py"
Cohesion: 0.21
Nodes (16): _avatar_image(), _circle_avatar(), _draw_grid(), _font(), _grid_size(), _placeholder_avatar(), FreeTypeFont, Image (+8 more)

### Community 130 - "events.py"
Cohesion: 0.19
Nodes (14): build_case_timeline(), event_to_item(), _is_duplicate_warn_log(), Build a per-user moderation case timeline from warns_db + moderation_log.  Pure, Serialize a discord.Member or discord.User for the timeline header., Skip warn_manual log rows that already appear in warns_db (prefer DB)., Merge warns + filtered mod-log events for one user; newest first., serialize_timeline_user() (+6 more)

### Community 131 - "load_events"
Cohesion: 0.10
Nodes (25): Request, Response, starboard_get(), starboard_put(), _Emoji, isolated_config(), Starboard core: settings, threshold, emoji matching, channel validation., test_count_meets_threshold() (+17 more)

### Community 132 - "test_supply_routes.py"
Cohesion: 0.13
Nodes (48): build(), cosmetics_shop_config(), FakeInteraction, FakeResponse, Тесты кога «Экономика»: /баланс /перевести /монеты-топ /магазин — через .callbac, shop_config(), test_balance_disabled_module(), test_balance_shows_amount_and_rank() (+40 more)

### Community 133 - "ru.ts"
Cohesion: 0.18
Nodes (11): MemberLookupResult, resolve_guild_member(), FakeBot, FakeGuild, _StubHTTPException, _StubNotFound, test_falls_back_to_fetch_when_not_cached(), test_not_found_when_fetch_raises_notfound() (+3 more)

### Community 134 - "wordle.py"
Cohesion: 0.26
Nodes (18): build(), FakeInteraction, Тесты кога «Верификация»: выключена по умолчанию, join-роль, кнопка, re-verify., test_explicitly_disabled_no_join_role(), test_join_assigns_unverified_role(), test_join_without_unverified_role_configured_does_nothing(), test_reverify_allows_click_when_consent_expired(), test_rules_consent_success_message() (+10 more)

### Community 135 - "test_warns_routes.py"
Cohesion: 0.09
Nodes (45): _bot_py_files(), _collect_literal_i18n_keys(), Path, EN/RU strings for the same key should declare the same {placeholders}., Catch blackjack-style mismatches: code key not present in locale dicts., Regression: buttons/footer must not show raw keys like casino.bj.btn.hit., test_blackjack_locale_keys_resolve(), test_guild_t_uses_server_language() (+37 more)

### Community 136 - "Supply.tsx"
Cohesion: 0.15
Nodes (23): has_running_job(), MassAssignJob, run_mass_assign(), build(), test_mass_assign_all_except_bots_completes(), test_mass_assign_allows_job_when_other_guild_running(), test_mass_assign_concurrent_requests_only_one_job_starts(), test_mass_assign_job_marked_failed_on_unexpected_exception() (+15 more)

### Community 137 - ".__init__"
Cohesion: 0.10
Nodes (34): advanceBunkerGamePhase(), applyBunkerAbility(), BunkerCardPools, BunkerCharacter, BunkerGameDetail, BunkerGameSummary, BunkerPlayerRef, endBunkerGame() (+26 more)

### Community 138 - "Docs.tsx"
Cohesion: 0.29
Nodes (18): create_feedback_category(), decide_feedback_case(), delete_feedback_category(), get_feedback_case(), get_feedback_panel_settings(), _get_guild_or_none(), list_feedback_cases(), list_feedback_categories() (+10 more)

### Community 139 - "EventDetailPanel.tsx"
Cohesion: 0.16
Nodes (4): DraftEvent, EventPublishSelect, RegisterSoloModal, RegisterTeamCaptainModal

### Community 140 - "format_voice_time"
Cohesion: 0.18
Nodes (6): EventBuilderView, LimitsModal, OptionsModal, Interaction, TextChannel, TextModal

### Community 141 - "test_feedback_panel_routes.py"
Cohesion: 0.17
Nodes (5): Tests for shared fake-lobby seat builder used by bunker/mafia test commands., build_fake_seats(), FakeSeat, Shared helpers for admin fake-lobby test games (Bunker / Mafia).  Builds a seat, Return ``total_players`` seats: host first, then bots.      Raises ValueError if

### Community 142 - "setup_session"
Cohesion: 0.19
Nodes (16): Request, Response, timezone_get(), timezone_put(), Request, Response, voice_stats(), get_settings() (+8 more)

### Community 143 - "FakeResponse"
Cohesion: 0.26
Nodes (19): _decide_ticket(), _display_name(), family_birthday_delete(), family_birthday_set(), family_birthdays_list(), family_get(), family_put(), family_roster() (+11 more)

### Community 144 - "FakeResponse"
Cohesion: 0.10
Nodes (23): activity, admin, auth, common, community, credits, docsShell, landing (+15 more)

### Community 145 - "test_news_routes.py"
Cohesion: 0.17
Nodes (27): clear_rank_roles(), connect(), get_all_linked_users(), get_cached_matches(), get_db_path(), get_guild_settings(), get_linked_in_guild(), get_rank_roles() (+19 more)

### Community 146 - "test_auto_roles_routes.py"
Cohesion: 0.31
Nodes (7): Application, Path, setup_static_routes(), test_asset_path_serves_asset_file(), test_root_path_serves_index_html(), test_unmatched_path_serves_index_html(), test_well_known_discord_not_spa_fallback()

### Community 147 - "test_supply_routes.py"
Cohesion: 0.14
Nodes (33): get_settings(), Настройки модуля сервера с дефолтами (выключен по умолчанию)., assign_character(), create_game(), build(), _FakeBunkerCog, _sample_character(), test_advance_phase_calls_cog() (+25 more)

### Community 148 - "lockdown.py"
Cohesion: 0.13
Nodes (15): action_log_fields(), format_user_ref(), Common log style: @mention (`id`), with name (`id`) fallback when mention is una, Кто / Кого / Причина (only if non-empty) / Дополнительно (only if non-empty)., actor_ref(), build_action_log_embed(), build_user_action_embed(), Any (+7 more)

### Community 149 - "test_xp_routes.py"
Cohesion: 0.23
Nodes (14): isolated_state(), test_reverify_sweeper_expires_member(), Тесты SQLite-хранилища согласий верификации., test_record_get_clear_and_list(), clear_consent(), connect(), get_consent(), get_db_path() (+6 more)

### Community 150 - "mafia.py"
Cohesion: 0.29
Nodes (9): build(), FakeAutoModCog, test_create_warn(), test_create_warn_validation(), test_create_warn_without_cog_still_succeeds(), test_delete_warn(), test_delete_warn_rejects_other_guild(), test_list_warns_empty() (+1 more)

### Community 151 - "format_voice_time"
Cohesion: 0.38
Nodes (4): Lockdown, Guild, Interaction, setup()

### Community 152 - "FakeVoiceChannel"
Cohesion: 0.10
Nodes (49): add_player(), add_round_event(), connect(), count_players(), create_ability_announcement(), get_ability_announcement(), get_active_game_in_channel(), get_db_path() (+41 more)

### Community 153 - "Fun.tsx"
Cohesion: 0.22
Nodes (13): build(), FakeDailyTopicCog, isolated_config(), test_create_topic_validation(), test_get_defaults(), test_post_now(), test_post_now_no_cog(), test_post_now_requires_channel() (+5 more)

### Community 154 - "InvitesCog"
Cohesion: 0.21
Nodes (15): build(), _cleanup_timer(), isolated_state(), Tests for MafiaCog's dashboard host overrides: force_advance_phase / force_end_g, _setup_game(), test_force_advance_phase_night_to_day(), test_force_advance_phase_returns_false_for_inactive_game(), test_force_advance_phase_returns_false_for_missing_game() (+7 more)

### Community 155 - "_FakeMember"
Cohesion: 0.18
Nodes (17): test_owner_alerts_mass_ban_threshold(), test_should_post_weekly_digest_false_when_already_posted(), test_should_post_weekly_digest_false_when_disabled(), test_should_post_weekly_digest_requires_monday_and_channel(), test_weekly_digest_channel_falls_back_to_alert_channel(), test_weekly_digest_settings_roundtrip(), get_settings(), mark_weekly_digest_posted() (+9 more)

### Community 156 - "Casino.tsx"
Cohesion: 0.16
Nodes (13): Shared embed_style palette and helpers., test_as_color_default_and_passthrough(), test_make_embed_accepts_int_color_and_footer(), test_make_embed_defaults_timestamp_and_color(), as_color(), make_embed(), module_footer(), Any (+5 more)

### Community 157 - "lang_for"
Cohesion: 0.47
Nodes (8): _check_channel(), _check_role(), get_config(), Request, Response, update_config(), _validate_relations(), _validate_structure()

### Community 158 - "Fun.tsx"
Cohesion: 0.15
Nodes (12): BracketDetail, BracketFormat, BracketMatch, deleteBracket(), disableBracketShare(), enableBracketShare(), fetchBracketDetail(), setBracketMatchWinner() (+4 more)

### Community 159 - "resolve_ticket"
Cohesion: 0.28
Nodes (4): Bot, Scheduled messages cog: posts due one-shot / daily messages., ScheduledMessagesCog, setup()

### Community 160 - "welcome.py"
Cohesion: 0.10
Nodes (31): polls_end(), polls_get(), polls_list(), _public_poll(), Request, Response, isolated(), test_create_vote_tallies_end() (+23 more)

### Community 161 - "test_auto_roles_routes.py"
Cohesion: 0.25
Nodes (16): build(), test_birthday_set_invalid_date(), test_birthday_set_unknown_member(), test_birthdays_crud(), test_get_defaults(), test_put_then_get(), test_put_validation(), test_requires_auth() (+8 more)

### Community 162 - "load_dashboard_config"
Cohesion: 0.11
Nodes (22): Henrik client concurrency / retry behaviour., Concurrent jobs must finish; throttle must not hold the concurrency slot., test_henrik_semaphore_no_deadlock(), account(), account_by_puuid(), close_client(), _enc(), friendly_error() (+14 more)

### Community 163 - "EventDetailPanel.tsx"
Cohesion: 0.12
Nodes (28): economy_get(), economy_put(), economy_reset_all(), economy_set_balance(), economy_top(), economy_weekly_report(), Request, Response (+20 more)

### Community 164 - "test_members_list.py"
Cohesion: 0.13
Nodes (13): default_bunker_capacity(), is_game_over(), _pick_age(), _pick_body_type(), Ядро игры «Бункер»: конфигурация, генерация персонажей, подсчёт голосов, условие, Половина игроков (округление вниз, минимум 1) — если ведущий не задал своё число, save_config(), English card pools for the Bunker survival tabletop game. (+5 more)

### Community 166 - "test_supply_routes.py"
Cohesion: 0.21
Nodes (19): build(), _FakeMafiaCog, test_advance_phase_calls_cog(), test_advance_phase_rejects_other_guild(), test_advance_phase_returns_409_when_game_not_active(), test_advance_phase_service_unavailable_without_cog(), test_end_game_calls_cog(), test_end_game_rejects_other_guild() (+11 more)

### Community 167 - "test_ctd_routes.py"
Cohesion: 0.15
Nodes (9): build_match_reply(), build_profile_reply(), load_match_payload(), load_profile_payload(), MatchNavView, ProfileNavView, Bot, ValChecker cog — Valorant profile / match / tracking (port of ValChecker Node bo (+1 more)

### Community 168 - "test_news_routes.py"
Cohesion: 0.17
Nodes (3): Guild, Regions relevant to at least one enabled guild (linked members there)., ValCheckerCog

### Community 169 - "birthdays_db.py"
Cohesion: 0.17
Nodes (21): connect(), delete_birthday(), for_date(), get_birthday(), get_db_path(), init(), is_valid_mm_dd(), list_birthdays() (+13 more)

### Community 170 - "test_feedback_panel_routes.py"
Cohesion: 0.16
Nodes (18): isolated(), test_check_module_health_flags_dead_channel(), test_check_module_health_flags_missing_verified_role(), test_check_module_health_flags_valchecker_dead_match_channel(), test_check_module_health_flags_valchecker_missing_match_channel(), test_check_module_health_ignores_disabled_module(), test_check_module_health_ok_when_channel_exists(), test_check_module_health_ok_when_verified_role_exists() (+10 more)

### Community 171 - "test_roles.py"
Cohesion: 0.67
Nodes (3): main(), One-off generator for locales/{ru,en}/slash.py — run from repo root., render()

### Community 172 - "test_access.py"
Cohesion: 0.26
Nodes (12): test_resolve_banner_url_returns_empty_when_unset(), test_resolve_banner_url_uses_custom_setting(), build_panel_payload(), default_panel_embed_spec(), get_settings(), _load_raw(), panel_banner_url(), Feedback panel appearance customization. (+4 more)

### Community 173 - "test_wordle_routes.py"
Cohesion: 0.08
Nodes (30): _cached_display(), invites_get(), invites_put(), Request, Response, Resolve display names with cache-first lookup and deduped concurrent fetches., _resolve_displays(), isolated_settings() (+22 more)

### Community 174 - "casino_db.py"
Cohesion: 0.15
Nodes (21): connect(), _ensure_row(), get_db_path(), get_main_guild_id(), __getattr__(), init(), leaderboard(), Connection (+13 more)

### Community 175 - "Mafia.tsx"
Cohesion: 0.20
Nodes (17): Request, Response, timed_roles_delete(), timed_roles_list(), isolated(), test_add_and_expired(), add(), connect() (+9 more)

### Community 176 - "custom_commands.py"
Cohesion: 0.33
Nodes (9): test_append_event_defaults_moderator_to_none_for_automatic_events(), test_append_event_stores_all_fields(), test_append_event_trims_to_max_entries(), test_append_then_load_returns_newest_first(), test_load_events_returns_empty_list_on_corrupt_json(), test_load_events_returns_empty_list_when_file_missing(), append_event(), load_events() (+1 more)

### Community 177 - "test_warns_routes.py"
Cohesion: 0.09
Nodes (19): FakeFollowup, FakeResponse, build(), FakeFollowup, FakeInteraction, FakeResponse, Тесты /профиль: GIF по умолчанию, fallback на PNG при огромном файле., test_profile_command_falls_back_to_png_when_gif_huge() (+11 more)

### Community 180 - "moderation_log.py"
Cohesion: 0.36
Nodes (12): automod_create_escalation(), automod_delete_escalation(), automod_get(), automod_update_enabled(), automod_update_escalation(), automod_update_filter(), automod_update_manual_warn_duration(), _is_str_list() (+4 more)

### Community 181 - "save_config"
Cohesion: 0.26
Nodes (10): build(), Test that partial failures during deactivate are logged with Ошибки field in emb, Test that partial failures are logged with Ошибки field in embed., _StubForbidden, test_activate_then_status_then_deactivate(), test_activate_with_partial_errors_logs_error_field(), test_deactivate_with_partial_errors_logs_error_field(), test_deactivate_without_backup_409() (+2 more)

### Community 182 - "test_news_routes.py"
Cohesion: 0.32
Nodes (13): close_event_route(), create_event(), delete_event_route(), get_event(), list_events(), notify_event_route(), Request, Response (+5 more)

### Community 183 - "test_members_list.py"
Cohesion: 0.23
Nodes (12): language_get(), language_put(), Request, Response, test_get_settings_defaults_respect_guild_language(), test_settings_defaults_respect_guild_language(), test_language_core_set_and_get(), test_settings_defaults_respect_guild_language() (+4 more)

### Community 184 - "VerificationCog"
Cohesion: 0.30
Nodes (10): build(), test_get_auto_roles_defaults_to_empty_when_file_missing(), test_get_auto_roles_requires_auth(), test_get_auto_roles_returns_stored_values(), test_update_auto_roles_persists_valid_roles(), test_update_auto_roles_rejects_managed_role(), test_update_auto_roles_rejects_non_list_body(), test_update_auto_roles_rejects_role_above_bot() (+2 more)

### Community 185 - "test_voice_panel_state.py"
Cohesion: 0.24
Nodes (8): build(), FakeSupplyCog, test_close_and_cancel(), test_create_supply(), test_create_supply_validation(), test_overview_empty(), test_overview_with_data(), test_requires_auth()

### Community 186 - "Mafia.tsx"
Cohesion: 0.20
Nodes (8): RawMessageDeleteEvent, Bot, Embed, Message, RawReactionActionEvent, Starboard: mirror highly-reacted messages into a configured channel., setup(), StarboardCog

### Community 187 - "embed_builder.py"
Cohesion: 0.26
Nodes (13): get_welcome_settings(), Request, Response, Send a sample welcome (channel and/or DM) using the dashboard user as the member, _serialize_messages(), update_welcome_settings(), _validate_messages_payload(), welcome_test() (+5 more)

### Community 188 - "test_feedback_panel_routes.py"
Cohesion: 0.26
Nodes (6): Embed, Guild, Message, При старте бота проверяем, нет ли пользователей в бан-листе         с причиной s, setup(), TempBan

### Community 189 - "test_supply_routes.py"
Cohesion: 0.05
Nodes (62): AntiRaidCog, get_settings(), is_suspicious_account(), JoinTracker, datetime, Ядро модуля «Антирейд»: детект всплеска входов новых участников.  Без импорта di, Настройки модуля сервера с дефолтами. enabled=False по умолчанию — модуль не, Считается ли аккаунт «свежим» (подозрительным) на момент входа. (+54 more)

### Community 190 - "test_auto_roles_routes.py"
Cohesion: 0.20
Nodes (11): test_publish_verification_panel_helper_sends_welcome_text(), _button_label(), publish_verification_panel(), Bot, Message, TextChannel, Ког «Верификация»: панель «Я не бот» / согласия с правилами для новичков.  ВЫКЛЮ, Publish the verification panel to `channel`. Shared by /verify_setup and the das (+3 more)

### Community 191 - "VerificationCog"
Cohesion: 0.23
Nodes (3): Guild, Interaction, VerificationCog

### Community 192 - "setup_session"
Cohesion: 0.21
Nodes (15): Request, Response, valchecker_get(), valchecker_put(), any_enabled_match_guild(), _clamp_poll(), get_settings(), ValChecker module settings in settings_db (dashboard source of truth). (+7 more)

### Community 193 - "build_game_started_embed"
Cohesion: 0.20
Nodes (6): Bot, Interaction, Range, Timed roles: slash assign + background sweeper., setup(), TimedRolesCog

### Community 194 - "Mafia.tsx"
Cohesion: 0.20
Nodes (14): AuditEntry, AuditModerator, AuditPage, fetchAudit(), AuditPage(), csvEscape(), downloadAuditCsv(), EntryRow() (+6 more)

### Community 196 - "test_module_test_send.py"
Cohesion: 0.20
Nodes (21): Request, Response, sticky_delete(), sticky_get(), sticky_settings(), sticky_test(), sticky_upsert(), isolated_config() (+13 more)

### Community 197 - "voice_logs.py"
Cohesion: 0.29
Nodes (4): Lock, Message, TextChannel, Repost sticky. Returns False if send failed (old message left intact).

### Community 198 - "test_welcome_routes.py"
Cohesion: 0.16
Nodes (5): _fake_match(), Unit tests for ValChecker stats formulas (ACS, HS%, WR, KD)., test_aggregate_wr_kd(), test_summarize_acs_and_hs(), test_to_cache_row_won_none()

### Community 199 - "test_news_routes.py"
Cohesion: 0.19
Nodes (24): Request, Response, scheduled_messages_create(), scheduled_messages_delete(), scheduled_messages_get(), scheduled_messages_settings(), scheduled_messages_update(), _validate_message_fields() (+16 more)

### Community 200 - "auto_reactions.py"
Cohesion: 0.42
Nodes (4): Button, Interaction, Persistent view: кнопки работают и после перезапуска бота., SupplyView

### Community 201 - "SupplyView"
Cohesion: 0.18
Nodes (17): audit_middleware(), describe_action(), normalize_stored_action(), Request, Аудит действий дашборда: каждое мутирующее действие модератора пишется в stats.d, Map legacy 'PUT /api/wordle' (and similar) rows to i18n keys., audit_list(), Request (+9 more)

### Community 202 - "embed_style.py"
Cohesion: 0.31
Nodes (10): _deny_disabled(), _deny_disabled_followup(), _lang(), _module_ok(), Interaction, Range, User, Return True if denied (and reply sent). (+2 more)

### Community 203 - "test_ctd_routes.py"
Cohesion: 0.12
Nodes (17): _has_legacy_role_access(), Переходный грант по роли на активном сервере (если задан DASHBOARD_ACCESS_ROLE_I, Гейт доступа к серверу (Фаза 2.3): сессия → активный сервер → Manage Server., Гейт для списка серверов бота — намеренно хардкод-роль, см. access.py., require_dashboard_access(), require_super_admin(), fun_get(), fun_put() (+9 more)

### Community 204 - "localize_character"
Cohesion: 0.33
Nodes (3): build_setup_panel(), SetupLinkModal, SetupView

### Community 205 - "guild_context.py"
Cohesion: 0.57
Nodes (6): get_ctd(), put_ctd(), Request, Response, CTD (тикеты) — привилегия основного сервера (Фаза 2b MULTIGUILD_PLAN.md).  Настр, _require_main_guild()

### Community 206 - "test_news_routes.py"
Cohesion: 0.14
Nodes (14): ChetBot, command_sync_mode(), get_main_guild_id(), main(), on_guild_join(), on_guild_remove(), on_ready(), Embed (+6 more)

### Community 207 - "test_voice_stats_routes.py"
Cohesion: 0.43
Nodes (7): build(), isolated_config(), test_get_defaults(), test_put_allows_unlimited_max_bet(), test_put_then_get(), test_put_validation(), test_requires_login()

### Community 208 - "pick_bunker_conditions"
Cohesion: 0.12
Nodes (25): test_status_color_and_label(), Ядро модуля «Семья» (портировано из FamQ): конфигурация, парсинг дат ДР, цвета/л, status_color(), status_label(), add_custom_emoji_reaction(), build_full_embed(), build_mini_embed(), build_ticket_result_embed() (+17 more)

### Community 209 - "resolve_ticket"
Cohesion: 0.22
Nodes (5): BirthdaysCog, Bot, Interaction, Guild-wide birthday calendar cog., setup()

### Community 210 - "HelpView"
Cohesion: 0.19
Nodes (10): HelpCategorySelect, HelpCog, HelpView, Bot, Button, Embed, Interaction, Member-facing /help — category select + leaders-style pagination. (+2 more)

### Community 211 - "spam_core.py"
Cohesion: 0.23
Nodes (11): get_spam_settings(), Request, Response, update_spam_settings(), test_message_limit_with_attachments(), test_spam_settings_defaults(), test_spam_settings_roundtrip(), get_settings() (+3 more)

### Community 212 - "test_auto_roles_routes.py"
Cohesion: 0.13
Nodes (23): FakeThread, test_fake_bot_fetch_user_falls_back_when_not_in_guild(), test_fake_bot_fetch_user_raises_when_nowhere_found(), test_fake_bot_get_channel_finds_channel_and_thread(), test_fake_bot_update_file_records_calls(), test_fake_member_send_raises_when_configured(), test_fake_member_send_records_dm(), test_fake_thread_edit_records_archived_and_locked() (+15 more)

### Community 213 - "test_welcome_routes.py"
Cohesion: 0.39
Nodes (7): build(), isolated_state(), Тесты кога OwnerAlertsCog: еженедельный дайджест активности дашборда., test_build_weekly_digest_embed_empty(), test_build_weekly_digest_embed_groups_actions(), test_post_weekly_digest_false_without_channel(), test_post_weekly_digest_sends_and_marks_posted()

### Community 214 - "adminPanel.js"
Cohesion: 0.19
Nodes (21): member_warns_create(), member_warns_list(), Request, Response, warn_delete(), test_active_warn_count_excludes_expired_and_removed(), test_add_and_get_warn(), test_add_warn_without_moderator_is_automod() (+13 more)

### Community 215 - "SupplyView"
Cohesion: 0.29
Nodes (9): Request, Response, wordle_get(), wordle_put(), test_settings_defaults(), test_settings_roundtrip(), get_settings(), Настройки модуля сервера с дефолтами (выключен по умолчанию).      channel_id — (+1 more)

### Community 216 - "README.md"
Cohesion: 0.15
Nodes (12): 1. Клонирование и зависимости, 2. Панель (frontend), 3. Запуск, Cheterin, ValChecker, Быстрый старт, Возможности, Документы (+4 more)

### Community 217 - "starboard_db.py"
Cohesion: 0.36
Nodes (8): build(), isolated_settings_db(), CTD-настройки — привилегия мейна (Фаза 2b): роут доступен только когда активный, test_ctd_forbidden_when_active_guild_not_main(), test_ctd_requires_auth(), test_get_ctd_defaults_on_main_guild(), test_put_and_get_ctd_round_trip(), test_put_ctd_404_when_role_missing()

### Community 218 - "test_xp_rank_cog.py"
Cohesion: 0.33
Nodes (4): has_moderator_access(), _FakeMember, _FakePermissions, test_has_moderator_access()

### Community 219 - "aiohttp Dependency"
Cohesion: 0.48
Nodes (6): build(), isolated_config(), test_get_defaults_all_disabled(), test_put_then_get(), test_put_validation(), test_requires_auth()

### Community 221 - "StickyMessages.tsx"
Cohesion: 0.13
Nodes (19): createScheduledMessage(), deleteScheduledMessage(), deleteSticky(), fetchScheduledMessages(), fetchSticky(), ScheduledMessagesSettings, setScheduledMessagesEnabled(), setStickyEnabled() (+11 more)

### Community 222 - "Interaction"
Cohesion: 0.17
Nodes (8): ApplicationModalPart1, ApplicationModalPart2, ContinueApplicationView, OpenTicketView, Button, Interaction, setup(), TicketControlView

### Community 224 - "warns_db.py"
Cohesion: 0.23
Nodes (15): isolated_storage(), isolated_db(), isolated_db(), add_warn(), db_connect(), db_init(), get_active_warn_count(), get_db_path() (+7 more)

### Community 225 - "test_voice_panel_state.py"
Cohesion: 0.17
Nodes (13): isolated_settings(), Тесты состояния панели голосовых комнат (voice_rooms) — per-guild в settings_db., test_on_ready_publishes_panel_for_each_guild(), test_panel_state_defaults_empty(), test_panel_state_is_per_guild(), test_panel_state_round_trip(), build_embed(), load_panel_state() (+5 more)

### Community 226 - "python-dotenv Dependency"
Cohesion: 0.27
Nodes (7): CustomCommandsCog, _embed_from_spec(), Bot, Embed, Message, Custom commands / auto-replies cog., setup()

### Community 227 - "language_core.py"
Cohesion: 0.29
Nodes (10): connect(), delete(), find_by_starboard_message(), get_db_path(), get_starboard_message(), init(), Connection, Starboard message mapping: original message_id → starboard message_id. (+2 more)

### Community 228 - "test_verification_routes.py"
Cohesion: 0.30
Nodes (13): build(), isolated_config(), test_get_defaults_disabled(), test_publish_maps_discord_forbidden(), test_publish_maps_discord_http_exception(), test_publish_rejects_missing_channel(), test_publish_rejects_when_module_disabled(), test_publish_rejects_when_not_configured() (+5 more)

### Community 229 - "voice_logs.py"
Cohesion: 0.36
Nodes (11): Client, get_log_channel_id(), log_action(), log_error(), log_security(), log_unhide_action(), Color, Exception (+3 more)

### Community 230 - "setup_session"
Cohesion: 0.30
Nodes (10): cookie_secure_flag(), derive_fernet_key(), Application, Whether Set-Cookie should use Secure.      Explicit `DASHBOARD_COOKIE_SECURE`, setup_session(), test_cookie_secure_flag_detects_https_frontend(), test_cookie_secure_flag_from_env(), test_derive_fernet_key_differs_per_secret() (+2 more)

### Community 231 - "test_ctd_routes.py"
Cohesion: 0.06
Nodes (33): guild_context_middleware(), Request, Per-request guild-контекст (Фаза 2.3).  Раньше гильдия была одна на всё приложен, FakeAuditLogExtra, _FakeChannelType, FakeGuildInner, FakeVoiceChannel, build() (+25 more)

### Community 233 - "owner_alerts.py"
Cohesion: 0.39
Nodes (8): owner_alerts_get(), owner_alerts_put(), owner_alerts_test(), Request, Response, setup_health_get(), critical_perms_missing(), guild_perms: discord.Permissions-like with attributes.

### Community 234 - "test_feedback_panel_routes.py"
Cohesion: 0.60
Nodes (5): Request, Response, verification_get(), verification_publish(), verification_put()

### Community 235 - "xp.py"
Cohesion: 0.20
Nodes (8): channel_allowed(), _fmt_voice(), member_has_ignored_role(), Bot, Message, Ког системы уровней: XP за текст, обработка уровней и наград, /ранг, /профиль., Формат времени голоса Ч:ММ:СС (как в JuniperBot)., setup()

### Community 236 - "test_tempban_routes.py"
Cohesion: 0.24
Nodes (5): _get(), load_assets(), Any, ClientSession, valorant-api.com asset lookups (agents / maps / competitive tiers).

### Community 237 - "auto_roles.py"
Cohesion: 0.48
Nodes (6): get_auto_roles(), _get_guild_or_none(), _is_role_assignable(), Request, Response, update_auto_roles()

### Community 238 - "welcome.py"
Cohesion: 0.24
Nodes (3): Invite, setup(), Welcome

### Community 239 - "test_fun_routes.py"
Cohesion: 0.39
Nodes (8): build(), isolated_config(), test_get_defaults(), test_put_auto_emoji_roundtrip_and_validation(), test_put_then_get(), test_put_validation(), test_put_zero_disables_punishment_and_cooldown(), test_requires_auth()

### Community 240 - "VoiceManager"
Cohesion: 0.31
Nodes (4): _config_channel_id(), GuildChannel, VoiceState, VoiceManager

### Community 241 - "test_antiraid_routes.py"
Cohesion: 0.48
Nodes (6): build(), isolated_config(), test_get_defaults_disabled(), test_put_then_get(), test_put_validation(), test_requires_login()

### Community 242 - "test_timeout_routes.py"
Cohesion: 0.53
Nodes (5): build(), isolated_db(), test_timeout_invalid_duration(), test_timeout_member(), test_untimeout_member()

## Knowledge Gaps
- **276 isolated node(s):** `$schema`, `typescript`, `oxc`, `react/rules-of-hooks`, `warn` (+271 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SelectOption` connect `.__init__` to `format_voice_time`?**
  _High betweenness centrality (0.206) - this node is a cross-community bridge._
- **Why does `Choice` connect `DocsSearch.tsx` to `events.py`, `Test Fake Bot`, `Automod Route Tests`, `family.py`, `embed_style.py`, `format_voice_time`, `Automod API Client`, `PublicBunkerAction.tsx`, `test_warns_routes.py`, `XPCog`, `Family Birthdays`, `format_voice_time`, `Streams API Client`?**
  _High betweenness centrality (0.144) - this node is a cross-community bridge._
- **Why does `FakeMember` connect `Streams API Client` to `Game Settings & Bunker DB`, `test_supply_routes.py`, `Test Fake Bot`, `wordle.py`, `Supply.tsx`, `Giveaways Routes`, `test_supply_routes.py`, `mafia.py`, `Fun.tsx`, `InvitesCog`, `Voice Rooms Routes`, `Mafia Discord Cog`, `test_auto_roles_routes.py`, `Lockdown Routes`, `test_supply_routes.py`, `Brackets Client Tests`, `test_warns_routes.py`, `save_config`, `VerificationCog`, `test_feedback_routes.py`, `test_voice_panel_state.py`, `Docs.tsx`, `test_supply_routes.py`, `SupplyView`, `test_voice_stats_routes.py`, `test_auto_roles_routes.py`, `ChannelInfo`, `test_welcome_routes.py`, `test_auto_roles_routes.py`, `starboard_db.py`, `Giveaways.tsx`, `aiohttp Dependency`, `aiohttp-session Dependency`, `Pillow Dependency`, `CTD`, `FakeAsset`, `test_verification_routes.py`, `test_ctd_routes.py`, `format_voice_time()`, `FakeVoiceChannel`, `test_fun_routes.py`, `DocsSearch.tsx`, `test_antiraid_routes.py`, `test_timeout_routes.py`, `DocsToc.tsx`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Are the 42 inferred relationships involving `FakeMember` (e.g. with `DashboardConfig` and `_StubForbidden`) actually correct?**
  _`FakeMember` has 42 INFERRED edges - model-reasoned connections that need verification._
- **Are the 42 inferred relationships involving `FakeGuild` (e.g. with `DashboardConfig` and `_StubForbidden`) actually correct?**
  _`FakeGuild` has 42 INFERRED edges - model-reasoned connections that need verification._
- **Are the 41 inferred relationships involving `FakeBot` (e.g. with `DashboardConfig` and `_StubForbidden`) actually correct?**
  _`FakeBot` has 41 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `typescript`, `oxc` to the rest of the system?**
  _276 weakly-connected nodes found - possible documentation gaps or missing edges._