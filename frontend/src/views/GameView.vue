<template>
  <div class="game-layout">

    <!-- Command bar -->
    <div class="top-bar">
      <span class="logotype">POLIS</span>
      <span class="city-name">{{ cityName }}</span>
      <span class="spacer"></span>
      <span class="cycle-badge">Cycle {{ cycle }}</span>
      <span v-if="election" class="cycle-badge" :title="`Re-election approval (need ≥ ${election.pass_score})`">
        {{ election.next_in === 0 ? 'Election now' : `Election in ${election.next_in}` }} ·
        approval {{ election.approval > 0 ? '+' : '' }}{{ election.approval }}
      </span>
      <button class="theme-toggle btn-sm" @click="toggleTheme">
        {{ theme === 'light' ? 'black-figure' : 'red-figure' }}
      </button>
      <button class="btn-primary" @click="runCycle" :disabled="busy || gameOver">
        {{ gameOver ? 'Reign ended' : (busy ? 'Running…' : 'Run Cycle') }}
      </button>
      <div class="menu-wrap">
        <button class="btn-subtle btn-sm menu-btn" @click="showMenu = !showMenu" aria-label="Menu">☰</button>
        <div v-if="showMenu" class="menu-pop" @click.self="showMenu = false">
          <button @click="showMenu = false; showSettings = true">Settings</button>
          <button @click="$router.push('/')">Home</button>
        </div>
      </div>
    </div>
    <div class="mdr"></div>

    <LLMSettings v-if="showSettings" @close="showSettings = false" />

    <p v-if="gameOver" class="error-bar" style="background:var(--danger); color:var(--on-danger)">
      The reign has ended — {{ endCauseLabel }}. Start a new game from Home to play again.
    </p>
    <p v-if="error" class="error-bar">{{ error }}</p>

    <!-- Quadrant: left rail (Factions / Projects) + main (Mayor / Events) -->
    <div class="panels">

      <!-- LEFT RAIL -->
      <div class="left-rail">

      <!-- Factions, grouped by domain -->
      <div class="panel rail-panel">
        <div class="panel-title">Factions</div>
        <div class="faction-list">
          <div v-for="d in factionsByDomain" :key="d.id" class="domain-group">
            <div class="domain-header" @click="toggleDomain(d.id)">
              <span class="domain-caret">{{ expandedDomains[d.id] ? '▾' : '▸' }}</span>
              <span class="domain-name">{{ d.name }}</span>
              <span class="domain-count">{{ d.factions.length }}</span>
              <div class="domain-fill-wrap" v-if="d.cap">
                <div class="domain-fill" :style="{ width: domainFillPct(d) + '%' }"></div>
              </div>
              <span class="domain-cap muted">{{ d.cap ? Math.round(d.utilization) + '/' + d.cap : '' }}</span>
            </div>

            <div v-if="expandedDomains[d.id]" class="domain-factions">
              <div v-for="f in d.factions" :key="f.id" class="faction-card">
                <div class="faction-header">
                  <span class="faction-name">{{ f.name }}</span>
                  <span class="muted faction-leader">{{ leaderName(f) }}</span>
                </div>
                <div class="faction-blurb" v-if="f.blurb">{{ f.blurb }}</div>
                <div class="rating-row">
                  <div class="rating-bar-wrap">
                    <div class="rating-bar" :style="{ width: ratingPct(f) + '%', background: ratingColor(f) }"></div>
                  </div>
                  <span class="rating-val">Lv {{ Math.floor(f.rating) }}</span>
                  <span class="rating-sub muted">({{ f.rating.toFixed(1) }})</span>
                </div>
                <div class="trait-list" v-if="f.traits && f.traits.length">
                  <span v-for="t in f.traits.slice(0,4)" :key="t.trait || t" class="trait-tag">{{ t.trait || t }}</span>
                </div>
                <div class="last-action">
                  <span class="la-label">Last</span>
                  <span class="la-text">{{ lastActionFor(f.id) || 'No action yet' }}</span>
                </div>
                <button class="btn-subtle btn-sm audience-btn" @click="openAudience(f.id)">Audience ▸</button>
              </div>
            </div>
          </div>
          <div v-if="!factionList.length" class="muted" style="font-size:0.85rem; padding:0.5rem">
            No faction data yet.
          </div>
        </div>
      </div>
      <!-- /Factions rail-panel -->

      <!-- Projects, grouped by domain -->
      <div class="panel rail-panel">
        <div class="panel-title">Projects</div>
        <div class="project-list">
          <div v-for="g in projectsByDomain" :key="g.id" class="domain-group">
            <div class="domain-header" @click="toggleProjectDomain(g.id)">
              <span class="domain-caret">{{ expandedProjectDomains[g.id] !== false ? '▾' : '▸' }}</span>
              <span class="domain-name">{{ g.name }}</span>
              <span class="domain-count">{{ g.stack ? g.stack.count : 0 }}</span>
            </div>
            <div v-if="expandedProjectDomains[g.id] !== false" class="domain-projects">
              <template v-if="g.stack && g.stack.count > 0">
                <div v-if="poolCount(g.stack) >= 1" class="project-row"
                     @click="selectedProject = g.stack" title="View details">
                  <span class="project-name">{{ g.stack.name }} ×{{ poolCount(g.stack) }}</span>
                </div>
                <div v-if="frontKind(g.stack) === 'building'" class="project-row building"
                     @click="selectedProject = g.stack" title="View details">
                  <span class="project-name">{{ g.stack.name }}</span>
                  <span class="project-pct accent">{{ Math.round(g.stack.progress) }}%</span>
                </div>
                <div v-else-if="frontKind(g.stack) === 'damaged'" class="project-row damaged"
                     @click="selectedProject = g.stack" title="View details">
                  <span class="project-name">{{ g.stack.name }}</span>
                  <span class="project-pct danger">{{ Math.round(g.stack.progress) }}% hp</span>
                </div>
              </template>
              <div v-else class="muted" style="font-size:0.78rem; padding:0.3rem 0.5rem">No projects</div>
            </div>
          </div>
        </div>
      </div>

      </div>
      <!-- /LEFT RAIL -->

      <!-- MAIN: Mayor (top) + Active Events & Chronicle (bottom) -->
      <div class="main-col">

        <div class="mayor-window">
          <div class="mayor-two-col">

            <!-- LEFT: Mayor title · Treasury · Action Points · buttons -->
            <div class="mayor-left">
              <div class="cinzel-title">Mayor &mdash; the Prytanis</div>
              <div class="mayor-section-label">Treasury</div>
              <div v-if="treas" class="mayor-mini">
                <div class="info-row"><span class="muted">Gold</span><span class="accent bold">{{ treas.gold }}</span></div>
                <div class="info-row"><span class="muted">Income</span><span class="green">+{{ treas.income_this_cycle }}</span></div>
                <div class="info-row"><span class="muted">Spent</span><span class="danger">-{{ treas.expenditure_this_cycle }}</span></div>
                <div class="info-row" v-if="treas.debt > 0"><span class="muted">Debt</span><span class="danger">{{ treas.debt }}</span></div>
              </div>
              <div v-else class="muted mayor-stub">—</div>
              <div v-if="mayorData" class="ap-row">
                <span class="mayor-section-label" style="margin:0">Action Points</span>
                <span class="ap-pips">
                  <span v-for="n in mayorData.action_cap" :key="n"
                        :class="['pip', n <= mayorData.action_points ? 'pip-on' : 'pip-off']">&#9670;</span>
                </span>
              </div>
              <div class="mayor-buttons">
                <button class="btn-primary btn-sm" :disabled="!mayorData" @click="showMayorModal = true">Take Action</button>
                <button class="btn-subtle btn-sm" :disabled="!mayorData" @click="openStandaloneAudience">Audience</button>
              </div>
            </div>

            <!-- RIGHT: The People co-header + the seven scales -->
            <div class="mayor-right">
              <div class="cinzel-title">The People<span v-if="pub"> &middot; {{ pub.population.toLocaleString() }}</span></div>
              <div v-if="pub" class="mayor-mini">
                <div class="info-row"><span class="muted">Fed</span><span :class="bandClass(pub.fed_band)">{{ pub.fed_band }}</span></div>
                <div class="info-row"><span class="muted">Mood</span><span :class="bandClass(pub.happy_band)">{{ pub.happy_band }}{{ pub.drunk ? ' · drunk' : '' }}</span></div>
                <div class="info-row"><span class="muted">Health</span><span :class="pub.sickly ? 'danger' : ''">{{ pub.health }}{{ pub.sickly ? ' · sickly' : '' }}</span></div>
                <div class="info-row"><span class="muted">Piety</span><span :class="bandClass(pub.piety_band)">{{ pub.piety_band }}</span></div>
                <div class="info-row"><span class="muted">Unrest</span><span :class="bandClass(pub.unrest_band)">{{ pub.unrest_band }}</span></div>
                <div class="info-row"><span class="muted">Drink</span><span :class="bandClass(pub.consumption_band)">{{ pub.consumption_band }}</span></div>
                <div class="info-row"><span class="muted">Confidence</span><span :class="bandClass(pub.confidence_band)">{{ pub.confidence_band }}</span></div>
              </div>
              <div v-else class="muted mayor-stub">—</div>
            </div>

          </div>
        </div>

        <div class="center-log">
          <div class="events-band">

            <!-- Active Events -->
            <div class="active-col">
              <div class="panel-title">Active</div>
              <div v-if="activeEvents.length" class="active-list">
                <div v-for="ev in activeEvents" :key="ev.id" class="active-card" :class="'kind-' + ev.kind">
                  <span class="active-name">{{ ev.name }}</span>
                  <span class="active-cy muted">{{ ev.cycles_remaining }} cy</span>
                </div>
              </div>
              <div v-else class="muted calm">The city is calm.</div>
            </div>

            <!-- The Chronicle -->
            <div class="chronicle-col">
              <div class="panel-title">The Chronicle</div>
              <div class="log-scroll">
                <div v-for="(ev, i) in recentEvents" :key="i"
                     class="frieze-row" :class="{ dramatic: ev.dramatic }">
                  {{ ev.narrative }}
                </div>
                <div v-if="!recentEvents.length" class="muted" style="padding:0.5rem; font-size:0.85rem">
                  Run a cycle to see deeds.
                </div>
              </div>
            </div>

          </div>
        </div>

      </div>

    </div>
  </div>

  <MayorActionsModal
    v-if="showMayorModal"
    :factions="snapshot?.factions || {}"
    :domains="snapshot?.domains || {}"
    :mayor-data="mayorData"
    :gold="treas?.gold ?? 0"
    @close="showMayorModal = false"
    @acted="onActed"
  />

  <!-- Standalone audience: faction picker -->
  <div v-if="showAudiencePicker" class="modal-overlay" @click.self="showAudiencePicker = false">
    <div class="card picker-box">
      <div class="panel-header">
        <h3>Request audience with…</h3>
        <button class="btn-subtle btn-sm" @click="showAudiencePicker = false">Close</button>
      </div>
      <div class="picker-list">
        <button v-for="f in factionList" :key="f.id" class="picker-row" @click="pickAudience(f.id)">
          <span>{{ f.name }}</span>
          <span class="muted">{{ f.domain_primary }}</span>
        </button>
      </div>
    </div>
  </div>

  <!-- Active-AI required warning (audience_spec v5) -->
  <div v-if="showAiWarning" class="modal-overlay" @click.self="showAiWarning = false">
    <div class="card ai-warning-box">
      <div class="panel-header">
        <h3>Audience unavailable</h3>
        <button class="btn-subtle btn-sm" @click="showAiWarning = false">Close</button>
      </div>
      <p class="ai-warning-text">No active AI is set for this game. Set an AI to hold audiences.</p>
      <div class="ai-warning-actions">
        <button class="btn-primary btn-sm" @click="showAiWarning = false; showSettings = true">Open Settings</button>
        <button class="btn-subtle btn-sm" @click="showAiWarning = false">Close</button>
      </div>
    </div>
  </div>

  <AudienceModal
    v-if="audienceFactionId && audienceFactionObj"
    :faction="audienceFactionObj"
    @close="audienceFactionId = null"
    @acted="onActed"
  />

  <!-- Project details -->
  <div v-if="selectedProject" class="modal-overlay" @click.self="selectedProject = null">
    <div class="card modal-box" style="width:420px; max-width:95vw">
      <div class="panel-header" style="margin-bottom:1rem">
        <h3 style="margin:0">{{ selectedProject.name }}</h3>
        <button class="btn-subtle btn-sm" @click="selectedProject = null">Close</button>
      </div>

      <div v-if="!selectedProject.completed" class="proj-progress">
        <div class="proj-progress-head">
          <span class="muted">Construction</span>
          <span class="accent">{{ Math.round(selectedProject.progress) }}%</span>
        </div>
        <div class="proj-bar"><div class="proj-bar-fill" :style="{ width: Math.round(selectedProject.progress) + '%' }"></div></div>
      </div>
      <div v-else class="proj-progress">
        <div class="proj-progress-head">
          <span class="muted">Health (top)</span>
          <span class="accent">{{ Math.round(selectedProject.progress) }}%</span>
        </div>
        <div class="proj-bar"><div class="proj-bar-fill" :style="{ width: Math.round(selectedProject.progress) + '%' }"></div></div>
      </div>

      <dl class="proj-detail-grid">
        <dt>Built</dt><dd>{{ poolCount(selectedProject) }} standing</dd>
        <dt>Top</dt><dd>{{ frontLabel(selectedProject) }}</dd>
        <dt>Domain</dt><dd>{{ domainName(selectedProject.domain) || '—' }}</dd>
        <dt>Build step</dt><dd>{{ selectedProject.build_step }}% / action</dd>
        <dt>Initiated by</dt><dd>{{ initiatorName(selectedProject.initiated_by) }}</dd>
      </dl>
    </div>
  </div>
