export interface DashboardUser {
  id: string
  username: string
  avatar: string | null
  is_admin: boolean
}

export async function fetchCurrentUser(): Promise<DashboardUser | null> {
  const response = await fetch('/api/auth/me', { credentials: 'include' })
  if (response.status === 401 || response.status === 403) {
    return null
  }
  if (!response.ok) {
    throw new Error(`Failed to fetch current user: ${response.status}`)
  }
  return response.json()
}

export async function logout(): Promise<void> {
  await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
}

export function loginUrl(): string {
  return '/api/auth/login'
}

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
    this.name = 'ApiError'
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { credentials: 'include', ...init })
  if (!response.ok) {
    let detail = ''
    try {
      detail = ((await response.json()) as { error?: string }).error ?? ''
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(response.status, detail || `HTTP ${response.status}`)
  }
  return response.json() as Promise<T>
}

const jsonInit = (method: string, body?: unknown): RequestInit => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
})

export interface MemberSummary {
  id: string
  username: string
  display_name: string
  avatar: string | null
  role_count: number
  joined_at: string | null
  is_bot: boolean
}

export interface MembersPage {
  total: number
  page: number
  page_size: number
  members: MemberSummary[]
}

export interface RoleChip {
  id: string
  name: string
  color: string
}

export interface MemberDetail extends Omit<MemberSummary, 'role_count'> {
  created_at: string
  roles: RoleChip[]
  invite_stats: { joins: number; leaves: number; invites: number }
  feedback_case_count: number
}

export interface RoleInfo extends RoleChip {
  position: number
}

export interface LockdownStatus {
  active: boolean
  role_count: number
}

export function fetchMembers(search: string, page: number, pageSize = 20): Promise<MembersPage> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
  if (search) params.set('search', search)
  return apiFetch(`/api/members?${params}`)
}

export function fetchMemberDetail(id: string): Promise<MemberDetail> {
  return apiFetch(`/api/members/${id}`)
}

export async function banMember(id: string, reason: string, deleteMessageDays: 0 | 1 | 7): Promise<void> {
  await apiFetch(`/api/members/${id}/ban`, jsonInit('POST', { reason, delete_message_days: deleteMessageDays }))
}

export async function kickMember(id: string, reason: string): Promise<void> {
  await apiFetch(`/api/members/${id}/kick`, jsonInit('POST', { reason }))
}

export async function fetchRoles(): Promise<RoleInfo[]> {
  const body = await apiFetch<{ roles: RoleInfo[] }>('/api/roles')
  return body.roles
}

export async function grantRole(memberId: string, roleId: string): Promise<void> {
  await apiFetch(`/api/members/${memberId}/roles`, jsonInit('POST', { role_id: roleId }))
}

export async function revokeRole(memberId: string, roleId: string): Promise<void> {
  await apiFetch(`/api/members/${memberId}/roles/${roleId}`, jsonInit('DELETE'))
}

export function fetchLockdownStatus(): Promise<LockdownStatus> {
  return apiFetch('/api/lockdown/status')
}

export async function activateLockdown(): Promise<void> {
  await apiFetch('/api/lockdown/activate', jsonInit('POST'))
}

export async function deactivateLockdown(): Promise<void> {
  await apiFetch('/api/lockdown/deactivate', jsonInit('POST'))
}

export interface ModerationLogEntry {
  type: 'spam_punish' | 'tempban' | 'manual_ban' | 'manual_kick'
  timestamp: string
  user_id: string
  user_display: string
  moderator_id: string | null
  moderator_display: string | null
  reason: string
  extra: string
}

export async function fetchModerationLog(): Promise<ModerationLogEntry[]> {
  const body = await apiFetch<{ events: ModerationLogEntry[] }>('/api/moderation-log')
  return body.events
}

export type MassAssignTarget = 'all' | 'all_except_bots' | 'selected'

export interface MassAssignStatus {
  status: 'running' | 'completed' | 'failed'
  total: number
  processed: number
  succeeded: number
  skipped: number
  failed: number
  errors: string[]
}

