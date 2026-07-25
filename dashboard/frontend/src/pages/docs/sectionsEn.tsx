import {
  Code,
  H,
  H3,
  Note,
  OL,
  P,
  Table,
  UL,
  Warn,
  type DocSection,
} from './docPrimitives'

export const DOC_SECTIONS_EN: DocSection[] = [

  // ────────────────────────── GENERAL ──────────────────────────
  {
    id: 'vvedenie',
    title: 'Introduction',
    group: 'General',
    content: (
      <>
        <H>What is Cheterin?</H>
        <P>
          Cheterin is a multi-purpose Discord bot with a web control panel. It covers what a gaming community needs:
          moderation and raid protection, levels, server logging, tickets and feedback, welcomes and roles, a message
          builder, events, polls, brackets, economy and casino, custom commands, scheduled and sticky messages, GTA5RP
          supply runs and family tools, private voice rooms, stream notifications, and more.
        </P>
        <P>
          The idea is simple: <strong>few chat commands, most setup in the browser</strong>. Almost every feature has
          its own panel section, and changes apply right away — no bot restart.
        </P>

        <H>How the panel works</H>
        <UL>
          <li>
            Sign in with Discord, pick a server you can manage, then turn modules on and configure them in the menu.
          </li>
          <li>
            Each server has its own settings. Enabling something on one server does not affect another.
          </li>
          <li>
            On the home page and under Server settings you can check <strong>Setup health</strong> — whether the bot
            has the critical Discord permissions it needs.
          </li>
        </UL>

        <H>Several servers</H>
        <P>
          Add the bot via an invite link. In the panel, choose which server to manage. You need{' '}
          <strong>Manage Server</strong> or Administrator on that server. New servers start with modules off. Some
          tools (CTD tickets, news relay, Super Admin) appear only on the main/staff server.
        </P>

        <H>Full module list</H>
        <Table
          headers={['Module', 'What it does', 'Panel section']}
          rows={[
            ['Member levels', 'XP for text and voice, reward roles, /rank, leaderboard', 'Member levels'],
            ['Voice statistics', 'Activity by hour/day, top channels and members', 'Voice statistics'],
            ['Logging', 'Server events to Discord channels, per event type', 'Logging'],
            ['Dashboard audit', 'Which moderators changed what in the panel', 'Dashboard audit'],
            ['Streams & subscriptions', 'Twitch stream and YouTube video notifications', 'Streams & subscriptions'],
            ['Anti-spam', 'Mass mentions (@everyone/roles) → 24h timeout and a 20-minute message purge', 'Moderation'],
            ['Spam traps', 'Trap channel: a non-admin message auto-bans (message purge) and unbans a few seconds later', 'Moderation'],
            ['Lockdown', 'Emergency server isolation during a raid', 'Moderation'],
            ['CTD tickets', 'Private support threads with auto-close', 'Feedback & tickets'],
            ['Feedback', 'Category-based submissions with moderator decisions', 'Feedback & tickets'],
            ['Welcomes', 'Channel message + DM guide for newcomers', 'Server entry'],
            ['Invite tracker', 'Who invited whom, joins and leaves', 'Server entry → Invites'],
            ['Auto-roles', 'Roles for new members on join', 'Server entry → Auto-roles'],
            ['Sticky roles', 'Remember roles on leave and restore them on rejoin', 'Server entry → Sticky roles'],
            ['Reaction roles', 'Self-assign roles via reactions', 'Buttons & embeds'],
            ['Embed Builder', 'Embed constructor, form buttons, templates', 'Buttons & embeds'],
            ['Events', 'Events and polls with join buttons', 'Events & polls'],
            ['Tournament brackets', 'Single/Double Elimination and Round Robin with a public link', 'Events → Brackets'],
            ['Mafia', 'Role-playing game: lobby in Discord; full match on a personal link', 'Mafia'],
            ['Bunker', 'Role-playing game: lobby in Discord; character card and voting on a personal link', 'Bunker'],
            ['Giveaways', 'Prize draws with timer, reroll, and auto winner pick', 'Events → Giveaways'],
            ['Daily topic', 'Question/topic of the day on a schedule', 'Daily topic'],
            ['Fun', 'Russian roulette, emoji roulette, Auto-Emoji, and Russian Wordle', 'Fun'],
            ['Economy', 'Server currency: activity payouts, transfers, role shop, weekly report', 'Economy'],
            ['Casino', 'Slots, coinflip, blackjack, Russian roulette bets, leaderboard', 'Casino'],
            ['Custom commands', 'Trigger → reply rules (exact or contains match)', 'Custom commands'],
            ['Scheduled messages', 'One-shot or recurring posts on a schedule', 'Messages → Scheduled'],
            ['Sticky messages', 'Keep a message at the bottom of a channel by re-posting', 'Messages → Sticky'],
            ['Polls', 'Dedicated polls with live tallies; end early from the panel', 'Events → Polls'],
            ['Timed roles', 'Temporary role grants that expire automatically', 'Members → Timed roles'],
            ['Birthdays', 'Server-wide birthday calendar and announcements', 'Birthdays'],
            ['Command preview', 'Try bot replies in the panel without posting to Discord', 'Custom commands → Preview'],
            ['Server timezone', 'Timezone for schedules, Wordle day, birthdays, supply times, voice-stats hours', 'Server settings'],
            ['Setup health', 'Check that the bot has critical permissions', 'Home / Server settings'],
            ['Owner alerts', 'Notify the owner on missing permissions, mass bans, or module errors', 'Server settings'],
            ['Automod', 'Message filters with punishments and warn escalation', 'Automod'],
            ['Anti-raid', 'Auto-lockdown on a surge of fresh-account joins — off by default', 'Moderation → Anti-raid'],
            ['Verification', '“I am not a bot” / accept-rules panel; optional re-verify — off by default', 'Moderation → Verification'],
            ['Supply runs', 'Member sign-ups with reserve list and reminders', 'Supply runs'],
            ['Family', 'Role-based roster, join applications via tickets, family birthdays', 'Family'],
            ['Private voice rooms', 'Personal voice channels with a control panel', 'Private voice rooms'],
            ['News relay', 'Forward messages from a source server', 'News relay'],
            ['Bulk role assign', 'Background role assignment to many members', 'Members & roles'],
            ['Super Admin', 'List of servers the bot is in', 'Super Admin'],
          ]}
        />
      </>
    ),
  },
  {
    id: 'start',
    title: 'Getting started',
    group: 'General',
    content: (
      <>
        <H>Adding the bot to your server</H>
        <OL>
          <li>Open the panel (for example, <Code>https://cheterin.online</Code>) and sign in with Discord.</li>
          <li>
            On the server picker, click <strong>Add bot</strong> next to the server you want (or use the invite link).
            You need Manage Server on that guild to add the bot.
          </li>
          <li>
            After joining, the bot sends a welcome. All modules are off by default — enable and configure what you need
            in the panel.
          </li>
        </OL>

        <H>Signing into the panel</H>
        <OL>
          <li>Open the panel URL in your browser (for example, <Code>https://cheterin.online</Code>).</li>
          <li>Click <strong>Sign in with Discord</strong>.</li>
          <li>
            Discord asks you to authorize the app. It only needs your basic profile and the list of servers you are in,
            so the panel can show which ones you can manage.
          </li>
          <li>
            Pick a server on the “Select server” page. You can switch servers later from the menu in the top right.
          </li>
        </OL>
        <Note>
          🔐 <strong>Passwords are never requested.</strong> Sign-in happens only on Discord&apos;s side — the service
          receives your ID, name, avatar, and server list with permission flags.
        </Note>

        <H>Who has access</H>
        <P>
          Settings for a given server are available to members with <strong>Manage Server</strong> or Administrator on
          that server. If you lose those permissions, panel access stops right away. Super Admin is visible only to
          super-admins of the main server.
        </P>

        <H>Navigation</H>
        <Table
          headers={['Section', 'Purpose']}
          rows={[
            ['Member levels', 'XP settings, rewards, leaderboard, member editing'],
            ['Economy', 'Currency, XP rate, daily bonus, transfers, role shop, balance top, weekly report'],
            ['Casino', 'Slots / coinflip / blackjack, Russian roulette bets, leaderboard'],
            ['Voice statistics', 'Activity charts, top channels and members'],
            ['Private voice rooms', 'Active rooms, publish control panel'],
            ['Family', 'Module toggle, role roster, ticket applications, birthdays'],
            ['Supply runs', 'Active runs, history, top participants, create a run'],
            ['Feedback & tickets', 'Feedback cases, categories, ticket panel'],
            ['Events & polls', 'Tabs: events, giveaways, polls, tournament brackets'],
            ['Messages', 'Tabs: scheduled posts and sticky messages'],
            ['Buttons & embeds', 'Embed Builder, templates, form buttons, reaction roles'],
            ['Birthdays', 'Member birthday calendar and announce channel'],
            ['Fun', 'Module toggle, Russian roulette timeout and cooldown, Auto-Emoji, Wordle'],
            ['Streams & subscriptions', 'Twitch streamer and YouTube channel subscriptions; test announce'],
            ['Daily topic', 'Topic list, channel and publish times, manual publish'],
            ['Mafia', 'Module toggle, default players and timers, log channel, active games'],
            ['Bunker', 'Module toggle, default players and timers, active games, special-ability requests'],
            ['Logging', 'Toggle and channel for each server event type'],
            [
              'Moderation',
              'Tabs: Lockdown & log, Settings (server logging), Anti-spam, Spam traps, Verification, Anti-raid',
            ],
            ['Automod', 'Message filters, punishments, warn escalation'],
            [
              'Server entry',
              'Welcomes, goodbyes, DM guide, auto-roles, sticky roles, invites; test send',
            ],
            ['Members & roles', 'Member search, cards, bans/kicks, bulk roles, timed roles'],
            ['Custom commands', 'Trigger → reply rules; Preview tab without posting to Discord'],
            ['Dashboard audit', 'History of moderator actions in the panel'],
            [
              'Server settings',
              'Bot language (RU/EN), server timezone, setup health, owner alerts',
            ],
            ['Super Admin', 'Bot server list, news relay, CTD tickets (main server only)'],
          ]}
        />
      </>
    ),
  },
  {
    id: 'config',
    title: 'Module channels and roles',
    group: 'General',
    content: (
      <>
        <P>
          There is no separate “Configuration” page: channels and roles are set in the matching panel sections
          (Settings tab for Supply runs, Private voice rooms, Buttons & embeds; Settings / Anti-spam / Spam traps under
          Moderation; Server entry for welcomes and roles). Values are stored per server and apply immediately.
        </P>

        <H>Moderation and spam</H>
        <P>
          <strong>Moderation → Settings:</strong> shared server logging channel.{' '}
          <strong>Moderation → Anti-spam</strong> and <strong>Spam traps:</strong> their own channels and options.
        </P>
        <Table
          headers={['Setting', 'Description']}
          rows={[
            ['Server log channel', 'Main log: DMs, tickets, moderator actions, and fallback for other modules.'],
            ['Spam trap channel', 'Trap channel: a non-admin message triggers an automatic ban and quick unban.'],
            ['Spam trap log channel', 'Where the spam-trap report is posted (if empty — spam log or server log).'],
            ['Spam log channel', 'Spam incident notifications (with Ban/Leave buttons).'],
            ['Spam alert role', 'Role that is only pinged in the spam log — not applied to the offender; punishment is a 24-hour timeout.'],
            ['Anti-spam exception channels', 'Channels where anti-spam does not punish (e.g. bot-commands).'],
          ]}
        />

        <H>Welcomes and onboarding</H>
        <Table
          headers={['Setting', 'Description']}
          rows={[
            ['Welcome channel', 'Public welcome channel for new members.'],
            ['Invite log channel', 'Invite log (who invited whom).'],
            ['Announcements channel', 'Linked in the newcomer DM guide.'],
            ['Rules channel', 'Linked in the DM guide.'],
            ['Roles channel', 'Role-pick channel — for the DM guide.'],
            ['LFG channel', 'Looking-for-teammates channel — for the DM guide.'],
          ]}
        />

        <H>Tickets (CTD)</H>
        <Note>
          Main-server feature: configured under “CTD tickets” in the Super Admin group (visible only to super-admins on
          the main server).
        </Note>
        <Table
          headers={['Setting', 'Description']}
          rows={[
            ['Support role', 'Support team role: invited into tickets and can close them.'],
            ['Panel channel', 'Channel where the ticket creation panel is posted.'],
          ]}
        />

        <H>Buttons and webhooks</H>
        <Table
          headers={['Setting', 'Description']}
          rows={[
            ['Button creator roles', 'Roles allowed to create form buttons.'],
            ['Form webhook', 'Webhook that receives form answers.'],
            ['Server invite link', 'Permanent server invite link (used in some DMs).'],
          ]}
        />

        <H>Private voice rooms</H>
        <Table
          headers={['Setting', 'Description']}
          rows={[
            ['Voice lobby', 'Joining this voice channel creates a private room.'],
            ['Control panel channel', 'Text channel where the room control panel is published.'],
            ['Rooms log channel', 'Private-room log (if empty — server log is used).'],
            ['Panel thumbnail', 'Optional image in the control-panel embed.'],
          ]}
        />

        <H>Supply runs</H>
        <Table
          headers={['Setting', 'Description']}
          rows={[
            ['Supply ping role', 'Role pinged when a run is created.'],
            ['Supply voice channel', 'Voice channel for the run — shown in the embed.'],
            ['Supply log channel', 'Supply log (if empty — server log is used).'],
            ['Reminder (minutes)', 'Minutes before start to remind participants. Empty = 10, 0 = disable.'],
          ]}
        />

        <Note>
          All dropdowns show real server channels and roles — you do not enter IDs by hand. Before saving, the panel
          checks that each selected channel and role still exists.
        </Note>
      </>
    ),
  },

  // ────────────────────────── MODULES ──────────────────────────
  {
    id: 'levels',
    title: 'Member levels',
    group: 'Modules',
    content: (
      <>
        <H>📈 Levels and XP</H>
        <P>
          Members earn XP from text chat and voice activity, level up, and receive reward roles. The module is{' '}
          <strong>off by default</strong> — enable it with the toggle in Member levels.
        </P>

        <H3>Text message XP</H3>
        <UL>
          <li>Each message awards <strong>15–25 XP</strong>, at most once per minute.</li>
          <li>Only in target channels (whitelist); you can also set ignored channels and roles.</li>
          <li>XP multiplier is configurable (100% = base values).</li>
        </UL>

        <H3>Voice XP</H3>
        <P>XP and voice time go only to <strong>active</strong> members:</P>
        <UL>
          <li>mic on (not muted) and deafen off;</li>
          <li>not bots;</li>
          <li>and only when the channel has <strong>at least two active</strong> members.</li>
        </UL>
        <P>
          XP stacks: while three are active, each gets triple XP; if one leaves, the remaining get double - accumulated
          XP is not lost. Per-minute formula: <Code>base × actives × multiplier</Code>. Base XP per minute is
          configurable (1–100, default 6); “max members” caps the multiplier so a crowd cannot farm XP. You can also set{' '}
          <strong>per-member multipliers</strong> (0–1000%, 100 = normal rate, 0 = no voice XP). Accumulated XP and
          time are written to the ranking <strong>when the voice session ends</strong> (leave or channel change).
        </P>

        <H3>Levels and rewards</H3>
        <UL>
          <li>Level curve rises with level (higher levels cost more); cap is 999.</li>
          <li>
            <strong>Level rewards:</strong> roles tied to each level - granted automatically on reach.
          </li>
          <li>
            <strong>Voice-time rewards:</strong> a separate track - roles for total talked time (e.g. “2 weeks in
            voice”).
          </li>
          <li>Resetting a member&apos;s ranking also removes reward roles automatically.</li>
        </UL>

        <H3>Level-up notification</H3>
        <P>
          Customizable template with placeholders <Code>{'{{member}}'}</Code>, <Code>{'{{level}}'}</Code>,{' '}
          <Code>{'{{roles_added}}'}</Code>; publish channel and auto-delete after N seconds.
        </P>

        <H3>Rank card and leaderboard</H3>
        <UL>
          <li>
            The <Code>/rank</Code> (<Code>/ранг</Code>) command generates a PNG card: avatar, level, progress to next
            level, rank place, voice time. Card background is configurable — upload your own image in the panel.
          </li>
          <li>
            The leaderboard is in the panel and on the public{' '}
            <Code>/leaderboard/&lt;server ID&gt;</Code> page (can be disabled; each server has its own
            link).
          </li>
          <li>
            The Members tab lets you view, edit, or reset any member&apos;s XP, or reset the whole server ranking.
          </li>
        </UL>

        <H3>/xp and /leaders commands</H3>
        <P>
          Both commands work only while Member levels is enabled — otherwise they reply that the level system is
          disabled.
        </P>
        <UL>
          <li>
            <Code>/xp add member amount</Code> - add (or subtract with a negative number) XP; result never goes below
            zero.
          </li>
          <li><Code>/xp set member amount</Code> - set exact XP.</li>
          <li><Code>/xp clear member</Code> - zero a member&apos;s XP (also removes reward roles).</li>
          <li>
            <Code>/leaders</Code> - interactive leaderboard in Discord (up to 1000 members, 10 per page). Sort buttons:{' '}
            <strong>🏆 XP</strong> / <strong>🗣️ Voice</strong>; pagination «‹ › »; close - ✕. Each row shows @mention
            (nickname), level, XP, and voice time as H:MM:SS. Available to everyone.
          </li>
        </UL>
      </>
    ),
  },
  {
    id: 'serverlog',
    title: 'Logging',
    group: 'Modules',
    content: (
      <>
        <H>🧾 Full logging</H>
        <P>
          The module writes all server events to Discord channels. Each event type is toggled separately and can post
          to its own channel — Logging in the panel.
        </P>
        <H3>Unified embed style</H3>
        <UL>
          <li>Colored left bar by event category (join - green, leave - yellow, roles/moderation - blue, voice - teal, etc.).</li>
          <li>Large member avatar on the right (thumbnail) and footer “Member ID: &lt;id&gt;”, which Discord pairs with the event time via a dot.</li>
          <li>
            Role changes and timeouts also show “Changed by” and “Reason” when Discord has a matching audit-log entry -
            including the bot&apos;s own actions (e.g. join auto-role shows the bot and reason “Auto-role on join”) and
            manual moderator changes.
          </li>
        </UL>
        <H3>Tracked events</H3>
        <Table
          headers={['Group', 'Events']}
          rows={[
            ['Messages', 'Edits (before/after), deletions (with content and attachments)'],
            ['Members', 'Join, leave, ban, unban, timeout (applied/removed), nickname change, role changes'],
            [
              'Voice',
              'Join, leave, channel switch (by the member), move/disconnect by admin, mute/deafen by admin',
            ],
            ['Roles', 'Create, delete, update (name, color, permissions)'],
            ['Channels', 'Create, delete, update (name, topic) and separately - permission overwrites'],
            ['Threads', 'Create, delete, update (rename, close/open, lock)'],
            ['Server', 'Guild setting changes (name, icon, verification level, AFK/system channel)'],
            ['Moderation', 'Any moderator slash command (anti-spam, tickets, etc.)'],
            ['Other', 'Server emoji, invite create and delete'],
          ]}
        />
        <Note>
          Bot messages are excluded from message logs - otherwise relay and the bot&apos;s own logs would loop. A
          member muting/deafening themselves is not logged - only server-side (admin) mute/deafen.
        </Note>
        <Warn>
          Distinguishing “member themselves” vs “admin” for voice moves and disconnects is a heuristic based on
          Discord&apos;s audit log (a recent entry in the last few seconds is treated as the cause). Discord does not
          tie those entries to a specific member, only to the channel, so with group moderator actions the actor may be
          wrong. The bot needs the <Code>View Audit Log</Code> permission for this heuristic.
        </Warn>
      </>
    ),
  },
  {
    id: 'voice-stats',
    title: 'Voice statistics',
    group: 'Modules',
    content: (
      <>
        <H>📊 Voice activity analytics</H>
        <P>
          Every voice session (who, which channel, how long, how much of it was active) is stored. Voice stats shows
          for a selected period (day/week/month):
        </P>
        <UL>
          <li>activity by hour of day - when the server is “alive”;</li>
          <li>activity by day of week;</li>
          <li>top voice channels by total time;</li>
          <li>top members by talked time;</li>
          <li>totals: sum time, session count, unique members.</li>
        </UL>
        <P>
          The same data feeds voice XP in the level system: active time is counted once and shared by both modules.
        </P>
      </>
    ),
  },
  {
    id: 'streams',
    title: 'Streams & subscriptions',
    group: 'Modules',
    content: (
      <>
        <H>📺 Stream notifications</H>
        <P>
          The bot watches selected streamers and posts when a stream starts. Subscriptions are managed in the panel: a
          card per streamer with a toggle and delete.
        </P>
        <H3>Platforms</H3>
        <UL>
          <li>
            <strong>Twitch</strong> — stream start notifications. The bot host must have Twitch app credentials
            configured; without them Twitch subscriptions will not announce.
          </li>
          <li>
            <strong>YouTube</strong> — new channel videos; no extra keys needed from you in the panel.
          </li>
        </UL>
        <H3>Subscription settings</H3>
        <UL>
          <li>Publish channel and optional ping role.</li>
          <li>
            Custom message template with placeholders <Code>{'{{channel}}'}</Code>, <Code>{'{{game}}'}</Code>,{' '}
            <Code>{'{{stream}}'}</Code>, <Code>{'{{channel.url}}'}</Code>.
          </li>
          <li>Keywords: only publish streams whose title contains (or does not contain) given words.</li>
          <li>Minimum interval between notifications - anti-spam when a stream restarts.</li>
        </UL>
        <P>The notification is an embed with stream preview, title, category, and link.</P>
      </>
    ),
  },
  {
    id: 'audit',
    title: 'Dashboard audit',
    group: 'Modules',
    content: (
      <>
        <H>🗂️ Moderator action history</H>
        <P>
          Every mutating panel action - saving config, ban, role grant, creating a supply run, changing any module
          setting - is recorded automatically: who, what, when.
        </P>
        <UL>
          <li>Entries with a clear action label, filter by moderator, pagination.</li>
          <li>Only successful changes are stored; simply opening pages is not recorded.</li>
          <li>History stays on your bot host — it is not sent to third-party services.</li>
        </UL>
        <P>
          Audit complements the moderation journal: the journal answers “what happened to a member”; audit answers “who
          on the team did it via the panel”.
        </P>
      </>
    ),
  },

  {
    id: 'moderation',
    title: 'Moderation & protection',
    group: 'Modules',
    content: (
      <>
        <H>🛡️ Anti-spam</H>
        <P>
          Reacts to <strong>mass mentions</strong> — <Code>@everyone</Code>/<Code>@here</Code> or any role mention —
          not to ordinary text flood (that is Automod’s “Repeated text” filter). In a short time window the bot counts
          how many such messages a user sends (with or without attachments). Crossing the limit triggers punishment.
        </P>
        <OL>
          <li>
            The offender gets a Discord timeout for <strong>24 hours</strong>, and their messages from the last{' '}
            <strong>20 minutes</strong> are purged in the background across text channels and active threads.
          </li>
          <li>
            An incident report goes to the spam log channel with <strong>Ban</strong> and <strong>Leave</strong>{' '}
            buttons — a moderator decides next steps in one click (the timeout is already applied).
          </li>
          <li>The incident is written to the moderation journal (visible in the panel).</li>
        </OL>
        <UL>
          <li>
            The spam alert role is only <strong>pinged</strong> in the log — it is never applied to the offender.
          </li>
          <li>Incident buttons keep working after a bot restart.</li>
          <li>Exception channels are excluded from punishment.</li>
          <li>Thresholds and the time window are configured under Moderation → Anti-spam.</li>
        </UL>

        <H>🛑 Spam traps</H>
        <P>
          This is <strong>not</strong> a “timed ban for N minutes” — it is a trap for raiders and self-banning bots.
          Any non-admin message in the spam trap channel instantly bans the author (purging recent message history) and
          unbans them again a couple of seconds later. The report goes to the spam trap log channel (or spam log /
          server log if unset).
        </P>
        <Note>
          If the bot restarts in the narrow window between ban and unban, someone can stay banned briefly — on the next
          startup the bot finds stuck spam-trap bans and unbans them automatically.
        </Note>
        <Warn>
          Do not confuse this with a real timed ban: for that, use <Code>/ban</Code> with a duration — timed bans from
          that command survive a bot restart (see “Moderation commands” below).
        </Warn>

        <H>🔒 Lockdown (server isolation)</H>
        <P>Emergency mode for raids. Enabled with <Code>/antispam</Code> or from the panel (Moderation).</P>
        <OL>
          <li>
            The bot walks all server roles and removes mass-mention permissions; the previous state is saved so it can
            be restored.
          </li>
          <li>Exception roles are left untouched.</li>
          <li>When lockdown ends, permissions are restored exactly as they were.</li>
          <li>Partial errors (e.g. a role above the bot) do not stop the process — they are listed in the report.</li>
        </OL>
        <Warn>
          Do not edit role permissions manually while Lockdown is active: restoring will overwrite those mass-mention
          changes.
        </Warn>

        <H>⚔️ Moderation commands: /ban /kick /mute /unmute /unban /clear</H>
        <P>
          Basic moderation commands in Discord — no dashboard visit required. Each has its own permission (not a shared
          Manage Server), matching Discord itself.
        </P>
        <Table
          headers={['Command', 'Parameters', 'What it does']}
          rows={[
            [
              '/ban',
              'user (pick or ID), reason (optional), time (optional)',
              'Bans a user — even someone not on the server, by ID. Duration as number+unit: 30s, 10m, 2h, 7d. Omit for permanent. Timed bans from this command survive a bot restart.',
            ],
            [
              '/unban',
              'userid, reason (optional)',
              'Unbans by ID. If a timed unban was scheduled, it is cancelled.',
            ],
            [
              '/kick',
              'user, reason (optional)',
              'Kicks a member from the server.',
            ],
            [
              '/mute',
              'user, time (required), reason (optional)',
              'Applies a timeout for number+unit (30s/10m/2h/7d). Discord caps timeouts at 28 days — longer values are rejected.',
            ],
            [
              '/unmute',
              'user, reason (optional)',
              'Removes a timeout early. If the member is not timed out — replies and does nothing.',
            ],
            [
              '/clear',
              'number (1–999)',
              'Deletes the last N messages in the current channel.',
            ],
          ]}
        />
        <P>
          If no reason is given, the log embed omits the Reason field entirely. Discord&apos;s native
          audit log (Server Settings → Audit Log) still records the actor as{' '}
          <Code>reason — command: Name (ID)</Code> when a reason is set, or{' '}
          <Code>command: Name (ID)</Code> when it is not — visible there without the dashboard.
        </P>

        <H>📝 Moderation journal</H>
        <P>
          Moderation shows recent actions: anti-spam punishments, spam traps, manual bans and kicks from the dashboard,
          and <Code>/ban</Code>/<Code>/kick</Code>/<Code>/unban</Code>/<Code>/clear</Code> — who, whom, when, and why.
        </P>
      </>
    ),
  },
  {
    id: 'automod',
    title: 'Automod',
    group: 'Modules',
    content: (
      <>
        <H>🛡️ Configurable message filters</H>
        <P>
          Separate automatic message moderation — independent of anti-spam and Lockdown. Each filter is toggled and
          configured on its own: whether to delete the message, which punishment to apply, and whether to notify the
          offender. The module is <strong>off by default</strong> — Automod section.
        </P>

        <H3>Filters</H3>
        <Table
          headers={['Filter', 'What it catches']}
          rows={[
            ['Links', 'Any links except allowed domains'],
            ['Invites', 'Invites to other Discord servers (your own server can be allowed separately)'],
            ['Scam & phishing links', 'Links/words from a configurable blocklist'],
            ['Bad words', 'Words and phrases from a configurable list'],
            ['Repeated text', 'Flood of identical messages (threshold, 60s window)'],
            ['Caps Lock', 'Messages with a high share of uppercase letters'],
            ['Emoji', 'Too many emoji (custom and unicode) in one message'],
            ['Mentions', 'Too many member/role mentions in one message'],
            ['Zalgo', 'Zalgo characters (combining diacritics)'],
          ]}
        />

        <H3>Per-filter settings</H3>
        <UL>
          <li><strong>Delete violating message</strong> — separate from the punishment.</li>
          <li>
            <strong>Punishment:</strong> none / warn / mute (timeout) / kick / ban.
          </li>
          <li>
            <strong>Punishment duration</strong> (days/hours/minutes, 0 = permanent): for warns — how long the warn
            lasts; for mute/ban — punishment length.
          </li>
          <li>
            <strong>Offender notification:</strong> templated message (<Code>{'{{member}}'}</Code>,{' '}
            <Code>{'{{reason}}'}</Code>) in the current channel or a chosen one.
          </li>
        </UL>
        <Warn>
          Discord timeouts are capped at 28 days — longer values are truncated on apply. An Automod timed ban with
          automatic unban may not lift itself if the bot restarts during the ban window — unban manually with{' '}
          <Code>/unban</Code>. For a timed ban that survives a restart, use <Code>/ban</Code> with a duration.
        </Warn>

        <H>⚠️ Warnings (warns)</H>
        <P>
          A separate warn ledger shared by AutoMod and manual issuance. Each warn stores reason, issuer (moderator or
          filter), date, and duration.
        </P>
        <UL>
          <li>
            Manual: <Code>/warn add</Code>, <Code>/warn list</Code>, <Code>/warn remove</Code>, or “Issue warning” on
            a member card under Members & roles.
          </li>
          <li>
            Manual warn duration is configured separately (AutoMod → Manual warn duration) — filter warns use the
            duration set on that filter.
          </li>
          <li>Removed or expired warns do not count in the active total but remain in history.</li>
        </UL>

        <H3>Escalation</H3>
        <P>
          Configurable thresholds “active warn count → action” (mute/kick/ban with their own duration). When a new warn
          brings the active count exactly to a threshold, that action runs automatically once.
        </P>
      </>
    ),
  },
  {
    id: 'tickets',
    title: 'Tickets & feedback',
    group: 'Modules',
    content: (
      <>
        <H>🎫 CTD tickets (Contact The Developer)</H>
        <Note>
          Main-server feature. CTD tickets and <Code>/ctd_setup</Code> are only available on the main server; settings
          live under “CTD tickets”, visible in the dashboard only when the main server is selected.
        </Note>
        <H3>Setup</H3>
        <OL>
          <li>Set the support role and panel channel under CTD tickets (main server only).</li>
          <li>Run <Code>/ctd_setup</Code> in the support channel — the bot posts a panel with “Create Ticket”.</li>
        </OL>
        <H3>How it works</H3>
        <UL>
          <li>The user clicks the button — a <strong>private thread</strong> is created.</li>
          <li>The ticket author and all support-role holders are invited. Other members cannot see the thread.</li>
          <li>A user cannot open a second ticket while the first is open.</li>
          <li>Support can close with “Close Ticket” — the thread is archived and locked, and a report goes to the log.</li>
        </UL>
        <H3>Smart auto-close</H3>
        <UL>
          <li>48 hours with no messages — the bot posts an inactivity warning.</li>
          <li>Another 24 hours of silence — the ticket is closed and archived automatically.</li>
        </UL>

        <H>💬 Feedback</H>
        <P>
          Structured submissions: complaints, suggestions, appeals — any categories you configure.
        </P>
        <H3>Categories</H3>
        <UL>
          <li>Created and edited in the dashboard: name, description, emoji, publish channel, form fields.</li>
          <li>The bot posts a panel with a category menu — the user picks one and fills a modal form.</li>
        </UL>
        <H3>Case lifecycle</H3>
        <OL>
          <li>The case gets a number and “Under review” status.</li>
          <li>A moderator accepts or rejects it in the dashboard (or via Discord buttons).</li>
          <li>The decision is recorded: who reviewed and when; status is published on the public case message.</li>
          <li>Full case history is under Feedback & tickets, including the member card.</li>
        </OL>
      </>
    ),
  },
  {
    id: 'engagement',
    title: 'Welcomes, invites & roles',
    group: 'Modules',
    content: (
      <>
        <H>👋 Welcomes</H>
        <UL>
          <li>
            <strong>Public welcome:</strong> message in the welcome channel mentioning the newcomer and
            member count. Toggle under Server entry.
          </li>
          <li>
            <strong>Goodbye:</strong> on leave, the bot can post to a channel (separate “Send goodbye to channel”
            toggle on the same tab).
          </li>
          <li>
            <strong>DM guide:</strong> a personal onboarding DM with links to announcements, rules, roles, and LFG
            channels, plus tips for joining the community. Separate toggle.
          </li>
          <li>
            <strong>DM log:</strong> the log channel notes whether the DM was delivered (users may have DMs closed).
          </li>
        </UL>

        <H>📥 Invite stats</H>
        <P>
          The bot tracks server invites and, on join, resolves whose link was used. Per inviter: joins, leaves, and
          total invites. Events post to the invite log channel, and stats appear on the member card. On leave, the
          inviter gets a leave counted.
        </P>

        <H>🤖 Auto-roles</H>
        <P>
          Under Server entry, pick one or more roles — every new member receives them automatically on join.
        </P>

        <H>📌 Sticky roles</H>
        <P>
          On Server entry → Sticky roles: when a member leaves, the bot can remember their roles and restore them when
          they rejoin. Choose which roles to track (or all assignable ones) and which to ignore (never saved or
          restored — useful for mod/admin roles).
        </P>

        <H>🎭 Reaction roles</H>
        <OL>
          <li>Create a message (e.g. via Embed Builder) or use an existing one.</li>
          <li>In the panel, bind “emoji → role” pairs to that message. Duplicate emoji are not allowed.</li>
          <li>The bot adds the reactions itself.</li>
          <li>User adds a reaction — gets the role; removes it — role is removed.</li>
        </OL>
        <P>
          Bindings to deleted messages and channels are cleaned up automatically when the bot starts.
        </P>

        <H>ℹ️ /userinfo command</H>
        <P>
          Member summary: account creation date, server join date, roles, invite stats. Available to moderators with
          Manage Server.
        </P>
      </>
    ),
  },
  {
    id: 'builder',
    title: 'Message builder & buttons',
    group: 'Modules',
    content: (
      <>
        <H>🎨 Embed Builder</H>
        <P>Embed constructor with live preview — what you see in the panel is exactly how it looks in Discord.</P>
        <UL>
          <li>Title, description, bar color (HEX), author with icon, footer.</li>
          <li>Thumbnail and large image.</li>
          <li>Fields with inline toggle.</li>
          <li>Link buttons and interactive buttons attached to the message.</li>
          <li>Channel picker and instant send as the bot; sent messages can be edited again.</li>
        </UL>

        <H>📑 Embed templates</H>
        <P>
          Any built embed can be saved as a named template and loaded later in one click — handy for recurring
          announcements, rules, and guides. Templates are created, applied, and deleted inside Embed Builder.
        </P>

        <H>🔘 Form buttons</H>
        <P>
          Interactive buttons that open a modal form with configurable questions. Answers go to a webhook — useful for
          collecting applications into a dedicated channel.
        </P>
        <UL>
          <li>Only roles allowed in Buttons & embeds settings can create buttons.</li>
          <li>Up to 5 questions per form (Discord limit).</li>
          <li>5-second per-user cooldown — anti-spam for forms.</li>
          <li>Buttons are persistent: they work after a bot restart.</li>
        </UL>
      </>
    ),
  },
  {
    id: 'events',
    title: 'Events & polls',
    group: 'Modules',
    content: (
      <>
        <H>📅 Events</H>
        <OL>
          <li>Create an event in the dashboard: name, description, publish channel, image.</li>
          <li>Optionally set a <strong>reward role</strong> — participants receive it automatically.</li>
          <li>The bot posts an embed with Join / Decline buttons.</li>
          <li>The participant list updates in the panel in real time.</li>
          <li>
            Closing an event disables buttons and marks it Closed; deleting also removes the reward role from all
            participants.
          </li>
        </OL>
        <P>
          Join buttons are persistent and keep working after a bot restart.
        </P>
      </>
    ),
  },
  {
    id: 'brackets',
    title: 'Tournament brackets',
    group: 'Modules',
    content: (
      <>
        <H>🏆 Three tournament formats</H>
        <Table
          headers={['Format', 'Mechanics']}
          rows={[
            ['Single Elimination', 'Classic knockout: one loss and you are out.'],
            ['Double Elimination', 'Winners and losers brackets: first loss drops you to losers; second loss eliminates you. Bracket winners meet in the grand final.'],
            ['Round Robin', 'Round-robin: everyone plays everyone (Berger schedule). Points: win 3, draw 1, loss 0. Up to 20 players.'],
          ]}
        />
        <H>Create and manage</H>
        <OL>
          <li>
            Under Events → Brackets click Create bracket, add participants (manually or from a finished event), and pick a
            format.
          </li>
          <li>
            For knockout formats the bracket is built with correct seeding: with a non-power-of-two count, byes are
            placed by the standard algorithm.
          </li>
          <li>
            An admin clicks the winner — they advance (in Round Robin, 1/X/2 buttons for win/draw).
          </li>
        </OL>
        <H>Public link</H>
        <P>
          Each bracket gets a public URL like <Code>/bracket/&lt;token&gt;</Code>. Share it with players: they see the
          live bracket but cannot edit it. No dashboard login required.
        </P>
      </>
    ),
  },

  {
    id: 'mafia',
    title: 'Mafia',
    group: 'Modules',
    content: (
      <>
        <H>🎭 Role-playing game “Mafia”</H>
        <P>
          Classic social game with roles: Mafia, Townie, Doctor, Sheriff. The module is{' '}
          <strong>off by default</strong> — the master toggle and defaults are under Mafia.
        </P>

        <H3>Starting</H3>
        <UL>
          <li>
            <Code>/mafia-start</Code> (<Code>/мафия-игра</Code>) creates a lobby with a Join button. Any server
            member can start it.
          </li>
          <li>
            Optional command parameters — min/max players (5–99) and three timers (night, discussion, voting). If
            omitted, defaults come from the module settings in the dashboard.
          </li>
          <li>
            The game starts automatically when the max is filled, or early via the lobby&apos;s{' '}
            <strong>“Start now”</strong> button — moderators only (Manage Server).
          </li>
          <li>
            <Code>/mafia-stop</Code> (<Code>/мафия-стоп</Code>) does the opposite: it cancels the lobby or stops a
            running game early — it does <strong>not</strong> start the game sooner. Moderators only.
          </li>
        </UL>

        <H3>Roles</H3>
        <Table
          headers={['Role', 'What it does']}
          rows={[
            ['Mafia', 'At night the mafia team picks a victim; team majority decides.'],
            ['Doctor', 'At night heals one player (including self), blocking a mafia kill.'],
            ['Sheriff', 'At night checks one player — learns whether they are mafia.'],
            ['Townie', 'No night action — only day discussion and voting.'],
          ]}
        />
        <P>Exactly 1 Doctor and 1 Sheriff regardless of player count; Mafia is about 25% of the roster (at least 1).</P>

        <H3>Personal player page</H3>
        <P>
          At start <strong>every</strong> participant gets a personal dashboard link in DMs (no Discord login) — valid
          for the whole match. The page shows: role (and a hint), current phase, countdown, and a live player list —
          alive and eliminated, with revealed roles for the dead. Miss the timer — the action simply does not count.
        </P>

        <H3>Night actions</H3>
        <P>
          Mafia/Doctor/Sheriff get a night-action form on their personal page — pick a living target. Mafia also sees
          their team roster and current votes.
        </P>

        <H3>Day</H3>
        <UL>
          <li>The bot creates a temporary voice channel for discussion.</li>
          <li>
            After discussion, execution voting opens — <strong>every living player</strong> votes on their personal
            page (not in Discord); vote tallies update live there too.
          </li>
          <li>Majority — execution; tie — nobody dies that day.</li>
          <li>
            Once all living players have voted, voting (like night) ends early without waiting for the timer.
          </li>
        </UL>
        <Note>
          The game channel keeps a short “voting started” announcement and a read-only live tally board for spectators
          and moderators — voting itself is not available there.
        </Note>

        <H3>Victory</H3>
        <P>
          Town wins when no mafia remain. Mafia wins when their count equals the other living players. Roles are
          revealed on elimination and in the final summary.
        </P>
      </>
    ),
  },
  {
    id: 'bunker',
    title: 'Bunker',
    group: 'Modules',
    content: (
      <>
        <H>🚪 Role-playing game “Bunker”</H>
        <P>
          A social survival game: each player gets a random character card (profession, health, backpack, etc.) that
          they gradually reveal to others, while the group votes each round who to kick from the bunker until only as
          many seats remain as the shelter holds. The module is <strong>off by default</strong> — master toggle and
          defaults are under Bunker.
        </P>

        <H3>Starting</H3>
        <UL>
          <li>
            <Code>/bunker-start</Code> (<Code>/бункер-игра</Code>) creates a lobby with Join. Any server member can
            start it.
          </li>
          <li>
            Optional parameters — min/max players (<Code>4–20</Code>, module default is usually 4–12), bunker
            capacity (how many survive), two timers (discussion, voting), and unique vs repeating cards. If omitted,
            defaults come from module settings; capacity defaults to half the final player count.
          </li>
          <li>
            The game starts at max fill, or early via the lobby&apos;s <strong>“Start now”</strong> button —
            moderators only (Manage Server).
          </li>
          <li>
            <Code>/bunker-stop</Code> (<Code>/бункер-стоп</Code>) does the opposite: it cancels the lobby or stops a
            running game early — it does <strong>not</strong> start the game sooner. Moderators only.
          </li>
          <li>
            At start the bot randomly picks a catastrophe (what happened outside) and bunker conditions (size, supplies)
            — both shown to everyone in the start announcement and on personal pages.
          </li>
          <li>
            The bot creates a temporary voice channel for discussion (like Mafia) — link in the start announcement and
            DMs; the channel is deleted when the game ends.
          </li>
        </UL>

        <H3>Card dealing: unique or with repeats</H3>
        <P>
          By default card traits (profession, hobby, specific illness/phobia, backpack, large inventory, personality,
          extra facts, special abilities) are dealt <strong>without repeats</strong> in one game — like a physical
          deck: two players cannot get the same profession or special ability. Age, gender, and body type are dice
          rolls over a small set of categories, not cards, so they always may repeat.
        </P>
        <P>
          Mode is toggled with “No repeats (deck)” / “With repeats” in module settings (default for new lobbies) or via
          the <Code>уникальные_карты</Code> parameter on <Code>/bunker-start</Code> for a specific game.
        </P>

        <H3>Character traits</H3>
        <Table
          headers={['Trait', 'What it is']}
          rows={[
            ['Profession', 'Job and experience (novice to expert) — experience gates a pro ability.'],
            ['Age', 'Young / adult / elderly / childfree — narrative flavor, not mechanics.'],
            ['Gender', 'Male or female.'],
            ['Body type', 'Fragile, slim, athletic, sturdy, heavy, or obese — survival narrative.'],
            ['Health', 'One of ~120 diagnoses across 4 severity tiers, or “healthy”.'],
            ['Hobby', 'Interest and skill level.'],
            ['Phobia/fear', 'One of ~120 fears/phobias, or “no phobias”.'],
            ['Backpack', 'One small survival item.'],
            ['Large inventory', 'One bulky item/equipment brought into the bunker.'],
            ['Personality', 'A trait with typical group behavior description.'],
            ['Extra facts', 'A life fact; some cards (“Active (Relationships)”) bind the player to another random participant in the same game.'],
            ['Special abilities', '2 cards per player (swap/steal traits, change bunker, etc.) — played separately from reveals.'],
          ]}
        />

        <H3>Personal player page</H3>
        <P>
          At start <strong>every</strong> participant gets a personal dashboard link in DMs (no Discord login) — valid
          for the whole game. The page shows: full character card (only yours), catastrophe and bunker conditions,
          countdown, live player list with already-revealed traits, and during voting a vote form and live tallies.
        </P>

        <H3>Revealing traits</H3>
        <P>
          In discussion, a player chooses how many traits to open per round — one or all at once, no hard limit. A
          revealed trait is immediately visible to others in their roster; unrevealed traits are owner-only. Eliminated
          players&apos; cards are fully revealed.
        </P>

        <H3>Special abilities</H3>
        <P>
          Each player has 2 special-ability cards (trait swaps, steal, change bunker capacity, revive, etc.), usable
          any time except during voting. The player clicks Use, picks a target and comment — the card is spent, and the
          request is posted in the Discord game channel <strong>and</strong> appears in the dashboard under Active
          games.
        </P>
        <Note>
          Card effects (swaps, steals, revives, etc.) are not applied automatically — too many variants to hard-code
          each of ~80 cards. The host/admin reads the request in the dashboard and manually edits the needed card fields
          — Edit on a player in the game detail opens a form with dropdowns per trait (profession, health, specials,
          etc.), avoiding structural typos — then marks the request Applied. Same idea as the tabletop game, where the
          host applies effects.
        </Note>

        <H3>Elimination voting</H3>
        <UL>
          <li>
            After each discussion, voting opens — <strong>every living player</strong> votes on their personal page for
            who leaves the bunker; tallies update live there.
          </li>
          <li>Majority — elimination; tie among leaders — nobody eliminated that round.</li>
          <li>
            Once all living players have voted, voting ends early without waiting for the timer.
          </li>
        </UL>

        <H3>Victory</H3>
        <P>
          Discussion/voting rounds repeat until living players equal bunker capacity — the remaining are survivors.
          All cards (survivors and eliminated) are revealed in the final announcement.
        </P>
      </>
    ),
  },
  {
    id: 'giveaways',
    title: 'Giveaways',
    group: 'Modules',
    content: (
      <>
        <H>🎉 Prize draws</H>
        <P>
          Classic giveaway: prize, duration, winner count — with automatic pick and optional reroll later. Available to
          anyone with Manage Server — no separate module toggle (same as Supplies/Brackets).
        </P>

        <H3>Starting</H3>
        <UL>
          <li>
            <Code>/giveaway start</Code> with parameters: prize, duration (e.g. <Code>10m</Code>,{' '}
            <Code>2h</Code>, <Code>1d</Code>), and winner count.
          </li>
          <li>
            In the dashboard: Events & polls → Giveaways → New giveaway — same parameters plus publish channel.
          </li>
        </UL>
        <P>
          The bot posts an embed with prize, winner count, live end timer, and a “🎉 Enter” button — pressing again
          removes entry.
        </P>

        <H3>Ending and reroll</H3>
        <UL>
          <li>When the timer ends (or via <Code>/giveaway end</Code>) the bot picks winners at random.</li>
          <li>If there were not enough entrants — a message says the draw ended with no winner.</li>
          <li>
            <Code>/giveaway reroll</Code> (or Reroll in the dashboard) picks new winners — previous winners of the same
            draw are excluded from the reroll pool.
          </li>
        </UL>

        <H3>Reliability</H3>
        <P>
          Giveaways are stored on disk: after a bot restart, active giveaways restore — enter button and timer keep
          working as if nothing happened.
        </P>
      </>
    ),
  },
  {
    id: 'daily-topic',
    title: 'Daily topic',
    group: 'Modules',
    content: (
      <>
        <H>💡 Topic of the day</H>
        <P>
          The bot posts a daily question/topic to a chosen channel so conversation does not die on quiet days. The
          topic is a plain text message from the bot (not an embed). The module is{' '}
          <strong>off by default</strong> — toggle under Daily topic, like Member levels / Family.
        </P>

        <H3>Setup</H3>
        <UL>
          <li>Topic/question list — add, edit, and delete in the dashboard.</li>
          <li>Publish channel.</li>
          <li>
            Publish times (server timezone): each day the bot randomly picks one of the configured times and posts when it hits.
          </li>
        </UL>

        <H3>How a topic is chosen</H3>
        <P>
          Topics cycle without repeats: until the list is exhausted, no topic appears twice. After a full pass the bot
          starts a new cycle (preferring not to repeat the topic that just closed the previous cycle).
        </P>

        <H3>Manual publish</H3>
        <P>
          “Publish now” in the dashboard posts a topic immediately without waiting for the schedule — handy for testing
          or day-to-day manual use. It counts as today&apos;s publish: the schedule will not fire again that day.
        </P>
      </>
    ),
  },

  {
    id: 'fun',
    title: 'Fun',
    group: 'Modules',
    content: (
      <>
        <H>🎉 Fun commands</H>
        <P>
          Light entertainment commands for chat. The module is <strong>off by default</strong> — enable under Fun;
          with the module off both commands reply “Module disabled”.
        </P>

        <H3>🔫 Russian roulette — /russian-roulette</H3>
        <UL>
          <li>
            Solo game: the caller pulls the trigger. The cylinder <strong>does not spin anew</strong>: first chamber is
            1/6, after each click the odds rise (1/5 → 1/4 → …), on the sixth pull a shot is usually guaranteed. With a
            <strong>8%</strong> chance the cylinder loads empty — you can go 6/6 with no shot; after 6/6 it reloads.
            Chamber number is shown in the message.
          </li>
          <li>
            Optional <Code>ставка</Code> parameter (with Economy enabled): survive — bet doubles; die — bet is lost.
            Bet limit is set under Economy.
          </li>
          <li>
            Loser gets a Discord timeout for the configured minutes. Limits: <Code>0–1440</Code> minutes (0 — no
            punishment, only a “death” message; default 1 minute).
          </li>
          <li>
            Per-player cooldown: <Code>0–3600</Code> seconds between attempts (default 30, 0 — no cooldown).
          </li>
          <li>The command only affects the player themselves — you cannot force someone else to play.</li>
        </UL>
        <Note>
          Timeouts need the Timeout Members permission, and timeouts do not apply to administrators — in those cases
          the bot says the loser “got lucky”, without an error.
        </Note>

        <H3>🎰 Emoji roulette — /emoji-roulette</H3>
        <P>
          Picks a random emoji from the server&apos;s custom emoji. If the server has none, the bot uses a built-in
          fallback set. No settings or cooldown.
        </P>

        <H3>✨ Auto-Emoji</H3>
        <P>
          Occasionally the bot reacts to member messages with a random server emoji — in any channel, only on human
          messages (bots and webhooks ignored). Separate toggle inside Fun, off by default.
        </P>
        <UL>
          <li>
            <strong>Chance per message</strong>: <Code>1–100%</Code> (default 4%) — probability of reacting to each
            eligible message.
          </li>
          <li>
            <strong>Minimum interval per channel</strong>: <Code>0–86400</Code> s (default 300) — even if chance hits,
            the bot will not react in the same channel more often than this.
          </li>
          <li>
            <strong>Remove reaction</strong>: <Code>0–3600</Code> s (default 120) — after this the bot removes its own
            reaction so it does not linger; 0 — never remove.
          </li>
        </UL>

        <H3>🟩 Wordle — /wordle</H3>
        <P>
          Russian Wordle in the style of the official Discord app. Each day (resets at midnight in the server timezone) everyone plays one
          shared 5-letter word — 6 guesses. Your letter board is <strong>ephemeral</strong> (only you see it); words are
          entered via “Enter word” through a modal. After each guess the bot posts and updates a live PNG “X is
          playing” card in the channel — avatar and color grid <strong>without letters</strong>, so others cannot
          peek.
        </P>
        <UL>
          <li>
            <Code>/wordle-training</Code> — unlimited games with a random word; no stats and no public cards.
          </li>
          <li>
            <Code>/wordle-stats</Code> — played, win %, current and best streak, guess distribution.
          </li>
          <li>
            <Code>/wordle-top</Code> — server top 10 by wins (ties broken by best streak).
          </li>
          <li>
            <strong>Daily announcement</strong>: at a configured time (server timezone, HH:MM) the bot posts yesterday&apos;s
            results — server streak 🔥, player results (👑 for best), yesterday&apos;s word, summary card, and a Play
            button. Without an announcement channel there is no daily post; live cards go to the channel where the
            command was used.
          </li>
          <li>
            Dictionary: 5-letter nouns (750+ answer words, larger allowed-guess list); “ё” is treated as “е”. Unknown
            words are rejected without spending a guess.
          </li>
        </UL>
      </>
    ),
  },
  {
    id: 'economy',
    title: 'Economy',
    group: 'Modules',
    content: (
      <>
        <H>💰 Server currency</H>
        <P>
          Coins (name and emoji configurable) are granted automatically as a <strong>percentage of earned XP</strong>{' '}
          — separately for text and voice. Economy inherits all Member levels rules: cooldowns, ignored channels and
          roles, multipliers. The module is <strong>off by default</strong>; with ranking off, coins are not granted
          (but commands and the shop still work).
        </P>

        <H3>Commands</H3>
        <UL>
          <li>
            <Code>/balance [member]</Code> (<Code>/баланс</Code>) — balance and top place (reply is only visible to
            you).
          </li>
          <li>
            <Code>/transfer member amount</Code> (<Code>/перевести</Code>) — transfer coins; fee <Code>0–50%</Code>{' '}
            (configurable, default 0, rounded up); transfers can be disabled entirely. Cannot transfer to yourself or
            bots.
          </li>
          <li>
            <Code>/coins-top</Code> (<Code>/монеты-топ</Code>) — top 10 by balance.
          </li>
          <li>
            <Code>/shop</Code> (<Code>/магазин</Code>) — shop list with buy buttons: coins are deducted and the role
            is granted immediately; if the bot cannot grant the role, coins are refunded automatically.
          </li>
          <li>
            <Code>/daily</Code> — daily bonus with no activity required (see below).
          </li>
          <li>
            <Code>/grant-balance member amount</Code> (<Code>/выдать-баланс</Code>) — add or remove coins manually
            (Manage Server). Negative amounts deduct; balance never goes below zero.
          </li>
        </UL>

        <H3>Earning</H3>
        <UL>
          <li>
            <strong>Text XP rate</strong>: <Code>0–1000%</Code> (default 50% — 10 XP yields 5 coins, rounded down).
          </li>
          <li>
            <strong>Voice XP rate</strong>: <Code>0–1000%</Code> (default 50%).
          </li>
        </UL>

        <H3>🎁 Daily bonus — /daily</H3>
        <P>
          Once per calendar day in the server timezone (resets at midnight, same idea as Wordle&apos;s word of the day) — coins with no
          activity. Separate toggle on the Daily bonus card under Economy, on by default.
        </P>
        <UL>
          <li>
            Amount grows <strong>linearly with consecutive-day streak</strong>: base (default 50) + per-day growth
            (default 25) × (streak day − 1), with a plateau on a configurable day (default day 7 = 200, then amount
            stops growing).
          </li>
          <li>
            The streak continues only if the previous claim was <strong>yesterday</strong>; skipping a day or first
            visit resets the streak to 1. Claiming again the same day replies “bonus already claimed” and does not
            touch the balance.
          </li>
        </UL>

        <H3>Russian roulette bets</H3>
        <P>
          The <Code>ставка</Code> parameter on <Code>/russian-roulette</Code>: bet is taken before the shot; survive —
          receive bet ×2 (net +100%), die — bet is lost. Max bet is configurable (<Code>0</Code> — no limit, up to
          1,000,000); bets can be disabled with a separate toggle.
        </P>

        <H3>Shop: roles and rank-card cosmetics</H3>
        <P>
          Up to 25 items (Discord button limit) of three types, edited in the dashboard with an “Item type” selector:
        </P>
        <UL>
          <li>
            <strong>Role</strong> — name, role ID, price (1–10,000,000). Granted on purchase; repurchase blocked if the
            role is already held. The bot needs Manage Roles, and the shop role must be below the bot&apos;s role.
          </li>
          <li>
            <strong>Card frame</strong> — color as <Code>#RRGGBB</Code> (color picker or typed). Changes the ring
            around the avatar on the <Code>/rank</Code> card.
          </li>
          <li>
            <strong>Title</strong> — short text (1–30 chars) shown next to the name on the <Code>/rank</Code> card, in
            the equipped frame color (or default blue).
          </li>
          <li>
            Frames and titles do not grant roles — cosmetics only. After purchase the member equips via{' '}
            <Code>/cosmetics</Code> (<Code>/косметика</Code>) (Frame / Title dropdowns from owned items, plus “No
            frame” / “No title” to clear). Owned items stay forever even if later removed from the shop.
          </li>
          <li>If funds are insufficient for any item, the bot shows the current balance and does not deduct.</li>
        </UL>

        <H3>🎰 Casino — /slots, /coinflip, /blackjack, /casino-top</H3>
        <P>
          A separate Casino page in the dashboard (Activity) with its own toggle; only works with Economy enabled. All
          games share one per-player cooldown — you cannot spam bets by alternating slots, coinflip, and blackjack.
        </P>
        <UL>
          <li>
            <Code>/slots bet</Code> — three reels (🍒 🍋 🔔 ⭐ 💎 7️⃣, common to rare). Three matching symbols pay a large
            multiplier (×3 for 🍒 up to ×50 for 7️⃣, “Jackpot”); two matching — ×1.5 (“Match”); no match — bet lost.
          </li>
          <li>
            <Code>/coinflip bet side</Code> — heads or tails; correct — ×2, wrong — bet lost.
          </li>
          <li>
            <Code>/blackjack bet</Code> — classic blackjack vs the bot dealer with Hit / Stand / Double. Reach 21 or beat
            the dealer without busting (win ×2, natural blackjack ×2.5, push returns the bet). Dealer stands on 17+.
          </li>
          <li>
            <Code>/casino-top</Code> — interactive casino leaderboard: wins or losses, by slots/coinflip, blackjack, or
            combined, with pagination.
          </li>
          <li>
            <strong>Loss roles</strong> — on Casino you can set “loss threshold → role” rules: when a member reaches the
            configured loss count (slots/coinflip, blackjack, or combined), the bot grants the chosen role.
          </li>
          <li>
            <strong>House edge</strong> (<Code>0–50%</Code>, default 5%) — shared for all three games: any “fair” payout
            (bet × multiplier) is reduced by this percent so the server economy does not inflate unboundedly.
          </li>
          <li>
            <strong>Bet limits</strong>: minimum (default 10) and maximum (default 5000, <Code>0</Code> — no limit).
          </li>
          <li>
            <strong>Cooldown</strong>: <Code>0–300</Code> s per player (default 5), shared by all three commands.
          </li>
        </UL>

        <H3>Dashboard management</H3>
        <P>
          Economy section: currency, rates, transfers, bets, shop editor, and balance top with manual adjustment (set
          an exact value for any member). All operations are logged (<Code>economy.db</Code>, <Code>history</Code>{' '}
          table) — you can always see where coins came from.
        </P>

        <H3>Weekly report</H3>
        <P>
          Optional digest posted to a chosen channel every N days (default 7): top earners, net flow, and high-level
          casino activity for that server. Enable and set the channel under Economy. Reports are per-guild and never
          mix balances across servers.
        </P>
      </>
    ),
  },
  {
    id: 'antiraid',
    title: 'Anti-raid',
    group: 'Modules',
    content: (
      <>
        <H>🚨 Auto-lockdown on join surge</H>
        <P>
          The module is <strong>fully off by default</strong> and does nothing until you enable it with the dashboard
          toggle — unrelated to any other bot module. When on, the bot watches new joins: if several “fresh” accounts
          join in a short time, automatic protection fires.
        </P>

        <H3>How a surge is counted</H3>
        <UL>
          <li>
            <strong>Window</strong> (<Code>1–3600</Code> s, default 10) and <strong>threshold</strong> (
            <Code>1–1000</Code> joins, default 5) — if the window reaches the threshold of consecutive joins, it counts
            as a raid.
          </li>
          <li>
            <strong>Minimum account age</strong> (<Code>0–8760</Code> h, default 24) — only joins of accounts younger
            than this are counted; <Code>0</Code> — count all joins. So a normal rush of real people (e.g. after
            advertising) is not confused with a bot raid.
          </li>
          <li>
            The counter is a sliding window: a join outside the window drops out of it rather than resetting everything.
          </li>
        </UL>

        <H3>On trigger</H3>
        <UL>
          <li>
            <strong>Lockdown</strong> (on by default) — same mechanism as manual <Code>/antispam</Code> and the
            Lockdown panel: remove mass-mention permissions from server roles with a restore backup.
          </li>
          <li>
            <strong>Slowmode</strong> (<Code>0–21600</Code> s, off by default) — optionally applied to all text
            channels.
          </li>
          <li>
            <strong>Cooldown</strong> before another trigger (<Code>0–1440</Code> min, default 30) — so the bot does
            not react to every new join while a raid is still ongoing.
          </li>
          <li>
            Each trigger is written to the moderation journal (visible on Moderation) and sent as an embed report to
            the log channel.
          </li>
        </UL>
      </>
    ),
  },
  {
    id: 'verification',
    title: 'Verification',
    group: 'Modules',
    content: (
      <>
        <H>✅ “I am not a bot” panel for newcomers</H>
        <P>
          The module is <strong>fully off by default</strong> and does nothing until you enable it with the dashboard
          toggle — unrelated to any other bot module.
        </P>

        <H3>How to set up</H3>
        <OL>
          <li>Enable the module under Verification in the dashboard.</li>
          <li>
            Set the <strong>Verified</strong> role ID — required; without it the button will not work. Optionally set
            an <strong>Unverified</strong> role ID granted automatically on join.
          </li>
          <li>
            Channel access for Unverified is configured via Discord permissions (Server Settings → Roles) by you — the
            bot only assigns/removes roles and does not manage channel overwrites.
          </li>
          <li>
            Publish the panel with <Code>/verify_setup</Code> in the desired channel — the “I am not a bot” panel is
            persistent and survives a bot restart.
          </li>
        </OL>

        <H3>On click</H3>
        <UL>
          <li>The member receives the Verified role.</li>
          <li>If they had Unverified — it is removed.</li>
          <li>Clicking again when already verified replies “You are already verified”, without errors.</li>
          <li>The event is written to the moderation journal (type “Verification passed”).</li>
        </UL>

        <H3>Rules agreement &amp; re-verification</H3>
        <UL>
          <li>
            Optional <strong>Rules agreement</strong> mode changes the button label to “Accept rules” (server language)
            and uses rules-oriented default panel text. Same Verified role on click.
          </li>
          <li>
            Optional <strong>Re-verification every N days</strong>: after N days the bot removes Verified (and restores
            Unverified if configured). The member must press the button again.
          </li>
        </UL>
      </>
    ),
  },
  {
    id: 'supply',
    title: 'Supply runs',
    group: 'Modules',
    content: (
      <>
        <H>📦 Supply runs</H>
        <P>
          Organize group game events (e.g. supplies in GTA5RP): an initiator announces a run, members sign up with
          buttons, and the bot tracks capacity, time, and reminders.
        </P>

        <H3>Creating a run</H3>
        <OL>
          <li>
            In Discord: <Code>/supply-run</Code> (<Code>/реаки-поставка</Code>) with <Code>против</Code> (target),{' '}
            <Code>лимит</Code> (main roster slots), and <Code>время</Code> as HH:MM in the server timezone. If that time already passed
            today, the run is scheduled for tomorrow.
          </li>
          <li>
            In the panel: Supply runs → New run — same parameters plus publish channel.
          </li>
        </OL>
        <P>
          The bot posts an embed with initiator, target, time (including a live Discord timer), voice channel, and
          participant list, pinging the configured supply role.
        </P>

        <H3>Buttons</H3>
        <Table
          headers={['Button', 'Action']}
          rows={[
            ['Join', 'Sign up for the main roster; if full — to the reserve.'],
            ['Withdraw', 'Leave main or reserve. The freed slot goes to the first person in reserve.'],
            ['Close run', 'End early. Available to the initiator and moderators (Manage Server).'],
          ]}
        />

        <H3>Reserve list</H3>
        <UL>
          <li>When the main roster is full, Join adds to the reserve (with a notice).</li>
          <li>
            If someone withdraws, the first in reserve is moved to main and gets a DM about it.
          </li>
        </UL>

        <H3>Reminder</H3>
        <P>
          A configured number of minutes before start (default 10) the bot posts in the run channel mentioning all
          sign-ups and a link to the voice channel. 0 disables reminders.
        </P>

        <H3>Completion</H3>
        <UL>
          <li>On timer or early: buttons disable, the list is struck through, and a final participant list is posted.</li>
          <li>Each participant of a finished run gets +1 to attendance stats.</li>
          <li>Cancelled runs (via dashboard) do not count toward stats.</li>
        </UL>

        <H3>Reliability and dashboard</H3>
        <UL>
          <li>
            All runs are stored on disk: after a bot restart, active runs restore — buttons work, timers and reminders
            are recreated.
          </li>
          <li>Dashboard: active runs with rosters, history (recent finished), top participants, Finish and Cancel.</li>
          <li>All events (join, withdraw, reserve, promote, close) are logged to the supply log channel.</li>
        </UL>
      </>
    ),
  },
  {
    id: 'family',
    title: 'Family',
    group: 'Modules',
    content: (
      <>
        <H>👨‍👩‍👧 Managing “Family”</H>
        <P>
          Module for a GTA5RP “Family” faction: live role-based roster, joining via application tickets, and a birthday
          list. Like Member levels, it is <strong>off by default</strong> — master toggle and all config live on the
          Family page.
        </P>

        <H3>Roster</H3>
        <UL>
          <li>
            Settings hold an arbitrary list of “group name → role” pairs (e.g. “Leadership” → a specific role).
          </li>
          <li>
            <Code>/roster</Code> (<Code>/список</Code>) posts a live message listing members per role; it updates automatically (with debounce)
            on role grant/remove and member leave.
          </li>
          <li>Dashboard Roster tab — preview of the current composition per role.</li>
        </UL>

        <H3>Join applications</H3>
        <OL>
          <li>A member opens an application via a button in the applications channel and fills a two-step form (modals).</li>
          <li>The bot creates a private thread with the form embed and pings team/ticket-manager roles.</li>
          <li>
            <strong>Accept</strong> / <strong>Deny</strong> / <strong>Close</strong> — grant or remove configured
            roles, archive the thread, and write the outcome to the log channel.
          </li>
        </OL>
        <P>
          Dashboard Applications tab: ticket list with status filter (open / accepted / denied / closed) and the same
          decision buttons as in Discord — both paths share one logic.
        </P>

        <H3>Birthdays</H3>
        <UL>
          <li>
            <Code>/birthday-add</Code>, <Code>/birthday-set</Code>, <Code>/birthday-remove</Code> (
            <Code>/добавить-др</Code>, <Code>/установить-др</Code>, <Code>/удалить-др</Code>) — a member sets a date
            (day and month, no year).
          </li>
          <li>A live upcoming-birthdays message updates on every change.</li>
          <li>Every day at midnight in the server timezone the bot congratulates birthday people in the configured channel.</li>
          <li>Dashboard Birthdays tab: search a member, add or remove a date for any player.</li>
        </UL>
      </>
    ),
  },

  {
    id: 'voice',
    title: 'Private voice rooms',
    group: 'Modules',
    content: (
      <>
        <H>🔊 How a room is created</H>
        <OL>
          <li>A member joins the voice lobby.</li>
          <li>
            The bot instantly creates a “Room • Name” voice channel in the same category and moves the member there.
          </li>
          <li>The creator becomes owner with extended permissions inside their channel.</li>
          <li>One user may have only one room: joining the lobby again recreates it.</li>
          <li>When the room empties — it is deleted automatically.</li>
        </OL>

        <H>Control panel</H>
        <P>
          In the control panel channel the bot posts a panel with buttons. Only the owner can use them while
          in their room:
        </P>
        <Table
          headers={['Button', 'Action']}
          rows={[
            ['Open', 'Allow everyone on the server to connect.'],
            ['Close', 'Deny connect for everyone (channel stays visible).'],
            ['Allow join', 'Grant access to a specific member (user select).'],
            ['Deny join', 'Block a specific member; if they are in the room — disconnect them.'],
            ['Rename', 'Change the room name (modal, up to 96 characters).'],
            ['Limit', 'Set user limit 0–99 (0 = unlimited).'],
            ['Transfer', 'Transfer ownership to another member currently in the room.'],
            ['Kick', 'Disconnect a member from the room.'],
            ['Mute all', 'Mute everyone except the owner.'],
            ['Unmute all', 'Remove mute from everyone.'],
          ]}
        />

        <H>Rules and limits</H>
        <UL>
          <li>You cannot grant access to bots or block yourself.</li>
          <li>
            <strong>Hiding the channel is forbidden:</strong> if the owner manually removes @everyone View Channel, the
            bot restores visibility within a few seconds (while keeping connect closed) and DMs the owner. Individual
            access grants are not reset.
          </li>
          <li>
            All actions — create, rename, access, transfer, kicks, and rejected attempts to control someone else&apos;s
            room — are logged to the rooms log channel.
          </li>
        </UL>

        <H>Reliability</H>
        <UL>
          <li>
            After a bot restart, rooms come back: owner permissions, individual access, names, and limits are restored;
            orphaned records are cleaned up.
          </li>
          <li>
            In the panel (Private voice rooms) you see all active rooms — owner, status, member count. A moderator can
            force-delete a room or republish the control panel.
          </li>
        </UL>
      </>
    ),
  },
  {
    id: 'news',
    title: 'News relay',
    group: 'Modules',
    content: (
      <>
        <H>📰 Purpose</H>
        <Note>
          Main-server feature. News relay is available only to super-admins; the source can be any server, but
          publishing goes only to main-server channels.
        </Note>
        <P>
          The module automatically forwards messages from selected bots on a source server into main-server channels.
          Typical case: on a third-party server, bots post game news (Valorant, Dota, CS, etc.) — Cheterin mirrors them
          into themed channels on the main server.
        </P>

        <H>What is forwarded</H>
        <UL>
          <li>Message text.</li>
          <li>All attachments (images, files) — downloaded and re-uploaded.</li>
          <li>All embeds — each sent as a separate message.</li>
        </UL>

        <H>Forwarding conditions</H>
        <P>A message is relayed only if all of these hold:</P>
        <OL>
          <li>Relay is enabled (dashboard toggle).</li>
          <li>The author is one of the listed source bots.</li>
          <li>The message was sent on the source server (configured guild ID).</li>
          <li>The message channel is in the routes list.</li>
        </OL>
        <Note>
          The bot must be on both servers: on the source to read messages, on the destination to publish.
        </Note>

        <H>Dashboard setup</H>
        <UL>
          <li>Source server ID and comma-separated source bot IDs.</li>
          <li>
            Routes: source channel ID → destination channel (picked from a list) + optional label. One source channel
            cannot map to two destinations.
          </li>
          <li>Log channel: relay events and errors. Messages from the log channel are never relayed (loop protection).</li>
        </UL>
        <P>Changes apply instantly — no bot restart needed.</P>
      </>
    ),
  },
  {
    id: 'members',
    title: 'Members & roles',
    group: 'Modules',
    content: (
      <>
        <H>👥 Member list</H>
        <UL>
          <li>Name search with pagination.</li>
          <li>
            Member card: avatar, registration and join dates, full role list, invite stats, feedback case count.
          </li>
          <li>Grant and remove roles directly from the card.</li>
        </UL>

        <H>🔨 Ban and kick from the dashboard</H>
        <P>
          On the member card: ban (with message-delete depth 0, 1, or 7 days) and kick — with a required reason. The
          action is written to the moderation journal with the moderator&apos;s name.
        </P>

        <H>🎯 Bulk role assign</H>
        <OL>
          <li>Check the members you want (or select all matching a filter).</li>
          <li>Click Grant role and pick a role.</li>
          <li>
            The bot starts a background job that respects Discord API rate limits and grants the role to everyone
            selected, then builds a report: how many succeeded, how many failed.
          </li>
        </OL>
      </>
    ),
  },

  {
    id: 'community-tools',
    title: 'Community tools',
    group: 'Modules',
    content: (
      <>
        <H>🧩 Custom commands, messages, polls, roles &amp; birthdays</H>
        <P>
          These modules live in the active server&apos;s dashboard (some as dedicated pages, some as tabs). Until you
          configure a module, it does nothing. They do not share data with other guilds.
        </P>

        <H3>Custom commands</H3>
        <P>
          Define trigger → reply rules: exact match or “contains”. When a member sends a matching message, the bot
          replies with the configured text. Toggle the module on Custom commands; disable individual rules without
          deleting them. The Preview tab dry-runs a reply without posting to Discord.
        </P>

        <H3>Messages — scheduled</H3>
        <P>
          On Messages → Scheduled: create one-shot or daily posts to a channel. Daily schedules use the{' '}
          <strong>server timezone</strong> from Server settings. Edit content, channel, and schedule from the panel.
          Disabled schedules stay in the list until removed.
        </P>

        <H3>Messages — sticky</H3>
        <P>
          On the same page → Sticky: keep a message at the bottom of a channel. After new chat activity the bot
          re-posts the sticky. Use refresh/test to post immediately without waiting for chat traffic.
        </P>

        <H3>Polls</H3>
        <P>
          The Polls tab on Events &amp; polls (separate from tournament/event posts). Track active and finished polls,
          live vote tallies, and end a poll early from the panel.
        </P>

        <H3>Timed roles</H3>
        <P>
          Grant a role until a set expiry. When time is up the bot removes the role automatically. Cancel early from the
          Timed roles tab on Members &amp; roles.
        </P>

        <H3>Birthdays</H3>
        <P>
          Server-wide birthday calendar (distinct from Family roster birthdays). Members&apos; day/month are stored for
          announcements to a configured channel (at midnight in the server timezone). Family birthdays remain on the
          Family page for roster members.
        </P>

        <H3>Server timezone</H3>
        <P>
          Under Server settings: choose the timezone used for daily schedules, Wordle day reset, weekly economy
          reports, birthday announcements, supply run times, and voice-statistics hour buckets. It is not a fixed
          “Moscow time” — set what your community uses.
        </P>

        <H3>Setup health</H3>
        <P>
          Home and Server settings show whether the bot has critical Discord permissions on this server (send messages,
          manage roles, and so on). Fix missing items in Discord’s role/channel permissions for the bot.
        </P>

        <H3>Owner alerts</H3>
        <P>
          On Server settings: optional DM and/or channel alerts when the bot lacks critical permissions, mass bans spike,
          or a module errors repeatedly. Thresholds are configurable per server.
        </P>

        <H3>Test sends</H3>
        <P>
          Several modules include a safe test action: welcome channel/DM preview, sticky refresh, and streams test
          announce — so you can verify setup without waiting for a real event.
        </P>
      </>
    ),
  },

  // ────────────────────────── REFERENCE ──────────────────────────
  {
    id: 'commands',
    title: 'Command list',
    group: 'Reference',
    content: (
      <>
        <P>
          Cheterin is designed to minimize chat commands — almost everything is done in the dashboard. Full bot slash
          command list:
        </P>
        <Table
          headers={['Command', 'Description', 'Permissions']}
          rows={[
            [
              '/ctd_setup',
              'Deploy the CTD ticket creation panel in the current channel.',
              'Manage Server',
            ],
            [
              '/antispam',
              'Toggle anti-spam mode (Lockdown): remove mass-mention permissions from roles with backup and restore.',
              'Manage Server',
            ],
            [
              '/userinfo',
              'Detailed member summary: registration and join dates, roles, invite stats.',
              'Manage Server',
            ],
            [
              '/supply-run',
              'Create a supply run: target, participant limit, time HH:MM (server timezone). Join buttons, reserve, reminder.',
              'Everyone',
            ],
            [
              '/rank',
              'Rank card (yours or another member): level, progress, top place, voice time.',
              'Everyone',
            ],
            [
              '/warn add | list | remove',
              'Warn a member, list their warns, or remove by ID.',
              'Manage Server',
            ],
            [
              '/ban',
              'Ban a user (by ID even if they are not on the server) with reason and duration (10m/2h/7d — empty means permanent). Timed unban survives bot restart.',
              'Ban Members',
            ],
            [
              '/unban',
              'Unban a user by ID with a reason.',
              'Ban Members',
            ],
            [
              '/kick',
              'Kick a member with a reason.',
              'Kick Members',
            ],
            [
              '/mute',
              'Timeout for a duration (10m/2h/7d, max 28 days — Discord limit).',
              'Timeout Members',
            ],
            [
              '/unmute',
              'Remove a timeout early.',
              'Timeout Members',
            ],
            [
              '/clear',
              'Delete 1 to 999 recent messages in the current channel.',
              'Manage Messages',
            ],
            [
              '/xp add | set | clear',
              'Change a member’s XP: add/subtract, set exact value, or clear. Only when Member levels is enabled.',
              'Manage Server',
            ],
            [
              '/leaders',
              'Interactive leaderboard (up to 1000 members, 10 per page). Sort by XP or Voice, pagination «‹ › », close ✕. Only when Member levels is enabled.',
              'Everyone',
            ],
            [
              '/mafia-start, /mafia-stop',
              'Create a Mafia lobby / cancel the lobby or stop the running game (does not start it early; moderators only).',
              'Everyone / Manage Server',
            ],
            [
              '/bunker-start, /bunker-stop',
              'Create a Bunker lobby / cancel the lobby or stop the running game (does not start it early; moderators only).',
              'Everyone / Manage Server',
            ],
            [
              '/giveaway start | end | reroll',
              'Start a giveaway, end early, or reroll winners.',
              'Manage Server',
            ],
            [
              '/russian-roulette',
              'Pull the trigger: cylinder does not respin; odds rise (1/6 → … → 1/1); 8% empty cylinder (6/6 with no shot). Loser gets a timeout. Optional coin bets: survive — double.',
              'Everyone',
            ],
            [
              '/emoji-roulette',
              'Random emoji from the server’s custom emoji.',
              'Everyone',
            ],
            [
              '/wordle',
              'Russian Wordle: shared 5-letter word of the day, 6 guesses. Board is only visible to the player; the channel gets a color card without letters.',
              'Everyone',
            ],
            [
              '/wordle-training',
              'Practice Wordle with a random word — unlimited and no stats.',
              'Everyone',
            ],
            [
              '/wordle-stats, /wordle-top',
              'Personal stats (streaks, guess distribution) and server player top.',
              'Everyone',
            ],
            [
              '/balance, /coins-top',
              'Server currency balance (yours or another’s) and top 10 richest. Requires Economy enabled.',
              'Everyone',
            ],
            [
              '/transfer',
              'Transfer coins to a member (fee configurable; transfers can be disabled).',
              'Everyone',
            ],
            [
              '/grant-balance',
              'Add or remove coins manually (negative amount deducts). Balance never goes below zero.',
              'Manage Server',
            ],
            [
              '/shop',
              'Role shop for coins: buy with a button, automatic refund if role grant fails.',
              'Everyone',
            ],
            [
              '/slots',
              'Three reels for a coin bet: matches pay (up to x50 jackpot). Requires Economy and Casino enabled.',
              'Everyone',
            ],
            [
              '/coinflip',
              'Heads/tails coin bet: correct side pays x2 (minus house edge).',
              'Everyone',
            ],
            [
              '/blackjack',
              'Blackjack vs the dealer for a coin bet: Hit/Stand/Double; win x2, natural blackjack x2.5.',
              'Everyone',
            ],
            [
              '/casino-top',
              'Interactive casino leaderboard: wins/losses for slots and coinflip, blackjack, or combined.',
              'Everyone',
            ],
            [
              '/daily',
              'Daily coin bonus with no activity: amount grows with consecutive-day streak; skipping a day resets it.',
              'Everyone',
            ],
            [
              '/cosmetics',
              'Equip a shop-bought rank-card frame and/or title (dropdowns, applies immediately).',
              'Everyone',
            ],
            [
              '/verify_setup',
              'Publish a verification panel with “I am not a bot” in the current channel. Requires Verification enabled and a configured role.',
              'Manage Server',
            ],
          ]}
        />
        <Note>
          By default commands appear on each server soon after the bot starts. On very large deployments they may take
          longer to show up in Discord — wait a bit or re-open the server app.
        </Note>
      </>
    ),
  },
  {
    id: 'faq',
    title: 'FAQ & troubleshooting',
    group: 'Reference',
    content: (
      <>
        <H>Sign-in and access</H>
        <H3>I signed in with Discord but do not see my server / see “Access denied”</H3>
        <P>
          The picker only shows servers where you have Manage Server or Administrator and where the bot is installed. If
          the server is missing — add the bot via Add bot; if you lack permissions — ask the owner for Manage Server.
        </P>
        <H3>After signing in I am sent back to the login page</H3>
        <P>
          Check that cookies are allowed for the dashboard domain — the session is stored in an encrypted cookie.
        </P>

        <H>Modules</H>
        <H3>The private rooms panel does not appear</H3>
        <P>
          Make sure the voice lobby and control panel channel are set under Private voice rooms, then click Publish
          panel.
        </P>
        <H3>A room is not created when joining the lobby</H3>
        <UL>
          <li>Confirm the lobby channel is a voice channel and matches the setting.</li>
          <li>The bot needs Manage Channels and Move Members in the lobby category.</li>
        </UL>
        <H3>The supply reminder did not arrive</H3>
        <UL>
          <li>Check the reminder minutes setting — 0 disables reminders.</li>
          <li>A reminder is sent only if the run has at least one participant.</li>
          <li>If the run was created less than N minutes before start, the reminder stage is skipped.</li>
        </UL>
        <H3>Relay does not forward messages</H3>
        <UL>
          <li>Confirm the Relay enabled toggle is on.</li>
          <li>Check that source server ID and bot IDs are correct (IDs, not names).</li>
          <li>The bot must be on the source server and able to see the source channel.</li>
          <li>Check the relay log channel — send errors are posted there.</li>
        </UL>
        <H3>A reaction role is not granted</H3>
        <UL>
          <li>The bot’s role must be above the granted role in the hierarchy.</li>
          <li>Confirm the message and channel still exist — bindings to deleted messages are cleaned up.</li>
        </UL>
        <H3>XP is not granted</H3>
        <UL>
          <li>Confirm the module is enabled with the master toggle under Member levels.</li>
          <li>Text XP only works in target channels — the list must not be empty.</li>
          <li>Voice XP requires at least two active members (mic + audio on) and is written to the ranking only after leaving the channel.</li>
          <li>Confirm the member does not have an ignored role.</li>
        </UL>
        <H3>Stream notifications do not arrive</H3>
        <UL>
          <li>For Twitch, the bot host must have Twitch credentials configured — ask the operator if Twitch never fires.</li>
          <li>Confirm the subscription toggle is on and a publish channel is selected.</li>
          <li>Keywords filter by stream title — too strict a filter blocks notifications.</li>
          <li>The minimum interval suppresses repeat notifications — keep that in mind when testing with stream restarts.</li>
        </UL>
        <H3>Logs are not written</H3>
        <P>
          Each event type under Logging is enabled separately, and an enabled type requires a channel. Check that the
          bot can send messages in the chosen channel.
        </P>
        <H3>An Automod timed ban didn&apos;t lift itself after a bot restart</H3>
        <P>
          That can happen: Automod&apos;s timed ban may not auto-unban after a restart during the ban window — use{' '}
          <Code>/unban</Code>. The <Code>/ban</Code> command with a duration is different: those timed bans survive a
          restart.
        </P>

        <H>General</H>
        <H3>What happens on a bot restart?</H3>
        <P>
          Persistent mechanics restore automatically: active supply runs (buttons + timers), private rooms (permissions
          and owners), ticket/event/spam-incident/form buttons. You should not lose data on a normal restart.
        </P>
        <H3>Where does the bot write logs?</H3>
        <P>
          The main channel is the server log under Moderation → Settings (and Logging for event types). Individual
          modules may use their own channels (spam, spam traps, invites, supplies, rooms, relay) when configured;
          otherwise the main one is used.
        </P>
      </>
    ),
  },
]