</template>

<script>
import { sim, state, treasury as treasuryApi, mayor as mayorApi, projects as projectsApi } from '../api.js'
import { store } from '../store.js'
import MayorActionsModal from '../components/MayorActionsModal.vue'
import AudienceModal from '../components/AudienceModal.vue'
import LLMSettings from '../components/LLMSettings.vue'

const MAX_RATING = 10

export default {
  name: 'GameView',
  components: { MayorActionsModal, AudienceModal, LLMSettings },
  data() {
    return {
      busy: false,
      error: '',
      gameOver: false,
      endCause: '',
      cycle: 0,
      cityName: '',
      snapshot: null,
      logs: [],
      treas: null,
      mayorData: null,
      projectList: [],
      showMayorModal: false,
      showSettings: false,
      selectedProject: null,
      expandedDomains: {},
      expandedProjectDomains: {},
      audienceFactionId: null,
      showAudiencePicker: false,
      llmProfileId: null,
      showAiWarning: false,
      showMenu: false,
      theme: 'dark',
    }
  },
  computed: {
    aiSet() {
      // An audience requires a valid active AI on the run (audience_spec v5).
      return !!this.llmProfileId
    },
    endCauseLabel() {
      return { public_revolt: 'the people rose against you',
               removal_coalition: 'the creditors forced you out',
               population_collapse: 'the city emptied beneath you',
               voted_out: 'the Assembly voted you out' }[this.endCause]
             || 'you were removed from office'
    },
    factionList() {
      if (!this.snapshot?.factions) return []
      return Object.values(this.snapshot.factions)
        .sort((a, b) => a.name.localeCompare(b.name))
    },
    pub() {
      return this.snapshot?.the_public || null
    },
    election() {
      return this.snapshot?.election || null
    },
    factionsByDomain() {
      const factions = this.snapshot?.factions
      if (!factions) return []
      const domains = this.snapshot?.domains || {}
      const groups = {}
      for (const f of Object.values(factions)) {
        const known = domains[f.domain_primary]
        const key = known ? f.domain_primary : 'other'
        if (!groups[key]) {
          groups[key] = {
            id: key,
            name: known ? (known.name || key) : 'Other',
            cap: known?.cap || 0,
            utilization: known?.utilization || 0,
            factions: [],
          }
        }
        groups[key].factions.push(f)
      }
      const arr = Object.values(groups)
      // Domains alphabetical; factions within each domain alphabetical by name.
      arr.sort((a, b) => a.name.localeCompare(b.name))
      arr.forEach(g => g.factions.sort((a, b) => a.name.localeCompare(b.name)))
      return arr
    },
    logsNewestFirst() {
      return [...this.logs].reverse()
    },
    activeEvents() {
      return this.snapshot?.active_events || []
    },
    recentEvents() {
      // Flatten the log newest-first into a frieze of recent deeds (dramatic beats highlighted).
      const out = []
      for (const entry of this.logsNewestFirst) {
        for (const ev of entry.events || []) out.push(ev)
        if (out.length >= 14) break
      }
      return out.slice(0, 14)
    },
    projectsByDomain() {
      const domains = this.snapshot?.domains
      if (!domains) return []
      // projectList is now one base-project stack per domain (projects_spec v6).
      const byDomain = {}
      for (const s of this.projectList) byDomain[s.domain] = s
      // One group per known domain, so empty domains still show.
      const groups = {}
      for (const [id, d] of Object.entries(domains)) {
        groups[id] = { id, name: d.name || id, stack: byDomain[id] || null }
      }
      const arr = Object.values(groups)
      // "Other": a stack whose domain has no matching domain entry
      for (const s of this.projectList) {
        if (!groups[s.domain]) arr.push({ id: 'other:' + s.domain, name: s.name, stack: s })
      }
      // Alphabetical by name, with Public Treasury (civic) pinned to the top.
      arr.sort((a, b) => {
        if (a.id === 'civic') return -1
        if (b.id === 'civic') return 1
        return a.name.localeCompare(b.name)
      })
      return arr
    },
    audienceFactionObj() {
      if (!this.audienceFactionId) return null
      return (this.snapshot?.factions || {})[this.audienceFactionId] || null
    },
  },
  async mounted() {
    await this.refresh()
  },
  methods: {
    async refresh() {
      try {
        const [snap, status, rawLogs] = await Promise.all([
          state.full(store.userId),
          sim.status(store.userId),
          state.logs(store.userId, 200),
        ])
        this.snapshot = snap
        this.cycle = status.current_cycle
        this.cityName = status.city_name || 'Polis'
        this.llmProfileId = status.llm_profile_id || null
        if (status.end_cause || status.status === 'complete') {
          this.gameOver = true
          this.endCause = status.end_cause || ''
        }
        this.logs = rawLogs
        // Mayor/treasury/projects — don't block if missing
        await Promise.allSettled([
          treasuryApi.get(store.userId).then(t => { this.treas = t }),
          mayorApi.get(store.userId).then(m => { this.mayorData = m }),
          projectsApi.list(store.userId).then(p => {
            this.projectList = p
            // Keep an open details modal (a stack) in sync with the refreshed data — match by domain
            if (this.selectedProject) {
              this.selectedProject = p.find(x => x.domain === this.selectedProject.domain) || null
            }
          }),
        ])
      } catch (e) {
        this.error = e.message
      }
    },
    poolCount(stack) {
      // Pristine instances shown as "Name ×N": count if the top is pristine, else count − 1.
      if (!stack) return 0
      const pristine = stack.completed && stack.progress === 100
      return pristine ? stack.count : Math.max(0, stack.count - 1)
    },
    frontKind(stack) {
      // The in-flux top: 'building', 'damaged', or null (pristine / empty — no front row).
      if (!stack || stack.count < 1) return null
      if (!stack.completed) return 'building'
      if (stack.progress < 100) return 'damaged'
      return null
    },
    frontLabel(stack) {
      const kind = this.frontKind(stack)
      if (kind === 'building') return `building ${Math.round(stack.progress)}%`
      if (kind === 'damaged') return `damaged ${Math.round(stack.progress)}% hp`
      return 'all intact'
    },
    domainName(id) {
      return (this.snapshot?.domains || {})[id]?.name || id
    },
    initiatorName(id) {
      if (!id || id === 'mayor') return 'Mayor'
      return (this.snapshot?.factions || {})[id]?.name || id
    },
    async runCycle() {
      this.error = ''
      this.busy = true
      try {
        const res = await sim.step(store.userId)
        if (res && res.game_over) {
          this.gameOver = true
          this.endCause = res.end_cause || ''
        }
        await this.refresh()
      } catch (e) {
        this.error = e.message
      } finally {
        this.busy = false
      }
    },
    async onActed() {
      // Refresh mayor data (AP + rep) and treasury (gold) after an action
      // without a full page reload — gold feeds the actions modal's affordability.
      try {
        this.mayorData = await mayorApi.get(store.userId)
        this.treas = await treasuryApi.get(store.userId)
      } catch { /* non-fatal */ }
    },
    toggleTheme() {
      this.theme = this.theme === 'light' ? 'dark' : 'light'
      document.documentElement.dataset.theme = this.theme === 'light' ? 'light' : ''
    },
    toggleDomain(id) {
      this.expandedDomains[id] = !this.expandedDomains[id]
    },
    toggleProjectDomain(id) {
      // Undefined = expanded, so project groups start open without pre-population.
      this.expandedProjectDomains[id] = this.expandedProjectDomains[id] === false ? true : false
    },
    domainFillPct(d) {
      if (!d.cap) return 0
      return Math.min(100, (d.utilization / d.cap) * 100)
    },
    lastActionFor(factionId) {
      for (const entry of this.logsNewestFirst) {
        const events = entry.events || []
        for (let i = events.length - 1; i >= 0; i--) {
          if (events[i].actor_id === factionId) return events[i].narrative
        }
      }
      return null
    },
    openAudience(factionId) {
      // Opens the audience pre-targeted to this faction. Requires an active AI.
      if (!this.aiSet) { this.showAiWarning = true; return }
      this.audienceFactionId = factionId
    },
    openStandaloneAudience() {
      if (!this.aiSet) { this.showAiWarning = true; return }
      this.showAudiencePicker = true
    },
    pickAudience(factionId) {
      this.showAudiencePicker = false
      this.audienceFactionId = factionId
    },
    ratingPct(f) {
      return Math.min(100, (f.rating / MAX_RATING) * 100)
    },
    ratingColor(f) {
      const pct = this.ratingPct(f)
      if (pct >= 60) return 'var(--accent)'
      if (pct >= 30) return 'var(--accent2)'
      return 'var(--danger)'
    },
    leaderName(f) {
      if (!f.leader) return ''
      return f.leader.name || ''
    },
    bandClass(band) {
      // Colour a scale's band word: oxblood for danger, terracotta for notable, clay otherwise.
      const danger = ['Starving', 'Miserable', 'Plague', 'Godless', 'Boiling', 'Sodden', 'Dry', 'Hostile']
      const notable = ['Hungry', 'Sullen', 'Sickly', 'Lax', 'Agitated', 'Restless', 'Tipsy',
                       'Suspicious', 'Zealous', 'Devout', 'Favorable', 'Beloved', 'Well fed', 'Festive']
      if (danger.includes(band)) return 'danger'
      if (notable.includes(band)) return 'accent'
      return ''
    },
  },
}
</script>