export async function startMassAssign(
  roleId: string,
  target: MassAssignTarget,
  memberIds?: string[],
): Promise<string> {
  const body: Record<string, unknown> = { target }
  if (memberIds) body.member_ids = memberIds
  const result = await apiFetch<{ job_id: string }>(`/api/roles/${roleId}/mass-assign`, jsonInit('POST', body))
  return result.job_id
}

export function fetchMassAssignStatus(jobId: string): Promise<MassAssignStatus> {
  return apiFetch(`/api/roles/mass-assign/${jobId}`)
}

export interface ReactionRolePair {
  emoji: string
  role_id: string
}

export interface ReactionRoleEntry {
  message_id: string
  channel_id: string
  pairs: ReactionRolePair[]
}

export interface CustomEmoji {
  id: string
  name: string
  url: string
}

export interface ChannelInfo {
  id: string
  name: string
  category?: string
}

export async function fetchReactionRoles(): Promise<ReactionRoleEntry[]> {
  const body = await apiFetch<{ reaction_roles: ReactionRoleEntry[] }>('/api/reaction-roles')
  return body.reaction_roles
}

export function createReactionRole(
  channelId: string,
  messageId: string,
  pairs: ReactionRolePair[],
): Promise<ReactionRoleEntry> {
  return apiFetch(
    '/api/reaction-roles',
    jsonInit('POST', { channel_id: channelId, message_id: messageId, pairs }),
  )
}

export function updateReactionRole(messageId: string, pairs: ReactionRolePair[]): Promise<ReactionRoleEntry> {
  return apiFetch(`/api/reaction-roles/${messageId}`, jsonInit('PUT', { pairs }))
}

export async function deleteReactionRole(messageId: string): Promise<void> {
  await apiFetch(`/api/reaction-roles/${messageId}`, jsonInit('DELETE'))
}

export async function fetchEmojis(): Promise<CustomEmoji[]> {
  const body = await apiFetch<{ emojis: CustomEmoji[] }>('/api/emojis')
  return body.emojis
}

export async function fetchChannels(): Promise<ChannelInfo[]> {
  const body = await apiFetch<{ channels: ChannelInfo[] }>('/api/channels')
  return body.channels
}

export interface EmbedFieldSpec {
  name: string
  value: string
  inline: boolean
}

export interface EmbedSpec {
  title: string
  description: string
  url: string
  color: string
  author: { name: string; url: string; icon_url: string }
  footer: { text: string; icon_url: string }
  image: { url: string }
  thumbnail: { url: string }
  timestamp: string | null
  fields: EmbedFieldSpec[]
}

export interface EmbedMessagePayload {
  content: string
  embed: EmbedSpec
  role_ids: string[]
}

export interface EmbedMessageResult {
  message_id: string
  channel_id: string
}

export function createEmbedMessage(channelId: string, payload: EmbedMessagePayload): Promise<EmbedMessageResult> {
  return apiFetch('/api/embed-messages', jsonInit('POST', { channel_id: channelId, ...payload }))
}

export function fetchEmbedMessage(channelId: string, messageId: string): Promise<EmbedMessagePayload> {
  return apiFetch(`/api/embed-messages/${channelId}/${messageId}`)
}

export function updateEmbedMessage(
  channelId: string,
  messageId: string,
  payload: EmbedMessagePayload,
): Promise<EmbedMessageResult> {
  return apiFetch(`/api/embed-messages/${channelId}/${messageId}`, jsonInit('PUT', payload))
}

export interface FeedbackCaseSummary {
  case_id: string
  category_key: string
  category_title: string
  submitter_id: string
  submitter_display: string
  status: 'pending' | 'approved' | 'denied'
  created_at: string | null
}

export interface FeedbackCaseField {
  key: string
  label: string
  value: string
}

export interface FeedbackCaseDetail extends FeedbackCaseSummary {
  fields: FeedbackCaseField[]
  public_channel_id: string | null
  public_message_id: string | null
  thread_id: string | null
}

