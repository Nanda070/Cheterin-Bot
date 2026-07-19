# Graph Report - Cheterin_Bot_Dashboard  (2026-07-19)

## Corpus Check
- 354 files · ~205,367 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 4272 nodes · 11259 edges · 161 communities (154 shown, 7 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 206 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0bcd6250`
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
- Reaction Roles Client
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
- PublicMafiaAction.tsx
- Welcome
- access_middleware.py
- test_mafia_routes.py
- test_warns_routes.py
- test_xp_routes.py
- config.py
- setup_static_routes()
- FakeAsset
- plugins
- DocsSearch.tsx
- xp_card.py
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
- Response
- Button.tsx
- events.py
- wordle_card.py
- events.py
- load_events
- test_supply_routes.py
- PublicMafiaAction.tsx
- wordle.py
- test_warns_routes.py
- Supply.tsx
- .__init__
- test_roles.py
- test_wordle_routes.py
- format_voice_time
- test_feedback_panel_routes.py
- DocsSearch.tsx
- FakeResponse
- FakeResponse
- test_news_routes.py
- test_auto_roles_routes.py
- test_supply_routes.py
- test_mass_role_jobs.py
- test_xp_routes.py
- test_wordle_routes.py
- format_voice_time
- FakeVoiceChannel
- AntiRaidCog
- SupplyView
- lockdown.py
- ChetBot
- auth.py
- test_antiraid_routes.py
- test_member_detail.py
- test_wordle_routes.py

## God Nodes (most connected - your core abstractions)
1. `force_login()` - 323 edges
2. `FakeMember` - 287 edges
3. `FakeGuild` - 220 edges
4. `FakeBot` - 203 edges
5. `apiFetch()` - 122 edges
6. `FakeChannel` - 114 edges
7. `FakeRole` - 107 edges
8. `make_moderation_app()` - 86 edges
9. `jsonInit()` - 75 edges
10. `react` - 61 edges

## Surprising Connections (you probably didn't know these)
- `Unified settings.db Per-Guild Storage` --references--> `get_settings()`  [INFERRED]
  MULTIGUILD_PLAN.md → bunker_core.py
- `Phase 2.3: OAuth Guilds Scope and Server Selection` --references--> `callback()`  [EXTRACTED]
  MULTIGUILD_PLAN.md → dashboard/backend/auth.py
- `FakeChoice` --uses--> `CasinoCog`  [INFERRED]
  dashboard/backend/tests/test_casino_cog.py → casino.py
- `FakeInteraction` --uses--> `CasinoCog`  [INFERRED]
  dashboard/backend/tests/test_casino_cog.py → casino.py
- `FakeInteraction` --uses--> `EconomyCog`  [INFERRED]
  dashboard/backend/tests/test_economy_cog.py → economy.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Phase 2 Multi-Guild Core** — multiguild_plan_settings_db, multiguild_plan_guild_dimension_migration, multiguild_plan_oauth_guilds_flow, multiguild_plan_bot_global_sync [EXTRACTED 1.00]
- **Main Guild Privileged Features** — multiguild_plan_main_guild_id, multiguild_plan_ctd_main_guild_gate, multiguild_plan_news_relay_superadmin, multiguild_plan_superadmin_main_check [EXTRACTED 1.00]
- **RU/EN Localization Program** — multiguild_plan_i18n_infrastructure, multiguild_plan_two_level_language_model, multiguild_plan_slash_command_localization, multiguild_plan_bunker_cards_bilingual [EXTRACTED 1.00]
- **Backend Runtime Dependencies** — requirements_discord_py, requirements_python_dotenv, requirements_aiohttp, requirements_aiohttp_session, requirements_cryptography, requirements_pillow [INFERRED 0.95]
- **Dashboard Application Architecture** — readme_chetbot, readme_dashboard, dashboard_frontend_index_html [INFERRED 0.85]
- **External Platform and Social Icons Set** — dashboard_frontend_public_icons_bluesky_icon, dashboard_frontend_public_icons_discord_icon, dashboard_frontend_public_icons_github_icon, dashboard_frontend_public_icons_x_icon, dashboard_frontend_public_icons_social_icon [INFERRED 0.85]
- **Dashboard UI Icon Asset Set** — dashboard_frontend_public_icons_bluesky_icon, dashboard_frontend_public_icons_discord_icon, dashboard_frontend_public_icons_documentation_icon, dashboard_frontend_public_icons_github_icon, dashboard_frontend_public_icons_social_icon, dashboard_frontend_public_icons_x_icon [EXTRACTED 1.00]
- **Docs Page User Interface** — dashboard_frontend_src_pages_docs, dashboard_frontend_src_components_docs_docsbanner, dashboard_frontend_src_assets_docs_banner [INFERRED 0.90]
- **Hero Page Visual Branding Elements** — dashboard_frontend_src_assets_hero, dashboard_frontend_src_assets_hero_branding, dashboard_frontend_src_assets_hero_layered_stack [INFERRED 0.85]

## Communities (161 total, 7 thin omitted)

### Community 0 - "Game Settings & Bunker DB"
Cohesion: 0.17
Nodes (21): init(), update_game(), isolated_state(), isolated_db(), _make_game(), База, созданная до появления voice_channel_id/vote_message_id/unique_cards,, test_add_player_rejects_duplicate(), test_create_and_get_game() (+13 more)

### Community 1 - "Supply Module"
Cohesion: 0.09
Nodes (47): _display_name(), _finalize(), Request, Response, _serialize_supply(), supply_cancel(), supply_close(), supply_create() (+39 more)

### Community 2 - "Dashboard App Bootstrap"
Cohesion: 0.07
Nodes (52): AppRunner, create_app(), json_error_middleware(), Application, Path, start_dashboard(), ConfigError, DashboardConfig (+44 more)

### Community 3 - "Test Fake Channels"
Cohesion: 0.05
Nodes (50): FakeAsset, FakeChannel, FakeColor, FakeComponentRow, FakeCustomEmoji, FakeMessage, FakePermissions, test_parse_role_button_ids_extracts_matching_custom_ids() (+42 more)

### Community 4 - "API Client Types"
Cohesion: 0.03
Nodes (76): AntiRaidSettings, AuditEntry, AutoRolesSettings, BracketStandingsRow, BunkerAbilityAnnouncement, BunkerAdditionalInfo, BunkerAgeInfo, BunkerBodyType (+68 more)

### Community 5 - "Test Fake Bot"
Cohesion: 0.06
Nodes (49): FakeBot, FakeGuild, FakeThread, make_client_app(), test_guild_unavailable_gets_503(), test_member_not_in_guild_gets_403(), test_member_with_access_reaches_handler(), test_member_without_access_role_gets_403() (+41 more)

### Community 6 - "Automod Route Tests"
Cohesion: 0.06
Nodes (74): force_login(), build(), test_escalation_crud(), test_escalation_validation(), test_get_defaults(), test_requires_auth(), test_update_filter(), test_update_filter_not_found() (+66 more)

### Community 7 - "Tournament Brackets"
Cohesion: 0.07
Nodes (61): create_bracket(), create_bracket_v2(), _de_get_match(), _de_match(), _de_recompute_match(), _de_resolve(), extract_entries_from_event(), generate_de() (+53 more)

### Community 8 - "Feedback Cases"
Cohesion: 0.07
Nodes (52): create_feedback_category(), decide_feedback_case(), delete_feedback_category(), get_feedback_case(), _get_guild_or_none(), list_feedback_cases(), list_feedback_categories(), publish_feedback_panel_route() (+44 more)

### Community 9 - "Giveaways Routes"
Cohesion: 0.08
Nodes (54): _display_name(), giveaways_create(), giveaways_end(), giveaways_overview(), giveaways_reroll(), Request, Response, _serialize_giveaway() (+46 more)

### Community 10 - "Automod Cog"
Cohesion: 0.07
Nodes (43): AutoMod, _consecutive_run_length(), Bot, Guild, Interaction, Member, Message, Ког «Автомодерация»: 9 настраиваемых фильтров сообщений, эскалация по количеству (+35 more)

### Community 11 - "Server Event Logging"
Cohesion: 0.08
Nodes (32): AuditLogAction, Command, Request, Response, serverlog_get(), serverlog_put(), _clip(), event_channel_id() (+24 more)

### Community 12 - "Automod Filter Core"
Cohesion: 0.08
Nodes (56): add_escalation_rule(), _default_filter(), delete_escalation_rule(), detect_bad_words(), detect_caps_lock(), detect_emoji_spam(), detect_invites(), detect_links() (+48 more)

### Community 13 - "Test Fake Members"
Cohesion: 0.20
Nodes (35): eliminate_player(), build(), _character(), _setup_game(), test_ability_already_used(), test_ability_dead_player(), test_ability_game_not_active(), test_ability_happy_path_marks_card_used_and_announces() (+27 more)

### Community 14 - "Daily Topic Module"
Cohesion: 0.07
Nodes (58): build_topic_message(), add_topic(), already_posted_today(), delete_topic(), get_settings(), get_today_post_time(), is_valid_time(), load_config() (+50 more)

### Community 15 - "API Client Functions"
Cohesion: 0.12
Nodes (18): ApiError, banMember(), createMemberWarn(), deleteWarn(), fetchMemberDetail(), fetchMemberWarns(), grantRole(), kickMember() (+10 more)

### Community 16 - "Bunker Game Core"
Cohesion: 0.08
Nodes (43): _Deck, default_bunker_capacity(), generate_characters(), has_moderator_access(), is_game_over(), _pick_additional_info(), _pick_age(), _pick_backpack_item() (+35 more)

### Community 17 - "Moderation Routes"
Cohesion: 0.22
Nodes (25): _assignable_roles(), ban_member(), dashboard_reason(), _get_guild_or_none(), get_moderation_log(), _get_target_or_response(), grant_role(), kick_member() (+17 more)

### Community 18 - "Bunker Discord Cog"
Cohesion: 0.08
Nodes (26): build_expulsion_result_embed(), build_game_started_embed(), build_lobby_cancelled_embed(), build_lobby_embed(), build_result_embed(), build_vote_embed(), BunkerCog, BunkerLobbyView (+18 more)

### Community 19 - "Mass Role Assignment"
Cohesion: 0.07
Nodes (57): MassAssignJob, run_mass_assign(), FakeRole, build(), test_auto_roles_route_is_registered_in_the_real_app(), test_get_auto_roles_defaults_to_empty_when_file_missing(), test_get_auto_roles_requires_auth(), test_get_auto_roles_returns_stored_values() (+49 more)

### Community 20 - "Embed Builder Routes"
Cohesion: 0.09
Nodes (49): create_embed_message(), create_embed_template(), delete_embed_template(), get_embed_message(), _get_guild_or_none(), _is_role_assignable(), list_embed_templates(), _parse_body() (+41 more)

### Community 21 - "Bot Entrypoint & Auth Middleware"
Cohesion: 0.06
Nodes (30): require_dashboard_access Middleware, ChetBot, Embed, CTD, CTDCloseView, CTDView, Button, Interaction (+22 more)

### Community 22 - "Frontend Package Deps"
Cohesion: 0.04
Nodes (46): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, tailwindcss, @tailwindcss/vite, devDependencies (+38 more)

### Community 23 - "Lockdown API Client"
Cohesion: 0.06
Nodes (33): DashboardUser, decideFeedbackCase(), FeedbackCaseDetail, FeedbackCaseSummary, fetchCurrentUser(), fetchFeedbackCaseDetail(), fetchFeedbackCases(), fetchLockdownStatus() (+25 more)

### Community 24 - "Mafia DB Tests"
Cohesion: 0.12
Nodes (41): _make_game(), test_add_player_rejects_duplicate(), test_assign_player_role_and_get_by_token(), test_create_and_get_game(), test_get_active_game_in_channel_filters_by_status(), test_get_day_vote_single_row(), test_get_game_by_lobby_and_vote_message(), test_get_night_actions_filters_by_role() (+33 more)

### Community 25 - "Mafia Core Tests"
Cohesion: 0.09
Nodes (30): _FakeMember, _FakePermissions, test_assign_roles_matches_scale_and_covers_all_players(), test_check_win_condition_mafia_wins_at_parity(), test_check_win_condition_no_winner_yet(), test_check_win_condition_town_wins_when_no_mafia(), test_has_moderator_access(), test_resolve_day_vote_all_skip_returns_none() (+22 more)

### Community 26 - "Stream Notifications"
Cohesion: 0.10
Nodes (24): _public_sub(), Request, Response, streams_create(), streams_delete(), streams_list(), streams_update(), add_subscription() (+16 more)

### Community 27 - "Feedback Panel Tests"
Cohesion: 0.10
Nodes (33): bet_error(), flip_coin(), get_settings(), load_config(), payout_amount(), Ядро модуля «Казино»: слоты и монетка на серверную валюту.  Без импорта discord, Три независимых барабана (с повторами), взвешенные по редкости символа., 0 — без выигрыша, SLOT_PAIR_MULTIPLIER — пара, множитель из таблицы — тройка. (+25 more)

### Community 28 - "Reaction Roles Tests"
Cohesion: 0.11
Nodes (32): FakePayload, _setup_config(), test_cleanup_missing_messages_keeps_entries_for_existing_messages(), test_cleanup_missing_messages_removes_entries_for_deleted_messages(), test_handle_reaction_change_add_grants_role_using_payload_member(), test_handle_reaction_change_ignores_bots_own_reaction(), test_handle_reaction_change_ignores_unconfigured_message(), test_handle_reaction_change_ignores_unmatched_emoji() (+24 more)

### Community 29 - "Streams API Client"
Cohesion: 0.08
Nodes (25): AuditPage, deleteVoiceRoom(), fetchAudit(), fetchVerificationSettings(), fetchVoiceRooms(), fetchVoiceStats(), loginUrl(), publishVoicePanel() (+17 more)

### Community 30 - "Voice Rooms Routes"
Cohesion: 0.11
Nodes (32): Request, Response, voice_panel_publish(), voice_room_delete(), voice_rooms_list(), build(), FakeVoiceChannel, isolated_db() (+24 more)

### Community 31 - "XP API Client"
Cohesion: 0.11
Nodes (28): isolated_db(), isolated_state(), isolated_state(), isolated_state(), audit_add(), audit_count(), audit_list(), connect() (+20 more)

### Community 32 - "Mafia Discord Cog"
Cohesion: 0.12
Nodes (18): build_game_started_embed(), build_lobby_cancelled_embed(), build_lynch_result_embed(), build_morning_embed(), build_result_embed(), build_vote_embed(), role_label(), _frontend_url() (+10 more)

### Community 33 - "Feedback API Client"
Cohesion: 0.17
Nodes (18): build(), FakeInteraction, FakeResponse, Тесты кога «Верификация»: выключена по умолчанию, join-роль, кнопка., test_disabled_by_default_no_join_role(), test_explicitly_disabled_no_join_role(), test_join_assigns_unverified_role(), test_join_without_unverified_role_configured_does_nothing() (+10 more)

### Community 34 - "Family DB Tests"
Cohesion: 0.14
Nodes (33): isolated_db(), test_birthday_message_roundtrip(), test_birthday_roundtrip_and_queries(), test_list_and_count_tickets_filters_by_status(), test_pending_form_roundtrip(), test_roster_message_roundtrip(), test_ticket_lifecycle(), test_ticket_recreate_replaces_previous_open_ticket() (+25 more)

### Community 35 - "Events & Embeds Client"
Cohesion: 0.14
Nodes (17): createEmbedMessage(), deleteEmbedTemplate(), EmbedMessagePayload, EmbedSpec, EmbedTemplate, fetchEmbedMessage(), fetchEmbedTemplates(), saveEmbedTemplate() (+9 more)

### Community 36 - "Lockdown Routes"
Cohesion: 0.33
Nodes (11): _role(), test_activate_collects_errors_and_continues(), test_activate_respects_exempts(), test_activate_strips_permissions_and_saves_backup(), test_deactivate_restores_from_backup(), test_deactivate_without_backup_returns_none(), activate_antispam(), antispam_status() (+3 more)

### Community 37 - "Events Route Tests"
Cohesion: 0.14
Nodes (32): build(), _poll_create_spec(), _poll_event(), test_close_event_route_404(), test_close_event_route_requires_auth(), test_close_event_route_success(), test_create_event_404_when_channel_missing(), test_create_event_404_when_role_reward_missing() (+24 more)

### Community 38 - "Mafia Public Route Tests"
Cohesion: 0.18
Nodes (31): build(), _setup_game(), test_action_dead_player(), test_action_deadline_passed(), test_action_game_not_active(), test_action_happy_path_and_resubmit(), test_action_invalid_target_not_alive(), test_action_self_target_allowed_for_doctor() (+23 more)

### Community 39 - "Family Tickets"
Cohesion: 0.13
Nodes (27): test_status_color_and_label(), status_color(), status_label(), add_custom_emoji_reaction(), ApplicationModalPart2, build_full_embed(), build_mini_embed(), build_ticket_result_embed() (+19 more)

### Community 40 - "Button Forms"
Cohesion: 0.11
Nodes (12): ButtonCreate, DynamicQuestionsModal, _get_allowed_role_ids(), _load_buttons_config(), Interaction, Member, Role, Удаляет устаревшие записи кулдаунов. (+4 more)

### Community 41 - "Audit Log & Stats DB"
Cohesion: 0.06
Nodes (41): Тесты ядра Вордла: целостность словаря, оценка догадок, слово дня, настройки., test_board_lines_pads_empty_rows(), test_day_number_epoch(), test_evaluate_all_green(), test_evaluate_duplicate_letters_consume_stock(), test_evaluate_green_priority_over_yellow(), test_evaluate_yellow_and_gray(), test_guess_error_cases() (+33 more)

### Community 42 - "Giveaway Cog"
Cohesion: 0.11
Nodes (13): generate_embed(), GiveawayCog, GiveawayView, Bot, Button, Embed, Interaction, Range (+5 more)

### Community 43 - "Brackets Client Tests"
Cohesion: 0.12
Nodes (15): BracketDetail, BracketMatch, deleteBracket(), disableBracketShare(), enableBracketShare(), fetchBracketDetail(), fetchPublicBracket(), setBracketMatchWinner() (+7 more)

### Community 44 - "Bunker API Client"
Cohesion: 0.10
Nodes (26): applyBunkerAbility(), BunkerCardPools, BunkerCharacter, BunkerGameDetail, BunkerGameSummary, BunkerPlayerRef, BunkerSettings, fetchBunkerCardPools() (+18 more)

### Community 45 - "Automod API Client"
Cohesion: 0.11
Nodes (23): AutomodFilter, AutomodPunishment, AutomodSettings, createEscalationRule(), deleteEscalationRule(), EscalationAction, EscalationRule, fetchAutomod() (+15 more)

### Community 46 - "Reaction Roles Client"
Cohesion: 0.06
Nodes (49): BotConfig, cancelSupply(), ChannelInfo, closeSupply(), createReactionRole(), createStreamSubscription(), createSupply(), deleteReactionRole() (+41 more)

### Community 47 - "Event Builder UI"
Cohesion: 0.16
Nodes (7): EventBuilderView, EventPublishSelect, LimitsModal, OptionsModal, Interaction, TextChannel, TextModal

### Community 48 - "Family Core Tests"
Cohesion: 0.13
Nodes (19): _FakeGuild, _FakeMember, test_build_birthday_text_groups_by_month_and_resolves_mentions(), test_can_manage_tickets_requires_configured_role(), test_has_staff_access_admin_bypasses_role_check(), test_has_staff_access_via_role(), test_parse_birthday_date_feb29_always_allowed(), test_parse_birthday_date_invalid() (+11 more)

### Community 49 - "XP Core Tests"
Cohesion: 0.09
Nodes (34): Request, Response, voice_stats(), test_deserved_roles(), test_format_voice_time(), test_level_formula_monotonic(), test_level_from_xp_roundtrip(), test_level_progress() (+26 more)

### Community 50 - "Event Publish Tests"
Cohesion: 0.20
Nodes (22): _poll_spec(), test_publish_event_poll_creates_matching_event_obj_and_view(), test_publish_event_role_reward_none_stays_none(), test_publish_event_tournament_creates_matching_event_obj_and_view(), test_validate_event_spec_accepts_valid_poll_spec(), test_validate_event_spec_accepts_valid_tournament_spec(), test_validate_event_spec_allows_missing_team_size_check_for_solo_mode(), test_validate_event_spec_rejects_description_too_long() (+14 more)

### Community 51 - "TypeScript Config"
Cohesion: 0.08
Nodes (23): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+15 more)

### Community 52 - "Bot Config Store"
Cohesion: 0.22
Nodes (17): get(), load_config(), migrate_from_env_if_needed(), save_config(), get_welcome_settings(), Request, Response, update_welcome_settings() (+9 more)

### Community 53 - "Family Birthdays"
Cohesion: 0.17
Nodes (11): BirthdayCog, build_birthday_embed(), Bot, Embed, Guild, Interaction, Member, User (+3 more)

### Community 54 - "Anti-Spam Cog"
Cohesion: 0.15
Nodes (25): get_settings(), load_config(), Настройки модуля с дефолтами (выключен по умолчанию)., save_config(), bunker_apply_ability(), bunker_card_pools(), bunker_game_detail(), bunker_games_list() (+17 more)

### Community 55 - "news.py"
Cohesion: 0.16
Nodes (17): _is_id_like(), news_get(), news_put(), Request, Response, get_channel_map(), get_settings(), load_config() (+9 more)

### Community 56 - "events.py"
Cohesion: 0.12
Nodes (18): Messageable, _config_int(), generate_embed(), get_reminder_minutes(), Bot, Button, Color, Embed (+10 more)

### Community 57 - "test_feedback_routes.py"
Cohesion: 0.21
Nodes (20): build(), build_with_channels(), _case(), test_decide_feedback_case_404_when_unknown(), test_decide_feedback_case_409_when_already_decided(), test_decide_feedback_case_409_when_category_deleted(), test_decide_feedback_case_approves_and_persists(), test_decide_feedback_case_rejects_non_boolean_approved() (+12 more)

### Community 58 - "FeedbackCategories.tsx"
Cohesion: 0.11
Nodes (23): fun_get(), fun_put(), Request, Response, test_spin_trigger_chance_grows(), test_spin_trigger_guaranteed_on_last_chamber(), test_get_settings_defaults(), test_pick_emoji_fallback_when_no_guild_emojis() (+15 more)

### Community 59 - "Docs.tsx"
Cohesion: 0.06
Nodes (16): App(), Documentation Banner Image, DashboardShell(), NAV_GROUPS, NavGroup, Section, DocSection, DocsPage() (+8 more)

### Community 60 - "voice_rooms.py"
Cohesion: 0.13
Nodes (21): VCTheme, apply_owner_permissions(), build_embed(), _config_channel_id(), is_room_owner(), load_panel_state(), PanelManager, Embed (+13 more)

### Community 61 - "XPCog"
Cohesion: 0.14
Nodes (14): XP_ADMIN_MAX, XP_ADMIN_MIN, channel_allowed(), member_has_ignored_role(), Bot, Interaction, Member, Message (+6 more)

### Community 62 - "auth.py"
Cohesion: 0.21
Nodes (18): callback(), login(), logout(), me(), Request, Response, DiscordOAuthError, exchange_code_for_token() (+10 more)

### Community 63 - "resolve_guild_member()"
Cohesion: 0.18
Nodes (11): MemberLookupResult, resolve_guild_member(), FakeBot, FakeGuild, _StubHTTPException, _StubNotFound, test_falls_back_to_fetch_when_not_cached(), test_not_found_when_fetch_raises_notfound() (+3 more)

### Community 64 - "xp.py"
Cohesion: 0.19
Nodes (21): _int_in(), _is_id_list(), Request, Response, Вкладка «Участники» дашборда: весь ростер гильдии, а не только те,     кто уже, _serialize_row(), xp_card_bg_delete(), xp_card_bg_upload() (+13 more)

### Community 65 - "test_feedback_category_routes.py"
Cohesion: 0.14
Nodes (10): Guild, Interaction, Member, Message, View, Удаляет устаревшие записи из кэша спам-детектора., Удаляет сообщения участника за последние 20 минут во всех каналах и тредах., Обработка кнопок спам-инцидентов — работает и после перезапуска бота. (+2 more)

### Community 66 - "Supply.tsx"
Cohesion: 0.18
Nodes (27): add_player(), assign_character(), create_game(), get_player(), reveal_fields(), _sample_character(), test_assign_character_and_get_by_token(), test_list_alive_players_excludes_eliminated() (+19 more)

### Community 67 - "MassAssignModal.tsx"
Cohesion: 0.25
Nodes (23): build(), FakeChoice, FakeInteraction, Тесты кога «Казино»: /слоты и /монетка — через .callback(), паттерн test_fun_cog, test_coinflip_disabled_module(), test_coinflip_house_edge_reduces_payout(), test_coinflip_loss(), test_coinflip_win() (+15 more)

### Community 68 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+11 more)

### Community 69 - ".__init__()"
Cohesion: 0.16
Nodes (10): CLEAR_MAX, CLEAR_MIN, ModerationCommandsCog, Bot, Interaction, Member, Range, User (+2 more)

### Community 70 - "VoiceTracker"
Cohesion: 0.16
Nodes (8): is_active(), Bot, Member, VoiceState, Войс-трекер: единый учёт голосовых сессий.  Кормит сразу два модуля: - статис, setup(), VoiceSession, VoiceTracker

### Community 71 - "Interaction"
Cohesion: 0.20
Nodes (7): ApplicationModalPart1, ContinueApplicationView, OpenTicketView, Button, Interaction, setup(), TicketControlView

### Community 72 - "ensure_owner()"
Cohesion: 0.09
Nodes (39): Тесты ядра экономики: курс от XP, комиссии, валидация ставок, хук award_for_xp., test_award_for_xp_disabled_gives_nothing(), test_award_for_xp_uses_kind_rate(), test_bet_error_cases(), test_bet_error_unlimited_when_max_zero(), test_claim_daily_bonus_consecutive_day_extends_streak(), test_claim_daily_bonus_first_time(), test_claim_daily_bonus_gap_resets_streak() (+31 more)

### Community 73 - "family.py"
Cohesion: 0.29
Nodes (17): _decide_ticket(), _display_name(), family_birthday_delete(), family_birthday_set(), family_birthdays_list(), family_get(), family_put(), family_roster() (+9 more)

### Community 74 - "test_family_routes.py"
Cohesion: 0.10
Nodes (39): Тесты economy_db: атомарные списания, переводы, топ, журнал., test_add_ignores_non_positive(), test_daily_bonus_default_when_missing(), test_daily_bonus_roundtrip_and_update(), test_equip_roundtrip_and_clear(), test_grant_and_own_cosmetic(), test_grant_cosmetic_is_idempotent(), test_history_recorded() (+31 more)

### Community 75 - "test_access.py"
Cohesion: 0.26
Nodes (12): has_dashboard_access(), has_super_admin_access(), FakeMember, FakePermissions, FakeRole, test_administrator_always_has_access(), test_member_with_allowed_role_has_access(), test_member_with_no_roles_denied() (+4 more)

### Community 76 - "test_config_routes.py"
Cohesion: 0.09
Nodes (23): fetchAutoRoles(), fetchMassAssignStatus(), fetchMembers(), fetchRoles(), fetchWelcomeSettings(), MassAssignStatus, MassAssignTarget, MembersPage (+15 more)

### Community 77 - "RosterCog"
Cohesion: 0.20
Nodes (9): generate_roster_text(), Bot, Guild, Interaction, Member, Live-ростер семьи: список участников по настроенным ролям.  Портировано из FamQ, Debounce: аккумулирует изменения и обновляет сообщение через 10 секунд., RosterCog (+1 more)

### Community 78 - "reaction_roles.py"
Cohesion: 0.17
Nodes (13): FakeMember, build(), _StubForbidden, _StubNotFound, test_ban_calls_discord_and_logs(), test_ban_discord_not_found_maps_to_404(), test_ban_forbidden_maps_to_403(), test_ban_invalid_json_body_returns_400() (+5 more)

### Community 79 - "PublicBunkerAction.tsx"
Cohesion: 0.09
Nodes (21): test_build_board_embed_finished_loss_reveals_answer(), File, _avatar_bytes(), BoardView, build_board_embed(), _card_file(), GuessModal, PlayNowView (+13 more)

### Community 80 - "Leaderboard.tsx"
Cohesion: 0.10
Nodes (36): _auto_emoji_config(), build(), enable_economy(), FakeInteraction, FakeMsg, FakeResponse, Тесты кога «Развлечения»: русская рулетка (исходы, таймаут, кулдаун) и эмодзи-ру, test_auto_emoji_channel_interval_limits_frequency() (+28 more)

### Community 81 - "VoiceManager"
Cohesion: 0.18
Nodes (13): createFeedbackCategory(), deleteFeedbackCategory(), FeedbackCategoryFieldSpec, FeedbackCategorySpec, fetchFeedbackCategories(), publishFeedbackPanel(), updateFeedbackCategory(), sampleSpec (+5 more)

### Community 82 - "mafia.py"
Cohesion: 0.20
Nodes (19): add(), connect(), get_by_user(), get_db_path(), init(), list_all(), _now(), Connection (+11 more)

### Community 83 - "events.py"
Cohesion: 0.22
Nodes (24): build(), FakeInteraction, Тесты кога слэш-команд модерации: /ban /kick /unban /clear.  Команды вызываются, test_ban_forbidden_reports_ephemeral_error(), test_ban_invalid_duration_format(), test_ban_permanent_default(), test_ban_requires_guild_context(), test_ban_with_duration_schedules_unban() (+16 more)

### Community 84 - "ChetBot"
Cohesion: 0.15
Nodes (14): Web Dashboard Index HTML, React Root Mount Element, React Entry Point Script, ChetBot, ChetBot Web Dashboard, ChetBot Official Documentation, aiohttp Dependency, aiohttp-session Dependency (+6 more)

### Community 85 - "ChannelInfo"
Cohesion: 0.23
Nodes (17): build(), isolated_state(), test_birthday_set_invalid_date(), test_birthday_set_unknown_member(), test_birthdays_crud(), test_get_defaults(), test_put_then_get(), test_put_validation() (+9 more)

### Community 86 - "MafiaLobbyView"
Cohesion: 0.18
Nodes (8): CasinoCog, Bot, Choice, Interaction, Ког «Казино»: /слоты и /монетка на серверную валюту.  Требует включённой «Эконом, Проверка тумблеров и кулдауна. Возвращает (casino, economy, error_text)., setup(), FakeResponse

### Community 87 - "voice_logs.py"
Cohesion: 0.11
Nodes (33): isolated_state(), isolated_db(), Тесты wordle_db: игры дня, статистика со стриками, мета сервера., test_add_guess_accumulates_and_finishes(), test_group_streak_gap_resets(), test_group_streak_grows_and_resets(), test_last_announced_day_roundtrip(), test_list_day_games_filters_by_day() (+25 more)

### Community 88 - "test_auto_roles_routes.py"
Cohesion: 0.23
Nodes (17): build(), build_with_guild(), _full_config(), PUT /api/config не должен затирать ключи других разделов (авто-роли, приветствия, test_get_config_requires_auth(), test_get_config_returns_defaults_when_file_missing(), test_get_config_returns_stored_values(), test_put_config_preserves_foreign_keys() (+9 more)

### Community 89 - "Giveaways.tsx"
Cohesion: 0.25
Nodes (18): build(), _spec(), test_create_feedback_category_404_when_channel_missing(), test_create_feedback_category_404_when_role_missing(), test_create_feedback_category_checks_structure_before_channel_existence(), test_create_feedback_category_rejects_duplicate_key(), test_create_feedback_category_rejects_invalid_key(), test_create_feedback_category_success() (+10 more)

### Community 90 - "PublicMafiaAction.tsx"
Cohesion: 0.18
Nodes (14): build(), test_get_moderation_log_requires_auth(), test_get_moderation_log_respects_limit(), test_get_moderation_log_returns_events_newest_first(), test_append_event_defaults_moderator_to_none_for_automatic_events(), test_append_event_stores_all_fields(), test_append_event_trims_to_max_entries(), test_append_then_load_returns_newest_first() (+6 more)

### Community 91 - "Welcome"
Cohesion: 0.09
Nodes (9): command_reason(), format_duration(), parse_duration(), parse_mute_duration(), Ядро команд модерации (/ban /kick /unban /clear): парсинг и форматирование срока, Секунды из строки вида 10m/2h/7d/30s. ValueError с понятным текстом при неверном, Как parse_duration, но с проверкой лимита Discord в 28 дней., Человекочитаемое представление уже провалидированной строки длительности (10m -> (+1 more)

### Community 92 - "access_middleware.py"
Cohesion: 0.17
Nodes (10): Guard an aiohttp handler with the Phase 1 session -> member -> role check., Гейт для списка серверов бота — намеренно хардкод-роль, см. access.py., require_dashboard_access(), require_super_admin(), audit_list(), Request, Response, Request (+2 more)

### Community 93 - "test_mafia_routes.py"
Cohesion: 0.27
Nodes (10): isolated_db(), isolated_state(), build(), isolated_state(), test_games_list(), test_get_defaults(), test_put_then_get(), test_put_validation() (+2 more)

### Community 94 - "test_warns_routes.py"
Cohesion: 0.18
Nodes (13): announceBunkerAbility(), BUNKER_FIELD_KEYS, BunkerFieldKey, BunkerPublicState, fetchPublicBunker(), revealBunkerFields(), submitBunkerVote(), FIELD_LABEL (+5 more)

### Community 95 - "test_xp_routes.py"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does SelectOption connect Mafia Game Engine to Discord Embed Builder, Supply Cog Tests?, Source Nodes

### Community 96 - "config.py"
Cohesion: 0.44
Nodes (12): get_game(), build(), _cleanup_timer(), _make_lobby(), Тесты игрового цикла кога «Бункер»: старт игры (раздача карточек, голосовой кана, Полный цикл: старт (4 игрока, вместимость 2) -> два раунда голосований -> игра з, test_end_game_deletes_voice_channel(), test_full_round_vote_ends_game_at_capacity() (+4 more)

### Community 97 - "setup_static_routes()"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does force_login() connect Mock Services & Unit Tests to a wide array of system modules and tests?, Source Nodes

### Community 98 - "FakeAsset"
Cohesion: 0.07
Nodes (37): make_moderation_app(), build(), test_get_defaults_disabled(), test_put_then_get(), test_put_validation(), test_requires_login(), build(), test_get_defaults() (+29 more)

### Community 99 - "plugins"
Cohesion: 0.22
Nodes (8): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, typescript, warn

### Community 100 - "DocsSearch.tsx"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Are the inferred relationships involving mock objects (FakeMember, FakeGuild, FakeBot, FakeRole) with DashboardConfig and _StubForbidden correct?, Source Nodes

### Community 101 - "xp_card.py"
Cohesion: 0.18
Nodes (16): audit_middleware(), describe_action(), Request, Аудит действий дашборда: каждое мутирующее действие модератора пишется в stats.d, derive_fernet_key(), Application, setup_session(), build_app() (+8 more)

### Community 102 - "auto_roles.py"
Cohesion: 0.18
Nodes (16): Request, Response, verification_get(), verification_put(), Тесты ядра верификации: настройки (выключена по умолчанию), проверка конфигураци, test_is_configured_does_not_require_unverified_role(), test_is_configured_requires_verified_role(), test_settings_disabled_by_default() (+8 more)

### Community 103 - "icons.svg"
Cohesion: 0.38
Nodes (6): Bluesky Icon, Discord Icon, Documentation Icon, GitHub Icon, Social Icon, X Icon

### Community 104 - "format_voice_time()"
Cohesion: 0.21
Nodes (5): Interaction, Invite, Member, setup(), Welcome

### Community 105 - "DocsToc.tsx"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: What connects schema, typescript, oxc to the rest of the system?, Source Nodes

### Community 108 - "Hero Image Graphic"
Cohesion: 1.00
Nodes (3): Hero Image Graphic, Cheterin Isometric Branding Concept, Layered Isometric Architecture Illustration

### Community 111 - "DocsSearch.tsx"
Cohesion: 0.07
Nodes (34): BracketFormat, BracketSummary, closeEvent(), createBracket(), createEvent(), CreateEventSpec, deleteEvent(), EmbedFieldSpec (+26 more)

### Community 112 - "test_fun_routes.py"
Cohesion: 0.33
Nodes (6): Application, Path, setup_static_routes(), test_asset_path_serves_asset_file(), test_root_path_serves_index_html(), test_unmatched_path_serves_index_html()

### Community 120 - "DocsSearch.tsx"
Cohesion: 0.47
Nodes (8): _check_channel(), _check_role(), get_config(), Request, Response, update_config(), _validate_relations(), _validate_structure()

### Community 121 - "test_members_list.py"
Cohesion: 0.15
Nodes (29): add_round_event(), connect(), count_players(), create_ability_announcement(), get_ability_announcement(), get_active_game_in_channel(), get_db_path(), get_game_by_lobby_message() (+21 more)

### Community 123 - "DocsToc.tsx"
Cohesion: 0.24
Nodes (23): build(), FakeInteraction, Тесты кога Вордла — вызов через .callback()/методы кога, паттерн test_xp_command, test_announce_nobody_played(), test_announce_nobody_won_reveals_word(), test_announce_with_winner_crowns_best_and_streak(), test_commands_disabled_module(), test_daily_guess_edits_existing_live_card() (+15 more)

### Community 124 - "init"
Cohesion: 0.48
Nodes (6): get_auto_roles(), _get_guild_or_none(), _is_role_assignable(), Request, Response, update_auto_roles()

### Community 125 - "Request"
Cohesion: 0.10
Nodes (24): get_settings(), is_suspicious_account(), JoinTracker, load_config(), datetime, Ядро модуля «Антирейд»: детект всплеска входов новых участников.  Без импорта di, Добавить вход и вернуть текущее число подозрительных входов в окне., Настройки модуля с дефолтами. enabled=False по умолчанию — модуль не     активен (+16 more)

### Community 126 - "Response"
Cohesion: 0.31
Nodes (9): build(), test_get_welcome_settings_defaults_to_enabled_when_file_missing(), test_get_welcome_settings_requires_auth(), test_get_welcome_settings_returns_stored_values(), test_update_welcome_settings_persists(), test_update_welcome_settings_rejects_non_boolean(), test_update_welcome_settings_rejects_non_dict_body(), test_update_welcome_settings_requires_auth() (+1 more)

### Community 127 - "Button.tsx"
Cohesion: 0.10
Nodes (14): BALANCE_ADMIN_MAX, FakeResponse, CosmeticsView, EconomyCog, Bot, Interaction, Member, Range (+6 more)

### Community 128 - "events.py"
Cohesion: 0.13
Nodes (6): CreateTeamCodeModal, DraftEvent, handle_registration(), JoinTeamCodeModal, RegisterSoloModal, RegisterTeamCaptainModal

### Community 129 - "wordle_card.py"
Cohesion: 0.21
Nodes (16): ImageDraw, _avatar_image(), _circle_avatar(), _draw_grid(), _font(), _grid_size(), _placeholder_avatar(), FreeTypeFont (+8 more)

### Community 130 - "events.py"
Cohesion: 0.32
Nodes (13): close_event_route(), create_event(), delete_event_route(), get_event(), list_events(), notify_event_route(), Request, Response (+5 more)

### Community 131 - "load_events"
Cohesion: 0.16
Nodes (13): test_load_events_reads_fresh_after_external_write(), test_load_events_returns_empty_events_dict_when_file_missing(), test_save_then_load_roundtrips(), create_participation_view(), EventManageSelect, EventNotifyModal, Events, load_events() (+5 more)

### Community 132 - "test_supply_routes.py"
Cohesion: 0.19
Nodes (33): build(), cosmetics_shop_config(), FakeInteraction, Тесты кога «Экономика»: /баланс /перевести /монеты-топ /магазин — через .callbac, shop_config(), test_balance_disabled_module(), test_balance_shows_amount_and_rank(), test_cosmetics_command_empty() (+25 more)

### Community 133 - "PublicMafiaAction.tsx"
Cohesion: 0.22
Nodes (10): fetchPublicMafia(), MafiaPublicState, submitMafiaAction(), submitMafiaVote(), PHASE_LABEL, PublicMafiaActionPage(), ROLE_HINT, ROLE_LABEL (+2 more)

### Community 134 - "wordle.py"
Cohesion: 0.29
Nodes (8): ChannelControlView, ensure_owner(), Button, Interaction, View, RenameModal, safe_followup(), select_member_ephemeral()

### Community 135 - "test_warns_routes.py"
Cohesion: 0.31
Nodes (8): build(), FakeAutoModCog, test_create_warn(), test_create_warn_validation(), test_create_warn_without_cog_still_succeeds(), test_delete_warn(), test_list_warns_empty(), test_requires_auth()

### Community 136 - "Supply.tsx"
Cohesion: 0.20
Nodes (20): _display_name(), _is_id(), mafia_games_list(), mafia_get(), mafia_public_action(), mafia_public_state(), mafia_public_vote(), mafia_put() (+12 more)

### Community 137 - ".__init__"
Cohesion: 0.20
Nodes (16): deleteCardBg(), fetchXpLeaderboard(), fetchXpOverview(), resetAllXp(), resetMemberXp(), setMemberXp(), updateXpSettings(), uploadCardBg() (+8 more)

### Community 138 - "test_roles.py"
Cohesion: 0.27
Nodes (7): build_lobby_embed(), MafiaLobbyView, Button, Interaction, PLAYERS_CEIL, PLAYERS_FLOOR, Range

### Community 139 - "test_wordle_routes.py"
Cohesion: 0.32
Nodes (15): create_reaction_role(), delete_reaction_role(), _get_guild_or_none(), _is_role_assignable(), list_channels(), list_emojis(), list_reaction_roles(), Request (+7 more)

### Community 140 - "format_voice_time"
Cohesion: 0.21
Nodes (12): build(), Test that partial failures during deactivate are logged with Ошибки field in emb, Test that activate returns 503 when guild is unavailable., Test that partial failures are logged with Ошибки field in embed., _StubForbidden, test_activate_guild_unavailable_503(), test_activate_then_status_then_deactivate(), test_activate_with_partial_errors_logs_error_field() (+4 more)

### Community 141 - "test_feedback_panel_routes.py"
Cohesion: 0.23
Nodes (8): build(), FakeFollowup, FakeInteraction, FakeResponse, Тесты /ранг: подтягивание экипированной косметики (рамка/титул) из магазина., test_rank_command_ignores_unequipped_owned_cosmetics(), test_rank_command_passes_equipped_frame_and_title(), test_rank_command_without_cosmetics_passes_none()

### Community 142 - "DocsSearch.tsx"
Cohesion: 0.20
Nodes (14): Тесты рендера карточки ранга: базовый рендер, кастомная рамка и титул., test_hex_to_rgb(), test_render_rank_card_long_title_does_not_crash(), test_render_rank_card_with_custom_frame_and_title(), test_render_rank_card_without_cosmetics_produces_png(), _background(), _circle_avatar(), _font() (+6 more)

### Community 144 - "FakeResponse"
Cohesion: 0.24
Nodes (6): Bot, Button, Interaction, Ког «Верификация»: панель «Я не бот» для новичков.  ВЫКЛЮЧЕН ПО УМОЛЧАНИЮ и не и, setup(), VerificationView

### Community 145 - "test_news_routes.py"
Cohesion: 0.21
Nodes (10): fetchMafiaGames(), fetchMafiaSettings(), MafiaGameSummary, MafiaSettings, updateMafiaSettings(), MafiaPage(), PHASE_LABEL, Tab (+2 more)

### Community 146 - "test_auto_roles_routes.py"
Cohesion: 0.27
Nodes (10): Request, Response, wordle_get(), wordle_put(), test_settings_defaults(), test_settings_roundtrip(), get_settings(), load_config() (+2 more)

### Community 147 - "test_supply_routes.py"
Cohesion: 0.07
Nodes (44): activateLockdown(), apiFetch(), createDailyTopic(), createGiveaway(), CustomEmoji, DailyTopicSettings, deactivateLockdown(), decideFamilyTicket() (+36 more)

### Community 148 - "test_mass_role_jobs.py"
Cohesion: 0.36
Nodes (13): utcnow(), build(), fresh_member(), Тесты кога «Антирейд»: выключен по умолчанию, детект всплеска, действия., test_below_threshold_does_not_trigger(), test_cooldown_prevents_immediate_retrigger(), test_disabled_by_default_does_nothing(), test_explicitly_disabled_ignores_burst() (+5 more)

### Community 149 - "test_xp_routes.py"
Cohesion: 0.21
Nodes (13): economy_get(), economy_put(), economy_set_balance(), economy_top(), Request, Response, isolated_state(), isolated_state() (+5 more)

### Community 150 - "test_wordle_routes.py"
Cohesion: 0.32
Nodes (12): Client, get_log_channel_id(), log_action(), log_error(), log_security(), log_unhide_action(), Color, Exception (+4 more)

### Community 151 - "format_voice_time"
Cohesion: 0.33
Nodes (5): Lockdown, Choice, Guild, Interaction, setup()

### Community 152 - "FakeVoiceChannel"
Cohesion: 0.18
Nodes (18): build(), FakeFollowup, FakeInteraction, FakeResponse, Тесты команд /xp (add/set/clear) и /leaders в XPCog — вызов через .callback(), т, test_leaders_disabled_module(), test_leaders_empty_leaderboard(), test_leaders_respects_limit() (+10 more)

### Community 153 - "AntiRaidCog"
Cohesion: 0.31
Nodes (5): AntiRaidCog, Bot, Member, Ког «Антирейд»: автоматический Lockdown при всплеске входов новых участников.  В, setup()

### Community 154 - "SupplyView"
Cohesion: 0.39
Nodes (7): build(), test_get_defaults(), test_put_auto_emoji_roundtrip_and_validation(), test_put_then_get(), test_put_validation(), test_put_zero_disables_punishment_and_cooldown(), test_requires_auth()

### Community 155 - "lockdown.py"
Cohesion: 0.39
Nodes (8): lockdown_activate(), lockdown_deactivate(), lockdown_status(), _log(), Request, Response, get_mention_exempt_ids(), get_mentionable_exempt_ids()

### Community 156 - "ChetBot"
Cohesion: 0.33
Nodes (4): DocNavItem, DocsSearchProps, DocsSidebarProps, GROUP_ICONS

### Community 157 - "auth.py"
Cohesion: 0.31
Nodes (4): Message, При старте бота проверяем, нет ли пользователей в бан-листе         с причиной, setup(), TempBan

### Community 158 - "test_antiraid_routes.py"
Cohesion: 0.29
Nodes (3): Modal, Bot, SlotsModal

### Community 159 - "test_member_detail.py"
Cohesion: 0.48
Nodes (5): build(), test_get_defaults(), test_put_then_get(), test_put_validation(), test_requires_auth()

### Community 160 - "test_wordle_routes.py"
Cohesion: 0.50
Nodes (4): DocsToc(), DocsTocProps, slugify(), TocItem

## Knowledge Gaps
- **248 isolated node(s):** `Section`, `NavGroup`, `NAV_GROUPS`, `DocSection`, `SECTIONS` (+243 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SelectOption` connect `Bunker API Client` to `load_events`, `Reaction Roles Client`?**
  _High betweenness centrality (0.232) - this node is a cross-community bridge._
- **Why does `load_events()` connect `load_events` to `events.py`, `events.py`, `Test Fake Bot`, `Tournament Brackets`, `Event Publish Tests`?**
  _High betweenness centrality (0.212) - this node is a cross-community bridge._
- **Why does `FakeGuild` connect `Test Fake Bot` to `Supply Module`, `Dashboard App Bootstrap`, `Test Fake Channels`, `test_supply_routes.py`, `Automod Route Tests`, `test_warns_routes.py`, `Giveaways Routes`, `format_voice_time`, `Test Fake Members`, `Daily Topic Module`, `FakeResponse`, `test_feedback_panel_routes.py`, `Mass Role Assignment`, `test_mass_role_jobs.py`, `Embed Builder Routes`, `FakeVoiceChannel`, `SupplyView`, `Reaction Roles Tests`, `Voice Rooms Routes`, `test_member_detail.py`, `Feedback API Client`, `Lockdown Routes`, `Events Route Tests`, `Mafia Public Route Tests`, `Event Publish Tests`, `test_feedback_routes.py`, `Supply.tsx`, `MassAssignModal.tsx`, `reaction_roles.py`, `Leaderboard.tsx`, `events.py`, `ChannelInfo`, `MafiaLobbyView`, `test_auto_roles_routes.py`, `Giveaways.tsx`, `PublicMafiaAction.tsx`, `test_mafia_routes.py`, `config.py`, `FakeAsset`, `xp_card.py`, `test_member_detail.py`, `DocsToc.tsx`, `Response`, `Button.tsx`?**
  _High betweenness centrality (0.171) - this node is a cross-community bridge._
- **Are the 33 inferred relationships involving `FakeMember` (e.g. with `DashboardConfig` and `_StubForbidden`) actually correct?**
  _`FakeMember` has 33 INFERRED edges - model-reasoned connections that need verification._
- **Are the 33 inferred relationships involving `FakeGuild` (e.g. with `DashboardConfig` and `_StubForbidden`) actually correct?**
  _`FakeGuild` has 33 INFERRED edges - model-reasoned connections that need verification._
- **Are the 32 inferred relationships involving `FakeBot` (e.g. with `DashboardConfig` and `_StubForbidden`) actually correct?**
  _`FakeBot` has 32 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Section`, `NavGroup`, `NAV_GROUPS` to the rest of the system?**
  _248 weakly-connected nodes found - possible documentation gaps or missing edges._