<style scoped>
.game-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

/* Top bar */
.top-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 1rem;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.logotype {
  font-family: 'Cinzel', Georgia, serif;
  font-weight: 600;
  font-size: 1.25rem;
  letter-spacing: 0.34em;
  color: var(--accent-strong);
}
.city-name {
  font-style: italic;
  font-size: 0.9rem;
  color: var(--muted);
}
.cycle-badge {
  font-family: 'Cinzel', Georgia, serif;
  font-size: 0.72rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent-weak);
}
.theme-toggle {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--muted);
  font-size: 0.72rem;
}
.menu-wrap { position: relative; }
.menu-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--accent-strong);
  font-size: 1rem;
  line-height: 1;
  padding: 0.25rem 0.55rem;
}
.menu-pop {
  position: absolute;
  right: 0;
  top: calc(100% + 4px);
  background: var(--surface-raised);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  min-width: 120px;
  z-index: 50;
}
.menu-pop button {
  background: transparent;
  color: var(--text);
  text-align: left;
  border-radius: 0;
  padding: 0.45rem 0.7rem;
}
.menu-pop button:hover { background: var(--glaze-row); }
.spacer { flex: 1; }

.error-bar {
  background: rgba(176, 84, 94, 0.12);
  border-bottom: 1px solid var(--danger);
  color: var(--danger);
  font-size: 0.85rem;
  padding: 0.4rem 1rem;
  flex-shrink: 0;
}