export async function fetchFeedbackCases(status?: string): Promise<FeedbackCaseSummary[]> {
  const path = status ? `/api/feedback-cases?status=${status}` : '/api/feedback-cases'
  const body = await apiFetch<{ cases: FeedbackCaseSummary[] }>(path)
  return body.cases
}

export function fetchFeedbackCaseDetail(caseId: string): Promise<FeedbackCaseDetail> {
  return apiFetch(`/api/feedback-cases/${caseId}`)
}

export async function decideFeedbackCase(caseId: string, approved: boolean): Promise<void> {
  await apiFetch(`/api/feedback-cases/${caseId}/decide`, jsonInit('POST', { approved }))
}

export interface FeedbackCategoryFieldSpec {
  key: string
  label: string
  style: 'short' | 'paragraph'
  required: boolean
  max_length: number
}

export interface FeedbackCategorySpec {
  key: string
  title: string
  button_label: string
  channel_id: string
  case_prefix: string
  case_title: string
  thread_name: string
  review_role_ids: string[]
  approved_text: string
  denied_text: string
  modal_title: string
  fields: FeedbackCategoryFieldSpec[]
  mini_summary_key: string
}

export async function fetchFeedbackCategories(): Promise<FeedbackCategorySpec[]> {
  const body = await apiFetch<{ categories: FeedbackCategorySpec[] }>('/api/feedback-categories')
  return body.categories
}

export function createFeedbackCategory(spec: FeedbackCategorySpec): Promise<FeedbackCategorySpec> {
  return apiFetch('/api/feedback-categories', jsonInit('POST', spec))
}

export function updateFeedbackCategory(
  key: string,
  spec: Omit<FeedbackCategorySpec, 'key'>,
): Promise<FeedbackCategorySpec> {
  return apiFetch(`/api/feedback-categories/${key}`, jsonInit('PUT', spec))
}

export async function deleteFeedbackCategory(key: string): Promise<void> {
  await apiFetch(`/api/feedback-categories/${key}`, jsonInit('DELETE'))
}

export function publishFeedbackPanel(channelId: string): Promise<{ ok: boolean; message_id: string }> {
  return apiFetch('/api/feedback-panel/publish', jsonInit('POST', { channel_id: channelId }))
}

export interface EventParticipantSolo {
  user_id: string
  ign: string
}

export interface EventParticipantTeamCaptain {
  user_id: string
  team_name: string
  members: string
}

export interface EventParticipantTeamCodeMember {
  user_id: string
  ign: string
  is_captain: boolean
}

export interface EventParticipantTeamCode {
  team_code: string
  team_name: string
  members: EventParticipantTeamCodeMember[]
}

export interface EventPollOption {
  label: string
  votes: number
  percent: number
}

export interface EventSummary {
  message_id: string
  type: 'tournament' | 'poll'
  title: string
  status: 'open' | 'closed'
  channel_id: string
  count: number
}

export interface EventDetail extends EventSummary {
  description: string
  role_reward: string | null
  mode?: 'solo' | 'team_captain' | 'team_code'
  max_limit?: number
  team_size?: number
  participants?: (EventParticipantSolo | EventParticipantTeamCaptain | EventParticipantTeamCode)[]
  multi_select?: boolean
  options?: EventPollOption[]
}

export async function fetchEvents(status?: string): Promise<EventSummary[]> {
  const path = status ? `/api/events?status=${status}` : '/api/events'
  const body = await apiFetch<{ events: EventSummary[] }>(path)
  return body.events
}

export function fetchEventDetail(messageId: string): Promise<EventDetail> {
  return apiFetch(`/api/events/${messageId}`)
}

export async function closeEvent(messageId: string): Promise<void> {
  await apiFetch(`/api/events/${messageId}/close`, jsonInit('POST'))
}

export async function deleteEvent(messageId: string): Promise<void> {
  await apiFetch(`/api/events/${messageId}`, jsonInit('DELETE'))
}

export async function notifyEventParticipants(
  messageId: string,
  message: string,
): Promise<{ success: number; failed: number }> {
  const result = await apiFetch<{ success: number; failed: number }>(`/api/events/${messageId}/notify`, jsonInit('POST', { message }))
  return { success: result.success, failed: result.failed }
}

