# Graph Report - .  (2026-07-17)

## Corpus Check
- 54 files · ~170,804 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3364 nodes · 8837 edges · 129 communities (113 shown, 16 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 93 edges (avg confidence: 0.61)
- Token cost: 64,224 input · 5,200 output

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
- Application
- Path
- Vite Logo
- PLAYERS_CEIL
- PLAYERS_FLOOR
- Select
- Color
- GuildChannel
- Invite
- Role
- User
- VoiceState

## God Nodes (most connected - your core abstractions)
1. `force_login()` - 291 edges
2. `FakeMember` - 205 edges
3. `FakeGuild` - 154 edges
4. `FakeBot` - 140 edges
5. `apiFetch()` - 108 edges
6. `FakeRole` - 93 edges
7. `FakeChannel` - 92 edges
8. `make_moderation_app()` - 73 edges
9. `jsonInit()` - 68 edges
10. `react` - 57 edges

## Surprising Connections (you probably didn't know these)
- `Unified settings.db Per-Guild Storage` --references--> `get_settings()`  [INFERRED]
  MULTIGUILD_PLAN.md → bunker_core.py
- `Phase 2.3: OAuth Guilds Scope and Server Selection` --references--> `callback()`  [EXTRACTED]
  MULTIGUILD_PLAN.md → dashboard/backend/auth.py
- `isolated_state()` --calls--> `init()`  [EXTRACTED]
  dashboard/backend/tests/test_family_routes.py → family_db.py
- `isolated_state()` --calls--> `init()`  [EXTRACTED]
  dashboard/backend/tests/test_xp_routes.py → stats_db.py
- `CTD Main-Guild Gate` --references--> `CTD`  [EXTRACTED]
  MULTIGUILD_PLAN.md → memobb.py

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

## Communities (129 total, 16 thin omitted)

### Community 0 - "Game Settings & Bunker DB"
Cohesion: 0.05
Nodes (112): get_settings(), load_config(), Настройки модуля с дефолтами (выключен по умолчанию)., add_player(), add_round_event(), assign_character(), connect(), count_players() (+104 more)

### Community 1 - "Supply Module"
Cohesion: 0.05
Nodes (65): _display_name(), _finalize(), Request, Response, _serialize_supply(), supply_cancel(), supply_close(), supply_create() (+57 more)

### Community 2 - "Dashboard App Bootstrap"
Cohesion: 0.05
Nodes (68): Application, AppRunner, create_app(), json_error_middleware(), start_dashboard(), audit_middleware(), describe_action(), Request (+60 more)

### Community 3 - "Test Fake Channels"
Cohesion: 0.06
Nodes (59): FakeChannel, FakeComponentRow, FakeCustomEmoji, FakeMessage, test_parse_role_button_ids_extracts_matching_custom_ids(), test_parse_role_button_ids_handles_no_components(), test_parse_role_button_ids_ignores_non_role_buttons(), build() (+51 more)

### Community 4 - "API Client Types"
Cohesion: 0.04
Nodes (68): AuditEntry, AutoRolesSettings, BracketFormat, BracketStandingsRow, BracketSummary, BunkerAbilityAnnouncement, BunkerAdditionalInfo, BunkerAgeInfo (+60 more)

### Community 5 - "Test Fake Bot"
Cohesion: 0.07
Nodes (51): FakeBot, FakeGuild, FakeThread, make_client_app(), test_guild_unavailable_gets_503(), test_member_not_in_guild_gets_403(), test_member_with_access_reaches_handler(), test_member_without_access_role_gets_403() (+43 more)

### Community 6 - "Automod Route Tests"
Cohesion: 0.07
Nodes (59): force_login(), build(), test_escalation_crud(), test_escalation_validation(), test_get_defaults(), test_requires_auth(), test_update_filter(), test_update_filter_not_found() (+51 more)

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
Nodes (32): AuditLogAction, Color, Command, Request, Response, serverlog_get(), serverlog_put(), GuildChannel (+24 more)

### Community 12 - "Automod Filter Core"
Cohesion: 0.08
Nodes (56): add_escalation_rule(), _default_filter(), delete_escalation_rule(), detect_bad_words(), detect_caps_lock(), detect_emoji_spam(), detect_invites(), detect_links() (+48 more)

### Community 13 - "Test Fake Members"
Cohesion: 0.12
Nodes (48): eliminate_player(), FakeMember, build(), _StubForbidden, _StubNotFound, test_ban_calls_discord_and_logs(), test_ban_discord_not_found_maps_to_404(), test_ban_forbidden_maps_to_403() (+40 more)

### Community 14 - "Daily Topic Module"
Cohesion: 0.08
Nodes (48): build_topic_message(), add_topic(), already_posted_today(), delete_topic(), get_settings(), get_today_post_time(), is_valid_time(), load_config() (+40 more)

### Community 15 - "API Client Functions"
Cohesion: 0.07
Nodes (46): ApiError, apiFetch(), banMember(), createDailyTopic(), createMemberWarn(), DailyTopicSettings, decideFamilyTicket(), deleteDailyTopic() (+38 more)

### Community 16 - "Bunker Game Core"
Cohesion: 0.07
Nodes (45): _Deck, default_bunker_capacity(), generate_characters(), has_moderator_access(), is_game_over(), _pick_additional_info(), _pick_age(), _pick_backpack_item() (+37 more)

### Community 17 - "Moderation Routes"
Cohesion: 0.09
Nodes (42): _assignable_roles(), ban_member(), dashboard_reason(), _get_guild_or_none(), get_moderation_log(), _get_target_or_response(), grant_role(), kick_member() (+34 more)

### Community 18 - "Bunker Discord Cog"
Cohesion: 0.08
Nodes (26): build_expulsion_result_embed(), build_game_started_embed(), build_lobby_cancelled_embed(), build_lobby_embed(), build_result_embed(), build_vote_embed(), BunkerCog, BunkerLobbyView (+18 more)

### Community 19 - "Mass Role Assignment"
Cohesion: 0.09
Nodes (38): MassAssignJob, run_mass_assign(), FakeRole, build(), Test that partial failures during deactivate are logged with Ошибки field in emb, Test that partial failures are logged with Ошибки field in embed., _StubForbidden, test_activate_then_status_then_deactivate() (+30 more)

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
Cohesion: 0.08
Nodes (27): activateLockdown(), DashboardUser, deactivateLockdown(), fetchCurrentUser(), fetchLockdownStatus(), fetchModerationLog(), LockdownStatus, logout() (+19 more)

### Community 24 - "Mafia DB Tests"
Cohesion: 0.12
Nodes (41): _make_game(), test_add_player_rejects_duplicate(), test_assign_player_role_and_get_by_token(), test_create_and_get_game(), test_get_active_game_in_channel_filters_by_status(), test_get_day_vote_single_row(), test_get_game_by_lobby_and_vote_message(), test_get_night_actions_filters_by_role() (+33 more)

### Community 25 - "Mafia Core Tests"
Cohesion: 0.08
Nodes (37): _FakeMember, _FakePermissions, test_assign_roles_matches_scale_and_covers_all_players(), test_check_win_condition_mafia_wins_at_parity(), test_check_win_condition_no_winner_yet(), test_check_win_condition_town_wins_when_no_mafia(), test_get_settings_defaults(), test_has_moderator_access() (+29 more)

### Community 26 - "Stream Notifications"
Cohesion: 0.10
Nodes (24): _public_sub(), Request, Response, streams_create(), streams_delete(), streams_list(), streams_update(), add_subscription() (+16 more)

### Community 27 - "Feedback Panel Tests"
Cohesion: 0.09
Nodes (33): make_moderation_app(), build(), test_publish_feedback_panel_404_when_channel_missing(), test_publish_feedback_panel_attributes_to_session_moderator_not_body(), test_publish_feedback_panel_rejects_missing_channel_id(), test_publish_feedback_panel_requires_auth(), test_publish_feedback_panel_success(), build() (+25 more)

### Community 28 - "Reaction Roles Tests"
Cohesion: 0.11
Nodes (32): FakePayload, _setup_config(), test_cleanup_missing_messages_keeps_entries_for_existing_messages(), test_cleanup_missing_messages_removes_entries_for_deleted_messages(), test_handle_reaction_change_add_grants_role_using_payload_member(), test_handle_reaction_change_ignores_bots_own_reaction(), test_handle_reaction_change_ignores_unconfigured_message(), test_handle_reaction_change_ignores_unmatched_emoji() (+24 more)

### Community 29 - "Streams API Client"
Cohesion: 0.09
Nodes (29): AuditPage, createStreamSubscription(), deleteStreamSubscription(), fetchAudit(), fetchChannels(), fetchNewsSettings(), fetchServerLog(), fetchStreams() (+21 more)

### Community 30 - "Voice Rooms Routes"
Cohesion: 0.11
Nodes (32): Request, Response, voice_panel_publish(), voice_room_delete(), voice_rooms_list(), build(), FakeVoiceChannel, isolated_db() (+24 more)

### Community 31 - "XP API Client"
Cohesion: 0.09
Nodes (29): BotConfig, deleteCardBg(), fetchConfig(), fetchXpLeaderboard(), fetchXpOverview(), resetAllXp(), resetMemberXp(), setMemberXp() (+21 more)

### Community 32 - "Mafia Discord Cog"
Cohesion: 0.12
Nodes (17): build_game_started_embed(), build_lobby_cancelled_embed(), build_lobby_embed(), build_lynch_result_embed(), build_morning_embed(), build_result_embed(), build_vote_embed(), _frontend_url() (+9 more)

### Community 33 - "Feedback API Client"
Cohesion: 0.09
Nodes (21): decideFeedbackCase(), FeedbackCaseDetail, FeedbackCaseSummary, fetchFeedbackCaseDetail(), fetchFeedbackCases(), fetchVoiceStats(), loginUrl(), VoiceStats (+13 more)

### Community 34 - "Family DB Tests"
Cohesion: 0.14
Nodes (33): isolated_db(), test_birthday_message_roundtrip(), test_birthday_roundtrip_and_queries(), test_list_and_count_tickets_filters_by_status(), test_pending_form_roundtrip(), test_roster_message_roundtrip(), test_ticket_lifecycle(), test_ticket_recreate_replaces_previous_open_ticket() (+25 more)

### Community 35 - "Events & Embeds Client"
Cohesion: 0.09
Nodes (26): createEmbedMessage(), createEvent(), CreateEventSpec, deleteEmbedTemplate(), EmbedFieldSpec, EmbedMessagePayload, EmbedSpec, EmbedTemplate (+18 more)

### Community 36 - "Lockdown Routes"
Cohesion: 0.12
Nodes (24): Choice, lockdown_activate(), lockdown_deactivate(), lockdown_status(), _log(), Request, Response, _role() (+16 more)

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
Cohesion: 0.11
Nodes (29): audit_list(), Request, Response, isolated_db(), audit_add(), audit_count(), audit_list(), connect() (+21 more)

### Community 42 - "Giveaway Cog"
Cohesion: 0.11
Nodes (13): generate_embed(), GiveawayCog, GiveawayView, Bot, Button, Embed, Interaction, Range (+5 more)

### Community 43 - "Brackets Client Tests"
Cohesion: 0.12
Nodes (15): BracketDetail, BracketMatch, deleteBracket(), disableBracketShare(), enableBracketShare(), fetchBracketDetail(), fetchPublicBracket(), setBracketMatchWinner() (+7 more)

### Community 44 - "Bunker API Client"
Cohesion: 0.11
Nodes (23): applyBunkerAbility(), BunkerCardPools, BunkerCharacter, BunkerGameDetail, BunkerGameSummary, BunkerPlayerRef, BunkerSettings, fetchBunkerCardPools() (+15 more)

### Community 45 - "Automod API Client"
Cohesion: 0.11
Nodes (23): AutomodFilter, AutomodPunishment, AutomodSettings, createEscalationRule(), deleteEscalationRule(), EscalationAction, EscalationRule, fetchAutomod() (+15 more)

### Community 46 - "Reaction Roles Client"
Cohesion: 0.14
Nodes (18): createReactionRole(), CustomEmoji, deleteReactionRole(), fetchAutoRoles(), fetchEmojis(), fetchReactionRoles(), fetchRoles(), ReactionRoleEntry (+10 more)

### Community 47 - "Event Builder UI"
Cohesion: 0.16
Nodes (7): EventBuilderView, EventPublishSelect, LimitsModal, OptionsModal, Interaction, TextChannel, TextModal

### Community 48 - "Family Core Tests"
Cohesion: 0.13
Nodes (19): _FakeGuild, _FakeMember, test_build_birthday_text_groups_by_month_and_resolves_mentions(), test_can_manage_tickets_requires_configured_role(), test_has_staff_access_admin_bypasses_role_check(), test_has_staff_access_via_role(), test_parse_birthday_date_feb29_always_allowed(), test_parse_birthday_date_invalid() (+11 more)

### Community 49 - "XP Core Tests"
Cohesion: 0.13
Nodes (22): test_deserved_roles(), test_level_formula_monotonic(), test_level_from_xp_roundtrip(), test_level_progress(), test_render_announce(), test_roll_text_xp_respects_multiplier(), test_voice_xp_requires_two_active(), all_reward_role_ids() (+14 more)

### Community 50 - "Event Publish Tests"
Cohesion: 0.20
Nodes (22): _poll_spec(), test_publish_event_poll_creates_matching_event_obj_and_view(), test_publish_event_role_reward_none_stays_none(), test_publish_event_tournament_creates_matching_event_obj_and_view(), test_validate_event_spec_accepts_valid_poll_spec(), test_validate_event_spec_accepts_valid_tournament_spec(), test_validate_event_spec_allows_missing_team_size_check_for_solo_mode(), test_validate_event_spec_rejects_description_too_long() (+14 more)

### Community 51 - "TypeScript Config"
Cohesion: 0.08
Nodes (23): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+15 more)