/* Quadrant: left rail (Factions/Projects) + main col (Mayor/Events) */
.panels {
  display: flex;
  flex: 1;
  overflow: hidden;
  gap: 0.5rem;
  padding: 0.5rem;
}
.left-rail {
  width: 244px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-height: 0;
}
.main-col {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

/* Every region is a framed pottery panel */
.panel,
.mayor-window,
.center-log {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.6rem 0.7rem;
  min-height: 0;
}
.rail-panel { flex: 1; }
.mayor-window { flex: 1; }
.center-log  { flex: 1; }

.mayor-window-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.6rem;
}
.mayor-actions-bar { display: flex; gap: 0.5rem; }
.mayor-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}

.panel-title {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.6rem;
  flex-shrink: 0;
}

/* Faction list */
.faction-list {
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

/* Domain groups */
.domain-group { }
.domain-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.4rem;
  cursor: pointer;
  border-radius: var(--radius);
  user-select: none;
}
.domain-header:hover { background: rgba(255,255,255,0.03); }
.domain-caret { font-size: 0.7rem; color: var(--muted); width: 0.8rem; flex-shrink: 0; }
.domain-name {
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.domain-count {
  font-size: 0.68rem;
  color: var(--muted);
  background: var(--border);
  border-radius: 8px;
  padding: 0 0.4rem;
  flex-shrink: 0;
}
.domain-fill-wrap {
  flex: 1;
  height: 4px;
  background: var(--border);
  border-radius: 2px;
  overflow: hidden;
  min-width: 30px;
}
.domain-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
  transition: width 0.3s;
}
.domain-cap { font-size: 0.68rem; flex-shrink: 0; }
.domain-factions {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding: 0.3rem 0 0.4rem 0.6rem;
}