export interface CreateEventSpec {
  channel_id: string
  type: 'tournament' | 'poll'
  title: string
  description: string
  banner_url: string
  ping: 'none' | 'everyone' | 'here'
  mode: 'solo' | 'team_captain' | 'team_code'
  require_info: boolean
  max_limit: number
  team_size: number
  role_reward: string | null
  options: string[]
  multi_select: boolean
}

export function createEvent(spec: CreateEventSpec): Promise<EventDetail> {
  return apiFetch('/api/events', jsonInit('POST', spec))
}

export interface BotConfig {
  LOG_CHANNEL_ID: string
  SPAM_EXCEPTION_CHANNELS: string[]
  TEMPBAN_CHANNEL_ID: string
  SPAM_LOG_CHANNEL_ID: string
  SPAM_LOG_ROLE_ID: string
  WELCOME_CHANNEL_ID: string
  INVITE_LOG_CHANNEL_ID: string
  ANNOUNCEMENTS_CHANNEL_ID: string
  RULES_CHANNEL_ID: string
  ROLES_CHANNEL_ID: string
  SEARCH_PLAYERS_CHANNEL_ID: string
  CTD_ROLE_ID: string
  CTD_CHANNEL_ID: string
  BUTTON_CREATE_ALLOWED_ROLES: string[]
  BUTTON_WEBHOOK_URL: string
  SERVER_INVITE_LINK: string
  VOICE_LOBBY_CHANNEL_ID: string
  VOICE_PANEL_CHANNEL_ID: string
  VOICE_LOG_CHANNEL_ID: string
  VOICE_PANEL_THUMB_URL: string
  SUPPLY_ROLE_ID: string
  SUPPLY_VOICE_CHANNEL_ID: string
  SUPPLY_LOG_CHANNEL_ID: string
  SUPPLY_REMINDER_MINUTES: string
}

export function fetchConfig(): Promise<BotConfig> {
  return apiFetch('/api/config')
}

export function updateConfig(config: BotConfig): Promise<BotConfig> {
  return apiFetch('/api/config', jsonInit('PUT', config))
}

export interface SupplyMember {
  id: string
  display: string
}

export interface Supply {
  id: string
  initiator_id: string
  initiator_display: string
  opponent: string
  limit: number
  time_str: string
  target_ts: number
  status: 'active' | 'finished' | 'cancelled'
  participants: SupplyMember[]
  reserve: SupplyMember[]
  channel_id: string
  created_at: string
  closed_at: string | null
}

export interface SupplyStatEntry {
  user_id: string
  display: string
  count: number
}

export interface SupplyOverview {
  active: Supply[]
  history: Supply[]
  stats: SupplyStatEntry[]
}

export function fetchSupplyOverview(): Promise<SupplyOverview> {
  return apiFetch('/api/supply')
}

export function createSupply(input: {
  channel_id: string
  opponent: string
  limit: number
  time_str: string
}): Promise<Supply> {
  return apiFetch('/api/supply', jsonInit('POST', input))
}

export async function closeSupply(id: string): Promise<void> {
  await apiFetch(`/api/supply/${id}/close`, jsonInit('POST'))
}

export async function cancelSupply(id: string): Promise<void> {
  await apiFetch(`/api/supply/${id}/cancel`, jsonInit('POST'))
}

export interface VoiceRoom {
  channel_id: string
  name: string
  owner_id: string
  owner_display: string
  is_closed: boolean
  user_limit: number
  member_count: number
  exists: boolean
}

export async function fetchVoiceRooms(): Promise<VoiceRoom[]> {
  const body = await apiFetch<{ rooms: VoiceRoom[] }>('/api/voice/rooms')
  return body.rooms
}

export async function deleteVoiceRoom(channelId: string): Promise<void> {
  await apiFetch(`/api/voice/rooms/${channelId}`, { method: 'DELETE' })
}

export async function publishVoicePanel(): Promise<void> {
  await apiFetch('/api/voice/panel/publish', jsonInit('POST'))
}

