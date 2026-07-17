# Graph Report - .  (2026-07-16)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 2714 nodes · 7231 edges · 104 communities (100 shown, 4 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 95 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ae82a902`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- events.py
- feedback.py
- voice_rooms.py
- FakeGuild
- brackets.py
- giveaway_core.py
- App.tsx
- MafiaCog
- test_embed_builder_core.py
- test_reaction_roles_cog.py
- FakeMember
- react
- supply_core.py
- moderation.py
- force_login
- ServerLog
- FakeMessage
- devDependencies
- apiFetch
- FakeChannel
- client.ts
- Events.tsx
- Streams
- test_mafia_core.py
- Lockdown.tsx
- FakeRole
- test_voice_routes.py
- family_db.py
- test_lockdown_core.py
- test_events_routes.py
- fetchChannels
- stats_db.py
- xp_core.py
- family_tickets.py
- ButtonCreate
- GiveawayCog
- BracketDetail.tsx
- make_moderation_app
- mafia_db.py
- MassAssignModal.tsx
- family_core.py
- send_dev_log
- test_events_core_publish.py
- compilerOptions
- BirthdayCog
- Spam
- news.py
- test_feedback_routes.py
- Docs.tsx
- XPCog
- create_app
- auth.py
- resolve_guild_member
- xp.py
- test_auth.py
- EmbedBuilder.tsx
- FeedbackCases.tsx
- compilerOptions
- VoiceTracker
- Interaction
- bot_config.py
- family.py
- FeedbackCategories.tsx
- test_access.py
- test_config_routes.py
- test_family_routes.py
- test_mafia_db.py
- RosterCog
- CTD
- fakes.py
- test_lockdown_routes.py
- load_dashboard_config
- ChetBot
- mafia.py
- Giveaways.tsx
- Welcome
- test_audit.py
- PublicMafiaAction.tsx
- main.py
- access_middleware.py
- app.py
- test_mafia_routes.py
- test_welcome_routes.py
- SupplyView
- config.py
- plugins
- DocsSearch.tsx
- xp_card.py
- setup_session
- auto_roles.py
- icons.svg
- welcome.py
- DocsToc.tsx
- favicon.svg
- Hero Image Graphic
- tsconfig.json
- React Logo Image
- Vite Logo

## God Nodes (most connected - your core abstractions)
1. `force_login()` - 252 edges
2. `FakeMember` - 153 edges
3. `FakeGuild` - 140 edges
4. `FakeBot` - 127 edges
5. `FakeRole` - 94 edges
6. `FakeChannel` - 86 edges
7. `apiFetch()` - 81 edges
8. `make_moderation_app()` - 64 edges
9. `react` - 52 edges
10. `jsonInit()` - 51 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `start_dashboard()`  [EXTRACTED]
  main.py → dashboard/backend/app.py
- `test_role_label_known_and_unknown()` --calls--> `role_label()`  [EXTRACTED]
  dashboard/backend/tests/test_mafia_core.py → mafia_core.py
- `ChetBot` --references--> `aiohttp Dependency`  [INFERRED]
  README.md → requirements.txt
- `ChetBot` --references--> `aiohttp-session Dependency`  [INFERRED]
  README.md → requirements.txt
- `ChetBot` --references--> `cryptography Dependency`  [INFERRED]
  README.md → requirements.txt

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Backend Runtime Dependencies** — requirements_discord_py, requirements_python_dotenv, requirements_aiohttp, requirements_aiohttp_session, requirements_cryptography, requirements_pillow [INFERRED 0.95]
- **Dashboard Application Architecture** — readme_chetbot, readme_dashboard, dashboard_frontend_index_html [INFERRED 0.85]
- **External Platform and Social Icons Set** — dashboard_frontend_public_icons_bluesky_icon, dashboard_frontend_public_icons_discord_icon, dashboard_frontend_public_icons_github_icon, dashboard_frontend_public_icons_x_icon, dashboard_frontend_public_icons_social_icon [INFERRED 0.85]
- **Dashboard UI Icon Asset Set** — dashboard_frontend_public_icons_bluesky_icon, dashboard_frontend_public_icons_discord_icon, dashboard_frontend_public_icons_documentation_icon, dashboard_frontend_public_icons_github_icon, dashboard_frontend_public_icons_social_icon, dashboard_frontend_public_icons_x_icon [EXTRACTED 1.00]
- **Docs Page User Interface** — dashboard_frontend_src_pages_docs, dashboard_frontend_src_components_docs_docsbanner, dashboard_frontend_src_assets_docs_banner [INFERRED 0.90]
- **Hero Page Visual Branding Elements** — dashboard_frontend_src_assets_hero, dashboard_frontend_src_assets_hero_branding, dashboard_frontend_src_assets_hero_layered_stack [INFERRED 0.85]

