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