### Community 52 - "Bot Config Store"
Cohesion: 0.19
Nodes (19): get(), load_config(), migrate_from_env_if_needed(), save_config(), get_welcome_settings(), Request, Response, update_welcome_settings() (+11 more)

### Community 53 - "Family Birthdays"
Cohesion: 0.17
Nodes (11): BirthdayCog, build_birthday_embed(), Bot, Embed, Guild, Interaction, Member, User (+3 more)

### Community 54 - "Anti-Spam Cog"
Cohesion: 0.13
Nodes (11): Guild, Interaction, Member, Message, View, Удаляет устаревшие записи из кэша спам-детектора., Удаляет сообщения участника за последние 20 минут во всех каналах и тредах., Обработка кнопок спам-инцидентов — работает и после перезапуска бота. (+3 more)

### Community 55 - "news.py"
Cohesion: 0.16
Nodes (17): _is_id_like(), news_get(), news_put(), Request, Response, get_channel_map(), get_settings(), load_config() (+9 more)

### Community 56 - "events.py"
Cohesion: 0.16
Nodes (13): test_load_events_reads_fresh_after_external_write(), test_load_events_returns_empty_events_dict_when_file_missing(), test_save_then_load_roundtrips(), create_participation_view(), EventManageSelect, EventNotifyModal, Events, load_events() (+5 more)