export interface NewsMapping {
  source_channel_id: string
  target_channel_id: string
  label: string
}

export interface NewsSettings {
  enabled: boolean
  source_guild_id: string
  source_bot_ids: string[]
  log_channel_id: string
  mappings: NewsMapping[]
}

export function fetchNewsSettings(): Promise<NewsSettings> {
  return apiFetch('/api/news')
}

export function updateNewsSettings(settings: NewsSettings): Promise<NewsSettings> {
  return apiFetch('/api/news', jsonInit('PUT', settings))
}

export interface BracketMatch {
  slot_a: string | null
  slot_b: string | null
  winner: 'a' | 'b' | 'draw' | null
}

export type BracketFormat = 'single_elim' | 'double_elim' | 'round_robin'

export interface BracketStandingsRow {
  entry: string
  played: number
  wins: number
  draws: number
  losses: number
  points: number
}

export interface BracketSummary {
  id: string
  title: string
  format: BracketFormat
  source_event_id: string | null
  entry_count: number
  created_at: string
}

export interface BracketDetail {
  id: string
  title: string
  format: BracketFormat
  source_event_id: string | null
  entries: string[]
  rounds: BracketMatch[][]
  share_token: string | null
  de?: {
    winners: BracketMatch[][]
    losers: BracketMatch[][]
    final: BracketMatch
  }
  rr_rounds?: BracketMatch[][]
  standings?: BracketStandingsRow[]
}

export async function fetchBrackets(): Promise<BracketSummary[]> {
  const body = await apiFetch<{ brackets: BracketSummary[] }>('/api/brackets')
  return body.brackets
}

export function fetchBracketDetail(id: string): Promise<BracketDetail> {
  return apiFetch(`/api/brackets/${id}`)
}

export async function fetchEventEntries(eventId: string): Promise<string[]> {
  const body = await apiFetch<{ entries: string[] }>(`/api/brackets/entries-from-event/${eventId}`)
  return body.entries
}

export function createBracket(
  title: string,
  entries: string[],
  sourceEventId: string | null,
  format: BracketFormat = 'single_elim',
): Promise<BracketDetail> {
  return apiFetch('/api/brackets', jsonInit('POST', { title, entries, source_event_id: sourceEventId, format }))
}

export async function deleteBracket(id: string): Promise<void> {
  await apiFetch(`/api/brackets/${id}`, jsonInit('DELETE'))
}

export function setBracketMatchWinner(
  id: string,
  roundIndex: number,
  matchIndex: number,
  winner: 'a' | 'b' | 'draw' | null,
  segment: 'W' | 'L' | 'F' = 'W',
): Promise<BracketDetail> {
  return apiFetch(
    `/api/brackets/${id}/matches/${roundIndex}/${matchIndex}/winner`,
    jsonInit('POST', { winner, segment }),
  )
}

export async function enableBracketShare(id: string): Promise<string> {
  const result = await apiFetch<{ share_token: string }>(`/api/brackets/${id}/share`, jsonInit('POST'))
  return result.share_token
}

export async function disableBracketShare(id: string): Promise<void> {
  await apiFetch(`/api/brackets/${id}/share`, jsonInit('DELETE'))
}

export function fetchPublicBracket(token: string): Promise<BracketDetail> {
  return apiFetch(`/api/public/brackets/${token}`)
}

export interface WelcomeSettings {
  channel_enabled: boolean
  dm_enabled: boolean
}

export function fetchWelcomeSettings(): Promise<WelcomeSettings> {
  return apiFetch('/api/welcome-settings')
}

export function updateWelcomeSettings(settings: WelcomeSettings): Promise<WelcomeSettings> {
  return apiFetch('/api/welcome-settings', jsonInit('PUT', settings))
}

export interface AutoRolesSettings {
  role_ids: string[]
}

export function fetchAutoRoles(): Promise<AutoRolesSettings> {
  return apiFetch('/api/auto-roles')
}