.faction-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.5rem 0.6rem;
}
.faction-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.3rem;
  gap: 0.4rem;
}
.faction-name { font-weight: 600; font-size: 0.85rem; }
.faction-leader { font-size: 0.72rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.faction-blurb { font-size: 0.72rem; color: var(--muted); font-style: italic; margin: 0.15rem 0 0.35rem; line-height: 1.3; }

/* Last action + audience button */
.last-action {
  display: flex;
  gap: 0.35rem;
  margin-top: 0.3rem;
  font-size: 0.72rem;
  line-height: 1.35;
}
.la-label {
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-size: 0.62rem;
  flex-shrink: 0;
  padding-top: 0.05rem;
}
.la-text { color: var(--text); }
.audience-btn { margin-top: 0.4rem; width: 100%; }
.rating-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.25rem;
}
.rating-bar-wrap {
  flex: 1;
  height: 5px;
  background: var(--border);
  border-radius: 3px;
  overflow: hidden;
}
.rating-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s;
}
.rating-val { font-size: 0.75rem; color: var(--muted); width: 28px; text-align: right; flex-shrink: 0; }
.trait-list { display: flex; flex-wrap: wrap; gap: 0.2rem; }
.trait-tag {
  font-size: 0.68rem;
  background: var(--border);
  border-radius: 3px;
  padding: 0.1rem 0.35rem;
  color: var(--muted);
}