### Community 57 - "test_feedback_routes.py"
Cohesion: 0.21
Nodes (20): build(), build_with_channels(), _case(), test_decide_feedback_case_404_when_unknown(), test_decide_feedback_case_409_when_already_decided(), test_decide_feedback_case_409_when_category_deleted(), test_decide_feedback_case_approves_and_persists(), test_decide_feedback_case_rejects_non_boolean_approved() (+12 more)

### Community 58 - "FeedbackCategories.tsx"
Cohesion: 0.15
Nodes (15): createFeedbackCategory(), deleteFeedbackCategory(), FeedbackCategoryFieldSpec, FeedbackCategorySpec, fetchFeedbackCategories(), publishFeedbackPanel(), updateFeedbackCategory(), sampleSpec (+7 more)

### Community 59 - "Docs.tsx"
Cohesion: 0.10
Nodes (6): Documentation Banner Image, DocSection, DocsPage(), GROUPS, NAV_ITEMS, SECTIONS

### Community 60 - "voice_rooms.py"
Cohesion: 0.15
Nodes (14): Modal, VCTheme, build_embed(), _config_channel_id(), is_room_owner(), load_panel_state(), PanelManager, Bot (+6 more)

### Community 61 - "XPCog"
Cohesion: 0.17
Nodes (11): channel_allowed(), member_has_ignored_role(), Bot, Interaction, Member, Message, Ког системы уровней: XP за текст, обработка уровней и наград, /ранг.  XP за во, Приводит роли-награды участника в соответствие с его прогрессом. (+3 more)