## Communities (104 total, 4 thin omitted)

### Community 0 - "events.py"
Cohesion: 0.05
Nodes (39): close_event_route(), create_event(), delete_event_route(), get_event(), list_events(), notify_event_route(), Request, Response (+31 more)

### Community 1 - "feedback.py"
Cohesion: 0.07
Nodes (56): create_feedback_category(), decide_feedback_case(), delete_feedback_category(), get_feedback_case(), _get_guild_or_none(), list_feedback_cases(), list_feedback_categories(), publish_feedback_panel_route() (+48 more)

### Community 2 - "voice_rooms.py"
Cohesion: 0.07
Nodes (44): Client, Modal, get_log_channel_id(), log_action(), log_error(), log_security(), log_unhide_action(), Color (+36 more)

### Community 3 - "FakeGuild"
Cohesion: 0.08
Nodes (45): FakeBot, FakeGuild, FakeThread, make_client_app(), test_guild_unavailable_gets_503(), test_member_not_in_guild_gets_403(), test_member_with_access_reaches_handler(), test_member_without_access_role_gets_403() (+37 more)

### Community 4 - "brackets.py"
Cohesion: 0.07
Nodes (61): create_bracket(), create_bracket_v2(), _de_get_match(), _de_match(), _de_recompute_match(), _de_resolve(), extract_entries_from_event(), generate_de() (+53 more)

### Community 5 - "giveaway_core.py"
Cohesion: 0.08
Nodes (54): _display_name(), giveaways_create(), giveaways_end(), giveaways_overview(), giveaways_reroll(), Request, Response, _serialize_giveaway() (+46 more)

### Community 6 - "App.tsx"
Cohesion: 0.06
Nodes (35): AuditPage, deleteVoiceRoom(), fetchAudit(), fetchPublicLeaderboard(), fetchSuperAdminGuilds(), fetchVoiceRooms(), fetchVoiceStats(), loginUrl() (+27 more)

### Community 7 - "MafiaCog"
Cohesion: 0.08
Nodes (28): SelectOption, build_game_started_embed(), build_lobby_cancelled_embed(), build_lobby_embed(), build_lynch_result_embed(), build_morning_embed(), build_result_embed(), build_vote_embed() (+20 more)

### Community 8 - "test_embed_builder_core.py"
Cohesion: 0.08
Nodes (54): create_embed_message(), create_embed_template(), delete_embed_template(), get_embed_message(), _get_guild_or_none(), _is_role_assignable(), list_embed_templates(), _parse_body() (+46 more)

### Community 9 - "test_reaction_roles_cog.py"
Cohesion: 0.08
Nodes (47): create_reaction_role(), delete_reaction_role(), _get_guild_or_none(), _is_role_assignable(), list_channels(), list_emojis(), list_reaction_roles(), Request (+39 more)

### Community 10 - "FakeMember"
Cohesion: 0.09
Nodes (44): FakeMember, build(), _StubForbidden, _StubNotFound, test_ban_calls_discord_and_logs(), test_ban_discord_not_found_maps_to_404(), test_ban_forbidden_maps_to_403(), test_ban_invalid_json_body_returns_400() (+36 more)

### Community 11 - "react"
Cohesion: 0.06
Nodes (41): BotConfig, ChannelInfo, fetchConfig(), fetchMafiaGames(), fetchMafiaSettings(), fetchNewsSettings(), fetchServerLog(), MafiaGameSummary (+33 more)