export function updateAutoRoles(roleIds: string[]): Promise<AutoRolesSettings> {
  return apiFetch('/api/auto-roles', jsonInit('PUT', { role_ids: roleIds }))
}

// ────────────────────────── Логирование событий ──────────────────────────

export interface ServerLogEventConfig {
  enabled: boolean
  channel_id: string
}

export interface ServerLogSettings {
  labels: Record<string, string>
  events: Record<string, ServerLogEventConfig>
}

export function fetchServerLog(): Promise<ServerLogSettings> {
  return apiFetch('/api/serverlog')
}

export function updateServerLog(events: Record<string, ServerLogEventConfig>): Promise<ServerLogSettings> {
  return apiFetch('/api/serverlog', jsonInit('PUT', { events }))
}

// ────────────────────────── Система уровней ──────────────────────────

export interface XpScopeSettings {
  enabled: boolean
  ignored_roles: string[]
  target_channels: string[]
  ignored_channels: string[]
  multiplier: number
}

export interface XpVoiceSettings extends XpScopeSettings {
  max_count: number
}

export interface XpLevelReward {
  level: number
  role_ids: string[]
}

export interface XpVoiceReward {
  minutes: number
  role_ids: string[]
}

export interface XpSettings {
  enabled: boolean
  public_leaderboard: boolean
  reset_on_leave: boolean
  text: XpScopeSettings
  voice: XpVoiceSettings
  announce: {
    enabled: boolean
    channel_id: string
    template: string
    delete_after: number
  }
  level_rewards: XpLevelReward[]
  voice_rewards: XpVoiceReward[]
}

export interface XpOverview {
  settings: XpSettings
  member_count: number
  has_card_bg: boolean
}

export interface XpLeaderboardEntry {
  user_id: string
  display: string
  avatar: string | null
  on_server: boolean
  xp: number
  level: number
  xp_into_level: number
  xp_step: number
  messages: number
  voice_seconds: number
  voice_time_text: string
  rank: number
}

export interface XpLeaderboardPage {
  total: number
  page: number
  page_size: number
  entries: XpLeaderboardEntry[]
}

export function fetchXpOverview(): Promise<XpOverview> {
  return apiFetch('/api/xp')
}

export function updateXpSettings(settings: XpSettings): Promise<{ settings: XpSettings }> {
  return apiFetch('/api/xp', jsonInit('PUT', settings))
}

export function fetchXpLeaderboard(page: number, search = ''): Promise<XpLeaderboardPage> {
  const params = new URLSearchParams({ page: String(page) })
  if (search) params.set('search', search)
  return apiFetch(`/api/xp/leaderboard?${params}`)
}

export async function setMemberXp(userId: string, xp: number): Promise<void> {
  await apiFetch(`/api/xp/members/${userId}`, jsonInit('PUT', { xp }))
}

export async function resetMemberXp(userId: string): Promise<void> {
  await apiFetch(`/api/xp/members/${userId}/reset`, jsonInit('POST'))
}

export async function resetAllXp(): Promise<void> {
  await apiFetch('/api/xp/reset-all', jsonInit('POST'))
}

export async function uploadCardBg(file: Blob): Promise<void> {
  const response = await fetch('/api/xp/card-bg', { method: 'POST', credentials: 'include', body: file })
  if (!response.ok) throw new ApiError(response.status, 'upload_failed')
}

export async function deleteCardBg(): Promise<void> {
  await apiFetch('/api/xp/card-bg', { method: 'DELETE' })
}

export interface PublicLeaderboardEntry {
  rank: number
  display: string
  avatar: string | null
  level: number
  xp: number
  voice_time_text: string
}

export function fetchPublicLeaderboard(): Promise<{ guild_name: string; entries: PublicLeaderboardEntry[] }> {
  return apiFetch('/api/public/leaderboard')
}

// ────────────────────────── Статистика войса ──────────────────────────

export interface VoiceStats {
  days: number
  session_count: number
  total_seconds: number
  total_time_text: string
  peak_concurrent: number
  by_hour_minutes: number[]
  by_weekday_minutes: number[]
  top_channels: { name: string; seconds: number; time_text: string }[]
  top_users: { user_id: string; display: string; avatar: string | null; seconds: number; time_text: string }[]
}