### Community 62 - "auth.py"
Cohesion: 0.21
Nodes (18): callback(), login(), logout(), me(), Request, Response, DiscordOAuthError, exchange_code_for_token() (+10 more)

### Community 63 - "resolve_guild_member()"
Cohesion: 0.18
Nodes (11): MemberLookupResult, resolve_guild_member(), FakeBot, FakeGuild, _StubHTTPException, _StubNotFound, test_falls_back_to_fetch_when_not_cached(), test_not_found_when_fetch_raises_notfound() (+3 more)

### Community 64 - "xp.py"
Cohesion: 0.21
Nodes (20): _int_in(), _is_id_list(), Request, Response, Вкладка «Участники» дашборда: весь ростер гильдии, а не только те,     кто уже, _serialize_row(), xp_card_bg_delete(), xp_card_bg_upload() (+12 more)

### Community 65 - "test_feedback_category_routes.py"
Cohesion: 0.25
Nodes (18): build(), _spec(), test_create_feedback_category_404_when_channel_missing(), test_create_feedback_category_404_when_role_missing(), test_create_feedback_category_checks_structure_before_channel_existence(), test_create_feedback_category_rejects_duplicate_key(), test_create_feedback_category_rejects_invalid_key(), test_create_feedback_category_success() (+10 more)