### Community 12 - "supply_core.py"
Cohesion: 0.09
Nodes (47): _display_name(), _finalize(), Request, Response, _serialize_supply(), supply_cancel(), supply_close(), supply_create() (+39 more)

### Community 13 - "moderation.py"
Cohesion: 0.09
Nodes (42): _assignable_roles(), ban_member(), dashboard_reason(), _get_guild_or_none(), get_moderation_log(), _get_target_or_response(), grant_role(), kick_member() (+34 more)

### Community 14 - "force_login"
Cohesion: 0.10
Nodes (45): force_login(), build(), test_auto_roles_route_is_registered_in_the_real_app(), test_get_auto_roles_defaults_to_empty_when_file_missing(), test_get_auto_roles_requires_auth(), test_get_auto_roles_returns_stored_values(), test_update_auto_roles_persists_valid_roles(), test_update_auto_roles_rejects_managed_role() (+37 more)

### Community 15 - "ServerLog"
Cohesion: 0.10
Nodes (25): Request, Response, serverlog_get(), serverlog_put(), _clip(), event_channel_id(), get_settings(), load_config() (+17 more)

### Community 16 - "FakeMessage"
Cohesion: 0.07
Nodes (34): FakeCustomEmoji, FakeMessage, test_fake_channel_send_creates_and_stores_message(), test_fake_channel_send_raises_when_configured(), test_fake_component_row_holds_children(), test_fake_message_defaults_to_empty_embeds_and_components(), test_fake_message_edit_raises_when_configured(), test_fake_message_edit_updates_content_embed_and_components() (+26 more)

### Community 17 - "devDependencies"
Cohesion: 0.04
Nodes (46): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, tailwindcss, @tailwindcss/vite, devDependencies (+38 more)

### Community 18 - "apiFetch"
Cohesion: 0.09
Nodes (37): ApiError, apiFetch(), banMember(), cancelSupply(), closeSupply(), createSupply(), decideFamilyTicket(), deleteFamilyBirthday() (+29 more)

### Community 19 - "FakeChannel"
Cohesion: 0.12
Nodes (38): FakeChannel, build(), test_create_embed_message_allows_content_only(), test_create_embed_message_channel_not_found(), test_create_embed_message_checks_channel_before_role_assignability(), test_create_embed_message_discord_error_logged(), test_create_embed_message_rejects_blank_content_and_empty_embed(), test_create_embed_message_rejects_empty_embed() (+30 more)

### Community 20 - "client.ts"
Cohesion: 0.07
Nodes (41): AuditEntry, AutoRolesSettings, BracketStandingsRow, deleteCardBg(), EmbedMessageResult, EventParticipantSolo, EventParticipantTeamCaptain, EventParticipantTeamCodeMember (+33 more)

### Community 21 - "Events.tsx"
Cohesion: 0.08
Nodes (33): BracketFormat, BracketSummary, closeEvent(), createBracket(), createEvent(), CreateEventSpec, deleteEvent(), EmbedFieldSpec (+25 more)

### Community 22 - "Streams"
Cohesion: 0.10
Nodes (24): _public_sub(), Request, Response, streams_create(), streams_delete(), streams_list(), streams_update(), add_subscription() (+16 more)

### Community 23 - "test_mafia_core.py"
Cohesion: 0.08
Nodes (36): _FakeMember, _FakePermissions, test_assign_roles_matches_scale_and_covers_all_players(), test_check_win_condition_mafia_wins_at_parity(), test_check_win_condition_no_winner_yet(), test_check_win_condition_town_wins_when_no_mafia(), test_get_settings_defaults(), test_has_moderator_access() (+28 more)

### Community 24 - "Lockdown.tsx"
Cohesion: 0.09
Nodes (27): activateLockdown(), DashboardUser, deactivateLockdown(), fetchCurrentUser(), fetchLockdownStatus(), fetchModerationLog(), LockdownStatus, logout() (+19 more)

### Community 25 - "FakeRole"
Cohesion: 0.13
Nodes (28): MassAssignJob, run_mass_assign(), FakeRole, build(), test_mass_assign_all_except_bots_completes(), test_mass_assign_concurrent_requests_only_one_job_starts(), test_mass_assign_job_marked_failed_on_unexpected_exception(), test_mass_assign_rejects_role_above_bot() (+20 more)