/* Event log */
.log-scroll {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.log-cycle { }
.log-cycle-header {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.3rem;
  padding-bottom: 0.2rem;
  border-bottom: 1px solid var(--border);
}
.log-event {
  font-size: 0.82rem;
  padding: 0.2rem 0;
  line-height: 1.4;
  color: var(--text);
}
.log-event.dramatic {
  color: var(--accent2);
}

/* Active Events & Chronicle band */
.events-band {
  display: grid;
  grid-template-columns: 1fr 1.1fr;
  gap: 0.8rem;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
.active-col, .chronicle-col {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}
.active-col { border-right: 1px solid var(--border); padding-right: 0.8rem; }
.active-list { display: flex; flex-direction: column; gap: 0.4rem; overflow-y: auto; }
.active-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  background: var(--glaze-row);
  border-left: 3px solid var(--accent-weak);
  padding: 0.4rem 0.5rem;
  font-size: 0.82rem;
}
.active-card.kind-disaster { border-left-color: var(--danger); }
.active-card.kind-boon     { border-left-color: var(--accent); }
.active-name { font-weight: 500; color: var(--text); }
.active-cy { font-size: 0.72rem; }
.calm { font-style: italic; font-size: 0.82rem; padding: 0.4rem 0; }
.frieze-row {
  font-size: 0.82rem;
  padding: 0.22rem 0;
  line-height: 1.4;
  color: var(--muted);
  border-bottom: 1px solid rgba(58,36,23,0.5);
}
.frieze-row.dramatic { color: var(--text); border-left: 3px solid var(--danger); padding-left: 0.5rem; }

/* Mayor panel */
.mayor-section {
  margin-bottom: 1rem;
}
.mayor-section-label {
  font-family: 'Cinzel', Georgia, serif;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin: 0.4rem 0 0.2rem;
}

/* Mayor command panel (two columns) */
.mayor-two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  overflow: auto;
}
.mayor-left { border-right: 1px solid var(--border); padding-right: 0.9rem; }
.cinzel-title {
  font-family: 'Cinzel', Georgia, serif;
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  color: var(--accent-strong);
  margin-bottom: 0.3rem;
}
.mayor-mini { font-size: 0.82rem; }
.ap-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  border-top: 1px solid var(--border);
  margin-top: 0.4rem;
  padding-top: 0.4rem;
}
.ap-pips { letter-spacing: 2px; font-size: 0.95rem; }
.pip-on  { color: var(--accent-strong); }
.pip-off { color: var(--accent-weak); opacity: 0.5; }
.mayor-buttons { display: flex; gap: 0.5rem; margin-top: 0.6rem; }
.mayor-stub {
  font-size: 0.8rem;
  font-style: italic;
}
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.3rem;
  padding: 0.1rem 0;
}
.bold { font-weight: 700; }
.project-list {
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  padding-right: 0.75rem;     /* keep domain labels clear of the scrollbar */
  scrollbar-gutter: stable;
}
.project-row {
  display: flex;
  justify-content: space-between;
  padding: 0.15rem 0.3rem;
  font-size: 0.8rem;
  cursor: pointer;
  border-radius: var(--radius);
  transition: background 0.12s;
}
.project-row:hover { background: rgba(116, 182, 164, 0.12); }
.project-row.building .project-name { font-weight: 600; }
.project-pct { font-size: 0.8rem; flex-shrink: 0; }