### Community 66 - "Supply.tsx"
Cohesion: 0.15
Nodes (15): cancelSupply(), closeSupply(), createSupply(), deleteVoiceRoom(), fetchSupplyOverview(), fetchVoiceRooms(), publishVoicePanel(), Supply (+7 more)

### Community 67 - "MassAssignModal.tsx"
Cohesion: 0.15
Nodes (12): fetchMassAssignStatus(), fetchMembers(), MassAssignStatus, MassAssignTarget, MembersPage, MemberSummary, startMassAssign(), MassAssignModal() (+4 more)

### Community 68 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+11 more)

### Community 69 - ".__init__()"
Cohesion: 0.13
Nodes (6): CreateTeamCodeModal, DraftEvent, handle_registration(), JoinTeamCodeModal, RegisterSoloModal, RegisterTeamCaptainModal

### Community 70 - "VoiceTracker"
Cohesion: 0.16
Nodes (8): is_active(), Bot, Member, VoiceState, Войс-трекер: единый учёт голосовых сессий.  Кормит сразу два модуля: - статис, setup(), VoiceSession, VoiceTracker

### Community 71 - "Interaction"
Cohesion: 0.20
Nodes (7): ApplicationModalPart1, ContinueApplicationView, OpenTicketView, Button, Interaction, setup(), TicketControlView

### Community 72 - "ensure_owner()"
Cohesion: 0.32
Nodes (7): ChannelControlView, ensure_owner(), Button, Interaction, View, safe_followup(), select_member_ephemeral()

### Community 73 - "family.py"
Cohesion: 0.29
Nodes (17): _decide_ticket(), _display_name(), family_birthday_delete(), family_birthday_set(), family_birthdays_list(), family_get(), family_put(), family_roster() (+9 more)

### Community 74 - "test_family_routes.py"
Cohesion: 0.23
Nodes (17): build(), isolated_state(), test_birthday_set_invalid_date(), test_birthday_set_unknown_member(), test_birthdays_crud(), test_get_defaults(), test_put_then_get(), test_put_validation() (+9 more)

### Community 75 - "test_access.py"
Cohesion: 0.26
Nodes (12): has_dashboard_access(), has_super_admin_access(), FakeMember, FakePermissions, FakeRole, test_administrator_always_has_access(), test_member_with_allowed_role_has_access(), test_member_with_no_roles_denied() (+4 more)

### Community 76 - "test_config_routes.py"
Cohesion: 0.27
Nodes (15): build(), build_with_guild(), _full_config(), test_get_config_requires_auth(), test_get_config_returns_defaults_when_file_missing(), test_get_config_returns_stored_values(), test_update_config_404_when_channel_not_found(), test_update_config_404_when_list_channel_not_found() (+7 more)

### Community 77 - "RosterCog"
Cohesion: 0.20
Nodes (9): generate_roster_text(), Bot, Guild, Interaction, Member, Live-ростер семьи: список участников по настроенным ролям.  Портировано из FamQ, Debounce: аккумулирует изменения и обновляет сообщение через 10 секунд., RosterCog (+1 more)

### Community 78 - "reaction_roles.py"
Cohesion: 0.32
Nodes (15): create_reaction_role(), delete_reaction_role(), _get_guild_or_none(), _is_role_assignable(), list_channels(), list_emojis(), list_reaction_roles(), Request (+7 more)

### Community 79 - "PublicBunkerAction.tsx"
Cohesion: 0.18
Nodes (13): announceBunkerAbility(), BUNKER_FIELD_KEYS, BunkerFieldKey, BunkerPublicState, fetchPublicBunker(), revealBunkerFields(), submitBunkerVote(), FIELD_LABEL (+5 more)