### Community 26 - "test_voice_routes.py"
Cohesion: 0.11
Nodes (32): Request, Response, voice_panel_publish(), voice_room_delete(), voice_rooms_list(), build(), FakeVoiceChannel, isolated_db() (+24 more)

### Community 27 - "family_db.py"
Cohesion: 0.13
Nodes (34): isolated_db(), test_birthday_message_roundtrip(), test_birthday_roundtrip_and_queries(), test_list_and_count_tickets_filters_by_status(), test_pending_form_roundtrip(), test_roster_message_roundtrip(), test_ticket_lifecycle(), test_ticket_recreate_replaces_previous_open_ticket() (+26 more)

### Community 28 - "test_lockdown_core.py"
Cohesion: 0.12
Nodes (24): Choice, lockdown_activate(), lockdown_deactivate(), lockdown_status(), _log(), Request, Response, _role() (+16 more)

### Community 29 - "test_events_routes.py"
Cohesion: 0.14
Nodes (32): build(), _poll_create_spec(), _poll_event(), test_close_event_route_404(), test_close_event_route_requires_auth(), test_close_event_route_success(), test_create_event_404_when_channel_missing(), test_create_event_404_when_role_reward_missing() (+24 more)

### Community 30 - "fetchChannels"
Cohesion: 0.13
Nodes (24): createReactionRole(), createStreamSubscription(), CustomEmoji, deleteReactionRole(), deleteStreamSubscription(), fetchChannels(), fetchEmojis(), fetchReactionRoles() (+16 more)

### Community 31 - "stats_db.py"
Cohesion: 0.11
Nodes (30): audit_list(), Request, Response, isolated_db(), isolated_state(), audit_add(), audit_count(), audit_list() (+22 more)

### Community 32 - "xp_core.py"
Cohesion: 0.10
Nodes (28): Request, Response, voice_stats(), test_deserved_roles(), test_format_voice_time(), test_level_formula_monotonic(), test_level_from_xp_roundtrip(), test_level_progress() (+20 more)

### Community 33 - "family_tickets.py"
Cohesion: 0.13
Nodes (27): test_status_color_and_label(), status_color(), status_label(), add_custom_emoji_reaction(), ApplicationModalPart2, build_full_embed(), build_mini_embed(), build_ticket_result_embed() (+19 more)

### Community 34 - "ButtonCreate"
Cohesion: 0.11
Nodes (12): ButtonCreate, DynamicQuestionsModal, _get_allowed_role_ids(), _load_buttons_config(), Interaction, Member, Role, Удаляет устаревшие записи кулдаунов. (+4 more)

### Community 35 - "GiveawayCog"
Cohesion: 0.11
Nodes (13): generate_embed(), GiveawayCog, GiveawayView, Bot, Button, Embed, Interaction, Range (+5 more)

### Community 36 - "BracketDetail.tsx"
Cohesion: 0.12
Nodes (15): BracketDetail, BracketMatch, deleteBracket(), disableBracketShare(), enableBracketShare(), fetchBracketDetail(), fetchPublicBracket(), setBracketMatchWinner() (+7 more)

### Community 37 - "make_moderation_app"
Cohesion: 0.13
Nodes (21): make_moderation_app(), build(), test_detail_400_on_non_numeric_id(), test_detail_404_when_member_absent(), test_detail_defaults_when_no_stats(), test_detail_shape_matches_userinfo(), build(), test_get_defaults() (+13 more)

### Community 38 - "mafia_db.py"
Cohesion: 0.16
Nodes (26): test_assign_player_role_and_get_by_token(), test_list_alive_players_excludes_eliminated(), test_remove_player(), add_player(), add_round_event(), assign_player_role(), connect(), count_players() (+18 more)

### Community 39 - "MassAssignModal.tsx"
Cohesion: 0.11
Nodes (16): fetchAutoRoles(), fetchMassAssignStatus(), fetchWelcomeSettings(), MassAssignStatus, MassAssignTarget, MemberSummary, startMassAssign(), updateAutoRoles() (+8 more)