export function fetchVoiceStats(days: number): Promise<VoiceStats> {
  return apiFetch(`/api/voice-stats?days=${days}`)
}

// ────────────────────────── Аудит ──────────────────────────

export interface AuditEntry {
  ts: number
  moderator_id: string
  moderator_name: string
  method: string
  path: string
  action: string
  status: number
  details: string
}

export interface AuditPage {
  total: number
  page: number
  page_size: number
  entries: AuditEntry[]
}

export function fetchAudit(page: number, moderator?: string): Promise<AuditPage> {
  const params = new URLSearchParams({ page: String(page) })
  if (moderator) params.set('moderator', moderator)
  return apiFetch(`/api/audit?${params}`)
}

// ────────────────────────── Стрим-уведомления ──────────────────────────

export interface StreamSubscription {
  id: string
  platform: 'twitch' | 'youtube'
  identifier: string
  display_name: string
  avatar_url: string
  enabled: boolean
  channel_id: string
  ping_role_id: string
  template: string
  keywords: string[]
  keyword_mode: 'any' | 'all'
  min_interval_minutes: number
  last_stream_id: string
}

export function fetchStreams(): Promise<{ twitch_configured: boolean; subscriptions: StreamSubscription[] }> {
  return apiFetch('/api/streams')
}

export function createStreamSubscription(input: {
  platform: 'twitch' | 'youtube'
  query: string
  channel_id: string
}): Promise<StreamSubscription> {
  return apiFetch('/api/streams', jsonInit('POST', input))
}

export function updateStreamSubscription(
  id: string,
  fields: Partial<Pick<StreamSubscription, 'enabled' | 'channel_id' | 'ping_role_id' | 'template' | 'keywords' | 'keyword_mode' | 'min_interval_minutes'>>,
): Promise<StreamSubscription> {
  return apiFetch(`/api/streams/${id}`, jsonInit('PATCH', fields))
}

export async function deleteStreamSubscription(id: string): Promise<void> {
  await apiFetch(`/api/streams/${id}`, { method: 'DELETE' })
}

// ────────────────────────── Шаблоны эмбедов ──────────────────────────

export interface EmbedTemplate {
  id: string
  name: string
  content: string
  embed: EmbedSpec
  role_ids: string[]
}

export async function fetchEmbedTemplates(): Promise<EmbedTemplate[]> {
  const body = await apiFetch<{ templates: EmbedTemplate[] }>('/api/embed-templates')
  return body.templates
}

export function saveEmbedTemplate(input: {
  name: string
  content: string
  embed: EmbedSpec
  role_ids: string[]
}): Promise<EmbedTemplate> {
  return apiFetch('/api/embed-templates', jsonInit('POST', input))
}

export async function deleteEmbedTemplate(id: string): Promise<void> {
  await apiFetch(`/api/embed-templates/${id}`, { method: 'DELETE' })
}

// ────────────────────────── Семья ──────────────────────────

export interface FamilyTargetRole {
  label: string
  role_id: string
}

export interface FamilySettings {
  enabled: boolean
  roster: {
    list_channel_id: string
    target_roles: FamilyTargetRole[]
  }
  applications: {
    application_channel_id: string
    log_channel_id: string
    staff_role_ids: string[]
    ticket_manager_role_id: string
    notify_role_id: string
    ticket_active_role_id: string
    approve_role_ids: string[]
    yes_emoji_id: string
    no_emoji_id: string
    thread_archive_minutes: number
  }
  birthdays: {
    channel_id: string
    list_channel_id: string
  }
}

export function fetchFamilySettings(): Promise<FamilySettings> {
  return apiFetch('/api/family')
}

export function updateFamilySettings(settings: FamilySettings): Promise<FamilySettings> {
  return apiFetch('/api/family', jsonInit('PUT', settings))
}

export interface FamilyRosterGroup {
  label: string
  role_id: string
  role_found: boolean
  members: { id: string; display: string }[]
}