### Community 80 - "Leaderboard.tsx"
Cohesion: 0.16
Nodes (6): fetchPublicLeaderboard(), PublicLeaderboardEntry, NAV_LINKS, PublicLayout(), LeaderboardPage(), MEDAL

### Community 81 - "VoiceManager"
Cohesion: 0.20
Nodes (11): apply_owner_permissions(), GuildChannel, Member, VoiceChannel, VoiceState, remove_owner_permissions(), set_closed_state(), set_member_allow() (+3 more)

### Community 82 - "mafia.py"
Cohesion: 0.32
Nodes (14): _display_name(), _is_id(), mafia_games_list(), mafia_get(), mafia_public_action(), mafia_public_state(), mafia_public_vote(), mafia_put() (+6 more)

### Community 83 - "events.py"
Cohesion: 0.32
Nodes (13): close_event_route(), create_event(), delete_event_route(), get_event(), list_events(), notify_event_route(), Request, Response (+5 more)

### Community 84 - "ChetBot"
Cohesion: 0.15
Nodes (14): Web Dashboard Index HTML, React Root Mount Element, React Entry Point Script, ChetBot, ChetBot Web Dashboard, ChetBot Official Documentation, aiohttp Dependency, aiohttp-session Dependency (+6 more)

### Community 85 - "ChannelInfo"
Cohesion: 0.19
Nodes (11): ChannelInfo, fetchMafiaGames(), fetchMafiaSettings(), MafiaGameSummary, MafiaSettings, updateMafiaSettings(), MafiaPage(), PHASE_LABEL (+3 more)

### Community 86 - "MafiaLobbyView"
Cohesion: 0.27
Nodes (6): MafiaLobbyView, Button, Interaction, PLAYERS_CEIL, PLAYERS_FLOOR, Range

### Community 87 - "voice_logs.py"
Cohesion: 0.32
Nodes (12): Client, get_log_channel_id(), log_action(), log_error(), log_security(), log_unhide_action(), Color, Exception (+4 more)

### Community 88 - "test_auto_roles_routes.py"
Cohesion: 0.27
Nodes (11): build(), test_auto_roles_route_is_registered_in_the_real_app(), test_get_auto_roles_defaults_to_empty_when_file_missing(), test_get_auto_roles_requires_auth(), test_get_auto_roles_returns_stored_values(), test_update_auto_roles_persists_valid_roles(), test_update_auto_roles_rejects_managed_role(), test_update_auto_roles_rejects_non_list_body() (+3 more)

### Community 89 - "Giveaways.tsx"
Cohesion: 0.22
Nodes (9): createGiveaway(), endGiveaway(), fetchGiveawayOverview(), Giveaway, GiveawayOverview, rerollGiveaway(), GiveawaysPage(), STATUS_LABEL (+1 more)

### Community 90 - "PublicMafiaAction.tsx"
Cohesion: 0.22
Nodes (10): fetchPublicMafia(), MafiaPublicState, submitMafiaAction(), submitMafiaVote(), PHASE_LABEL, PublicMafiaActionPage(), ROLE_HINT, ROLE_LABEL (+2 more)

### Community 91 - "Welcome"
Cohesion: 0.21
Nodes (5): Interaction, Invite, Member, setup(), Welcome

### Community 92 - "access_middleware.py"
Cohesion: 0.24
Nodes (7): Guard an aiohttp handler with the Phase 1 session -> member -> role check., Гейт для списка серверов бота — намеренно хардкод-роль, см. access.py., require_dashboard_access(), require_super_admin(), Request, Response, superadmin_guilds()

### Community 93 - "test_mafia_routes.py"
Cohesion: 0.27
Nodes (10): isolated_db(), isolated_state(), build(), isolated_state(), test_games_list(), test_get_defaults(), test_put_then_get(), test_put_validation() (+2 more)

### Community 94 - "test_warns_routes.py"
Cohesion: 0.31
Nodes (8): build(), FakeAutoModCog, test_create_warn(), test_create_warn_validation(), test_create_warn_without_cog_still_succeeds(), test_delete_warn(), test_list_warns_empty(), test_requires_auth()