### Community 40 - "family_core.py"
Cohesion: 0.13
Nodes (19): _FakeGuild, _FakeMember, test_build_birthday_text_groups_by_month_and_resolves_mentions(), test_can_manage_tickets_requires_configured_role(), test_has_staff_access_admin_bypasses_role_check(), test_has_staff_access_via_role(), test_parse_birthday_date_feb29_always_allowed(), test_parse_birthday_date_invalid() (+11 more)

### Community 41 - "send_dev_log"
Cohesion: 0.16
Nodes (14): Messageable, _config_int(), generate_embed(), get_reminder_minutes(), Bot, Color, Embed, Ког «Сборы на поставку» (портировано из ChetSupply, функционал расширен).  Слэш- (+6 more)

### Community 42 - "test_events_core_publish.py"
Cohesion: 0.20
Nodes (22): _poll_spec(), test_publish_event_poll_creates_matching_event_obj_and_view(), test_publish_event_role_reward_none_stays_none(), test_publish_event_tournament_creates_matching_event_obj_and_view(), test_validate_event_spec_accepts_valid_poll_spec(), test_validate_event_spec_accepts_valid_tournament_spec(), test_validate_event_spec_allows_missing_team_size_check_for_solo_mode(), test_validate_event_spec_rejects_description_too_long() (+14 more)

### Community 43 - "compilerOptions"
Cohesion: 0.08
Nodes (23): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+15 more)

### Community 44 - "BirthdayCog"
Cohesion: 0.17
Nodes (11): BirthdayCog, build_birthday_embed(), Bot, Embed, Guild, Interaction, Member, User (+3 more)

### Community 45 - "Spam"
Cohesion: 0.13
Nodes (11): Guild, Interaction, Member, Message, View, Удаляет устаревшие записи из кэша спам-детектора., Удаляет сообщения участника за последние 20 минут во всех каналах и тредах., Обработка кнопок спам-инцидентов — работает и после перезапуска бота. (+3 more)

### Community 46 - "news.py"
Cohesion: 0.16
Nodes (17): _is_id_like(), news_get(), news_put(), Request, Response, get_channel_map(), get_settings(), load_config() (+9 more)

### Community 47 - "test_feedback_routes.py"
Cohesion: 0.21
Nodes (20): build(), build_with_channels(), _case(), test_decide_feedback_case_404_when_unknown(), test_decide_feedback_case_409_when_already_decided(), test_decide_feedback_case_409_when_category_deleted(), test_decide_feedback_case_approves_and_persists(), test_decide_feedback_case_rejects_non_boolean_approved() (+12 more)

### Community 48 - "Docs.tsx"
Cohesion: 0.10
Nodes (6): Documentation Banner Image, DocSection, DocsPage(), GROUPS, NAV_ITEMS, SECTIONS

### Community 49 - "XPCog"
Cohesion: 0.17
Nodes (11): channel_allowed(), member_has_ignored_role(), Bot, Interaction, Member, Message, Ког системы уровней: XP за текст, обработка уровней и наград, /ранг.  XP за во, Приводит роли-награды участника в соответствие с его прогрессом. (+3 more)

### Community 50 - "create_app"
Cohesion: 0.21
Nodes (19): AppRunner, create_app(), Application, Path, start_dashboard(), FakeBot, A non-ConfigError, non-OSError failure during app construction/startup     must, On a real port-bind conflict (OSError from TCPSite.start), the     http_session (+11 more)

### Community 51 - "auth.py"
Cohesion: 0.21
Nodes (18): callback(), login(), logout(), me(), Request, Response, DiscordOAuthError, exchange_code_for_token() (+10 more)

### Community 52 - "resolve_guild_member"
Cohesion: 0.18
Nodes (11): MemberLookupResult, resolve_guild_member(), FakeBot, FakeGuild, _StubHTTPException, _StubNotFound, test_falls_back_to_fetch_when_not_cached(), test_not_found_when_fetch_raises_notfound() (+3 more)