/* Project details modal */
.proj-progress { margin-bottom: 1rem; }
.proj-progress-head {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  margin-bottom: 0.3rem;
}
.proj-bar {
  height: 8px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 999px;
  overflow: hidden;
}
.proj-bar-fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.2s;
}
.proj-detail-grid {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.35rem 1rem;
  margin: 0;
  font-size: 0.85rem;
}
.proj-detail-grid dt { color: var(--muted); }
.proj-detail-grid dd { margin: 0; text-align: right; }

/* Audience faction picker */
.picker-box { width: 360px; max-width: 95vw; max-height: 80vh; display: flex; flex-direction: column; }
.picker-list { overflow-y: auto; display: flex; flex-direction: column; gap: 0.3rem; }
.picker-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.5rem 0.6rem;
  font-size: 0.85rem;
  text-align: left;
  color: var(--text);
}
.picker-row:hover { border-color: var(--accent); background: rgba(116, 182, 164, 0.10); }
.project-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.project-domain { font-size: 0.72rem; }

/* Active-AI required warning */
.ai-warning-box { width: 340px; max-width: 95vw; }
.ai-warning-text { color: var(--text); font-size: 0.88rem; line-height: 1.4; margin: 0.5rem 0 1rem; }
.ai-warning-actions { display: flex; justify-content: flex-end; gap: 0.5rem; }
</style>