### Community 95 - "test_xp_routes.py"
Cohesion: 0.35
Nodes (10): build(), isolated_state(), test_leaderboard_guild_unavailable(), test_leaderboard_keeps_members_who_left(), test_leaderboard_pagination_over_merged_roster(), test_leaderboard_search_filters_by_display_name(), test_leaderboard_shows_every_guild_member_even_without_xp(), test_leaderboard_sorted_by_xp_desc() (+2 more)

### Community 96 - "config.py"
Cohesion: 0.47
Nodes (8): _check_channel(), _check_role(), get_config(), Request, Response, update_config(), _validate_relations(), _validate_structure()

### Community 97 - "setup_static_routes()"
Cohesion: 0.33
Nodes (6): Application, Path, setup_static_routes(), test_asset_path_serves_asset_file(), test_root_path_serves_index_html(), test_unmatched_path_serves_index_html()

### Community 98 - "FakeAsset"
Cohesion: 0.22
Nodes (3): FakeAsset, FakeColor, FakePermissions

### Community 99 - "plugins"
Cohesion: 0.22
Nodes (8): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, typescript, warn

### Community 100 - "DocsSearch.tsx"
Cohesion: 0.33
Nodes (4): DocNavItem, DocsSearchProps, DocsSidebarProps, GROUP_ICONS

### Community 101 - "xp_card.py"
Cohesion: 0.33
Nodes (8): FreeTypeFont, Image, ImageFont, _background(), _circle_avatar(), _font(), Генерация PNG-карточки ранга (аватар, уровень, прогресс-бар, место в топе).  Ф, render_rank_card()

### Community 102 - "auto_roles.py"
Cohesion: 0.48
Nodes (6): get_auto_roles(), _get_guild_or_none(), _is_role_assignable(), Request, Response, update_auto_roles()

### Community 103 - "icons.svg"
Cohesion: 0.38
Nodes (6): Bluesky Icon, Discord Icon, Documentation Icon, GitHub Icon, Social Icon, X Icon

### Community 104 - "format_voice_time()"
Cohesion: 0.33
Nodes (6): Request, Response, voice_stats(), test_format_voice_time(), format_voice_time(), Человекочитаемое время войса: «2 нед. 1 д. 3 ч.»

### Community 105 - "DocsToc.tsx"
Cohesion: 0.50
Nodes (4): DocsToc(), DocsTocProps, slugify(), TocItem

### Community 108 - "Hero Image Graphic"
Cohesion: 1.00
Nodes (3): Hero Image Graphic, Cheterin Isometric Branding Concept, Layered Isometric Architecture Illustration

## Knowledge Gaps
- **222 isolated node(s):** `$schema`, `typescript`, `oxc`, `react/rules-of-hooks`, `warn` (+217 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SelectOption` connect `XP API Client` to `events.py`?**
  _High betweenness centrality (0.274) - this node is a cross-community bridge._
- **Why does `load_events()` connect `events.py` to `.__init__()`, `Test Fake Bot`, `Tournament Brackets`, `Event Publish Tests`, `events.py`?**
  _High betweenness centrality (0.250) - this node is a cross-community bridge._
- **Why does `FakeGuild` connect `Test Fake Bot` to `Game Settings & Bunker DB`, `Supply Module`, `Dashboard App Bootstrap`, `Test Fake Channels`, `Automod Route Tests`, `Giveaways Routes`, `Test Fake Members`, `Moderation Routes`, `Mass Role Assignment`, `Embed Builder Routes`, `Feedback Panel Tests`, `Reaction Roles Tests`, `Voice Rooms Routes`, `Lockdown Routes`, `Events Route Tests`, `Mafia Public Route Tests`, `Event Publish Tests`, `test_feedback_routes.py`, `test_feedback_category_routes.py`, `test_family_routes.py`, `test_config_routes.py`, `test_auto_roles_routes.py`, `test_mafia_routes.py`, `test_warns_routes.py`, `test_xp_routes.py`, `FakeVoiceChannel`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `FakeMember` (e.g. with `_StubForbidden` and `_StubNotFound`) actually correct?**
  _`FakeMember` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `FakeGuild` (e.g. with `_StubForbidden` and `_StubNotFound`) actually correct?**
  _`FakeGuild` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `FakeBot` (e.g. with `_StubForbidden` and `_StubNotFound`) actually correct?**
  _`FakeBot` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `typescript`, `oxc` to the rest of the system?**
  _222 weakly-connected nodes found - possible documentation gaps or missing edges._