### Community 53 - "xp.py"
Cohesion: 0.21
Nodes (20): _int_in(), _is_id_list(), Request, Response, Вкладка «Участники» дашборда: весь ростер гильдии, а не только те,     кто уже, _serialize_row(), xp_card_bg_delete(), xp_card_bg_upload() (+12 more)

### Community 54 - "test_auth.py"
Cohesion: 0.30
Nodes (15): FakeBot, FakeGuild, FakeMember, make_app(), _NullHttpSession, Placeholder; overridden per-test via monkeypatch on discord_oauth functions., test_callback_access_denied_uses_frontend_url(), test_callback_denies_when_role_missing() (+7 more)

### Community 55 - "EmbedBuilder.tsx"
Cohesion: 0.16
Nodes (14): createEmbedMessage(), deleteEmbedTemplate(), EmbedMessagePayload, EmbedTemplate, fetchEmbedMessage(), fetchEmbedTemplates(), saveEmbedTemplate(), updateEmbedMessage() (+6 more)

### Community 56 - "FeedbackCases.tsx"
Cohesion: 0.16
Nodes (12): decideFeedbackCase(), FeedbackCaseDetail, FeedbackCaseSummary, fetchFeedbackCaseDetail(), fetchFeedbackCases(), FeedbackPage(), Tab, FeedbackCaseDetailPanel() (+4 more)

### Community 57 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+11 more)

### Community 58 - "VoiceTracker"
Cohesion: 0.16
Nodes (8): is_active(), Bot, Member, VoiceState, Войс-трекер: единый учёт голосовых сессий.  Кормит сразу два модуля: - статис, setup(), VoiceSession, VoiceTracker

### Community 59 - "Interaction"
Cohesion: 0.20
Nodes (7): ApplicationModalPart1, ContinueApplicationView, OpenTicketView, Button, Interaction, setup(), TicketControlView

### Community 60 - "bot_config.py"
Cohesion: 0.24
Nodes (15): get(), load_config(), migrate_from_env_if_needed(), save_config(), test_get_returns_default_when_key_missing(), test_get_returns_stored_value(), test_load_config_reads_fresh_after_external_write(), test_load_config_returns_empty_dict_when_file_missing() (+7 more)

### Community 61 - "family.py"
Cohesion: 0.29
Nodes (17): _decide_ticket(), _display_name(), family_birthday_delete(), family_birthday_set(), family_birthdays_list(), family_get(), family_put(), family_roster() (+9 more)

### Community 62 - "FeedbackCategories.tsx"
Cohesion: 0.18
Nodes (13): createFeedbackCategory(), deleteFeedbackCategory(), FeedbackCategoryFieldSpec, FeedbackCategorySpec, fetchFeedbackCategories(), publishFeedbackPanel(), updateFeedbackCategory(), sampleSpec (+5 more)

### Community 63 - "test_access.py"
Cohesion: 0.26
Nodes (12): has_dashboard_access(), has_super_admin_access(), FakeMember, FakePermissions, FakeRole, test_administrator_always_has_access(), test_member_with_allowed_role_has_access(), test_member_with_no_roles_denied() (+4 more)

### Community 64 - "test_config_routes.py"
Cohesion: 0.27
Nodes (15): build(), build_with_guild(), _full_config(), test_get_config_requires_auth(), test_get_config_returns_defaults_when_file_missing(), test_get_config_returns_stored_values(), test_update_config_404_when_channel_not_found(), test_update_config_404_when_list_channel_not_found() (+7 more)

### Community 65 - "test_family_routes.py"
Cohesion: 0.25
Nodes (16): build(), test_birthday_set_invalid_date(), test_birthday_set_unknown_member(), test_birthdays_crud(), test_get_defaults(), test_put_then_get(), test_put_validation(), test_requires_auth() (+8 more)

### Community 66 - "test_mafia_db.py"
Cohesion: 0.25
Nodes (16): _make_game(), test_add_player_rejects_duplicate(), test_create_and_get_game(), test_get_active_game_in_channel_filters_by_status(), test_get_game_by_lobby_and_vote_message(), test_get_night_actions_filters_by_role(), test_list_active_games_excludes_finished_and_cancelled(), test_round_events_roundtrip() (+8 more)