export function fetchFamilyRoster(): Promise<{ groups: FamilyRosterGroup[] }> {
  return apiFetch('/api/family/roster')
}

export type FamilyTicketStatus = 'open' | 'approved' | 'denied' | 'closed'

export interface FamilyTicket {
  user_id: string
  display: string
  status: FamilyTicketStatus
  nickname: string
  game_level: string
  faction_pref: string
  online_timezone: string
  real_name: string
  real_age: string
  about_text: string
  why_join: string
  inviter_nickname: string | null
  created_at: string
  handled_by: string | null
  thread_id: string | null
}

export interface FamilyTicketsPage {
  total: number
  page: number
  page_size: number
  entries: FamilyTicket[]
}

export function fetchFamilyTickets(status: FamilyTicketStatus | '', page: number): Promise<FamilyTicketsPage> {
  const params = new URLSearchParams({ page: String(page) })
  if (status) params.set('status', status)
  return apiFetch(`/api/family/tickets?${params}`)
}

export async function decideFamilyTicket(userId: string, decision: 'approve' | 'deny' | 'close'): Promise<void> {
  await apiFetch(`/api/family/tickets/${userId}/${decision}`, jsonInit('POST'))
}

export interface FamilyBirthday {
  user_id: string
  display: string
  day: number
  month: number
  date_display: string
}

export function fetchFamilyBirthdays(): Promise<{ entries: FamilyBirthday[] }> {
  return apiFetch('/api/family/birthdays')
}

export async function setFamilyBirthday(userId: string, date: string): Promise<{ date_display: string }> {
  return apiFetch('/api/family/birthdays', jsonInit('POST', { user_id: userId, date }))
}

export async function deleteFamilyBirthday(userId: string): Promise<void> {
  await apiFetch(`/api/family/birthdays/${userId}`, { method: 'DELETE' })
}

// ────────────────────────── Мафия ──────────────────────────

export interface MafiaSettings {
  enabled: boolean
  default_min_players: number
  default_max_players: number
  default_night_timer_sec: number
  default_day_discussion_timer_sec: number
  default_day_vote_timer_sec: number
  log_channel_id: string
}

export function fetchMafiaSettings(): Promise<MafiaSettings> {
  return apiFetch('/api/mafia')
}

export function updateMafiaSettings(settings: MafiaSettings): Promise<MafiaSettings> {
  return apiFetch('/api/mafia', jsonInit('PUT', settings))
}

export type MafiaGameStatus = 'lobby' | 'active' | 'finished' | 'cancelled'
export type MafiaGamePhase = 'lobby' | 'night' | 'day_discussion' | 'day_vote' | 'ended'

export interface MafiaGameSummary {
  id: number
  channel_id: string
  channel_name: string
  status: MafiaGameStatus
  phase: MafiaGamePhase
  round_number: number
  player_count: number
  alive_count: number
  created_at: string
}

export async function fetchMafiaGames(): Promise<MafiaGameSummary[]> {
  const body = await apiFetch<{ games: MafiaGameSummary[] }>('/api/mafia/games')
  return body.games
}

export type MafiaRole = 'mafia' | 'citizen' | 'doctor' | 'sheriff'

export interface MafiaPlayerRef {
  user_id: string
  display_name: string
}

export interface MafiaPublicState {
  game_status: MafiaGameStatus
  phase: MafiaGamePhase
  round_number: number
  phase_deadline_ts: number | null
  your_role: MafiaRole | null
  your_alive: boolean
  action_required: boolean
  your_action_submitted: boolean
  your_submitted_target: string | null
  alive_players: MafiaPlayerRef[]
  teammates?: MafiaPlayerRef[]
  mafia_votes?: { actor: string; target: string | null }[]
}

export function fetchPublicMafia(token: string): Promise<MafiaPublicState> {
  return apiFetch(`/api/public/mafia/${token}`)
}

export async function submitMafiaAction(token: string, targetUserId: string | null): Promise<void> {
  await apiFetch(`/api/public/mafia/${token}/action`, jsonInit('POST', { target_user_id: targetUserId }))
}