### Community 67 - "RosterCog"
Cohesion: 0.20
Nodes (9): generate_roster_text(), Bot, Guild, Interaction, Member, Live-ростер семьи: список участников по настроенным ролям.  Портировано из FamQ, Debounce: аккумулирует изменения и обновляет сообщение через 10 секунд., RosterCog (+1 more)

### Community 68 - "CTD"
Cohesion: 0.19
Nodes (6): CTD, CTDCloseView, CTDView, Button, Interaction, setup()

### Community 69 - "fakes.py"
Cohesion: 0.17
Nodes (6): DashboardConfig, FakeAsset, FakeColor, FakePermissions, FakePermissions, FakeRole

### Community 70 - "test_lockdown_routes.py"
Cohesion: 0.21
Nodes (12): build(), Test that partial failures during deactivate are logged with Ошибки field in emb, Test that activate returns 503 when guild is unavailable., Test that partial failures are logged with Ошибки field in embed., _StubForbidden, test_activate_guild_unavailable_503(), test_activate_then_status_then_deactivate(), test_activate_with_partial_errors_logs_error_field() (+4 more)

### Community 71 - "load_dashboard_config"
Cohesion: 0.32
Nodes (12): ConfigError, load_dashboard_config(), Exception, test_empty_role_list_raises(), test_frontend_dist_defaults_to_empty_string(), test_frontend_dist_picked_up_when_present(), test_frontend_url_defaults_to_empty_string(), test_frontend_url_picked_up_when_present() (+4 more)

### Community 72 - "ChetBot"
Cohesion: 0.15
Nodes (14): Web Dashboard Index HTML, React Root Mount Element, React Entry Point Script, ChetBot, ChetBot Web Dashboard, ChetBot Official Documentation, aiohttp Dependency, aiohttp-session Dependency (+6 more)

### Community 73 - "mafia.py"
Cohesion: 0.33
Nodes (12): _display_name(), _is_id(), mafia_games_list(), mafia_get(), mafia_public_action(), mafia_public_state(), mafia_put(), Request (+4 more)

### Community 74 - "Giveaways.tsx"
Cohesion: 0.22
Nodes (9): createGiveaway(), endGiveaway(), fetchGiveawayOverview(), Giveaway, GiveawayOverview, rerollGiveaway(), GiveawaysPage(), STATUS_LABEL (+1 more)

### Community 75 - "Welcome"
Cohesion: 0.21
Nodes (5): Interaction, Invite, Member, setup(), Welcome

### Community 76 - "test_audit.py"
Cohesion: 0.30
Nodes (10): audit_middleware(), describe_action(), Request, Аудит действий дашборда: каждое мутирующее действие модератора пишется в stats.d, build_app(), test_describe_action_known_and_fallback(), test_failed_mutation_not_audited(), test_filter_by_moderator() (+2 more)

### Community 77 - "PublicMafiaAction.tsx"
Cohesion: 0.23
Nodes (9): fetchPublicMafia(), MafiaPublicState, submitMafiaAction(), PHASE_LABEL, PublicMafiaActionPage(), ROLE_HINT, ROLE_LABEL, baseState (+1 more)

### Community 78 - "main.py"
Cohesion: 0.17
Nodes (3): ChetBot, main(), Embed

### Community 79 - "access_middleware.py"
Cohesion: 0.24
Nodes (7): Guard an aiohttp handler with the Phase 1 session -> member -> role check., Гейт для списка серверов бота — намеренно хардкод-роль, см. access.py., require_dashboard_access(), require_super_admin(), Request, Response, superadmin_guilds()

### Community 80 - "app.py"
Cohesion: 0.27
Nodes (7): json_error_middleware(), Application, Path, setup_static_routes(), test_asset_path_serves_asset_file(), test_root_path_serves_index_html(), test_unmatched_path_serves_index_html()

### Community 81 - "test_mafia_routes.py"
Cohesion: 0.27
Nodes (10): isolated_db(), isolated_state(), build(), isolated_state(), test_games_list(), test_get_defaults(), test_put_then_get(), test_put_validation() (+2 more)

### Community 82 - "test_welcome_routes.py"
Cohesion: 0.31
Nodes (9): build(), test_get_welcome_settings_defaults_to_enabled_when_file_missing(), test_get_welcome_settings_requires_auth(), test_get_welcome_settings_returns_stored_values(), test_update_welcome_settings_persists(), test_update_welcome_settings_rejects_non_boolean(), test_update_welcome_settings_rejects_non_dict_body(), test_update_welcome_settings_requires_auth() (+1 more)

### Community 83 - "SupplyView"
Cohesion: 0.40
Nodes (4): Button, Interaction, Persistent view: кнопки работают и после перезапуска бота., SupplyView

### Community 84 - "config.py"
Cohesion: 0.47
Nodes (8): _check_channel(), _check_role(), get_config(), Request, Response, update_config(), _validate_relations(), _validate_structure()

### Community 85 - "plugins"
Cohesion: 0.22
Nodes (8): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, typescript, warn

### Community 86 - "DocsSearch.tsx"
Cohesion: 0.33
Nodes (4): DocNavItem, DocsSearchProps, DocsSidebarProps, GROUP_ICONS

### Community 87 - "xp_card.py"
Cohesion: 0.33
Nodes (8): FreeTypeFont, Image, ImageFont, _background(), _circle_avatar(), _font(), Генерация PNG-карточки ранга (аватар, уровень, прогресс-бар, место в топе).  Ф, render_rank_card()

### Community 88 - "setup_session"
Cohesion: 0.43
Nodes (6): derive_fernet_key(), Application, setup_session(), test_derive_fernet_key_differs_per_secret(), test_derive_fernet_key_is_deterministic(), test_derive_fernet_key_is_valid_fernet_key()

### Community 89 - "auto_roles.py"
Cohesion: 0.48
Nodes (6): get_auto_roles(), _get_guild_or_none(), _is_role_assignable(), Request, Response, update_auto_roles()

### Community 90 - "icons.svg"
Cohesion: 0.38
Nodes (6): Bluesky Icon, Discord Icon, Documentation Icon, GitHub Icon, Social Icon, X Icon

### Community 91 - "welcome.py"
Cohesion: 0.60
Nodes (4): get_welcome_settings(), Request, Response, update_welcome_settings()

### Community 92 - "DocsToc.tsx"
Cohesion: 0.50
Nodes (4): DocsToc(), DocsTocProps, slugify(), TocItem

### Community 94 - "Hero Image Graphic"
Cohesion: 1.00
Nodes (3): Hero Image Graphic, Cheterin Isometric Branding Concept, Layered Isometric Architecture Illustration

## Knowledge Gaps
- **183 isolated node(s):** `$schema`, `typescript`, `oxc`, `react/rules-of-hooks`, `warn` (+178 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SelectOption` connect `MafiaCog` to `events.py`, `react`?**
  _High betweenness centrality (0.294) - this node is a cross-community bridge._
- **Why does `force_login()` connect `force_login` to `FakeGuild`, `giveaway_core.py`, `FakeMember`, `supply_core.py`, `moderation.py`, `FakeMessage`, `FakeChannel`, `FakeRole`, `test_voice_routes.py`, `test_events_routes.py`, `make_moderation_app`, `test_feedback_routes.py`, `bot_config.py`, `test_config_routes.py`, `test_family_routes.py`, `fakes.py`, `test_lockdown_routes.py`, `test_audit.py`, `test_mafia_routes.py`, `test_welcome_routes.py`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `FakeMember` (e.g. with `DashboardConfig` and `_StubForbidden`) actually correct?**
  _`FakeMember` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `FakeGuild` (e.g. with `DashboardConfig` and `_StubForbidden`) actually correct?**
  _`FakeGuild` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `FakeBot` (e.g. with `DashboardConfig` and `_StubForbidden`) actually correct?**
  _`FakeBot` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `FakeRole` (e.g. with `DashboardConfig` and `_StubForbidden`) actually correct?**
  _`FakeRole` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `typescript`, `oxc` to the rest of the system?**
  _183 weakly-connected nodes found - possible documentation gaps or missing edges._