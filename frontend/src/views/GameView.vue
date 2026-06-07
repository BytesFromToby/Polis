<template>
  <div class="game-layout">

    <!-- Top bar -->
    <div class="top-bar">
      <button class="btn-primary" @click="runCycle" :disabled="busy">
        {{ busy ? 'Running…' : 'Run Cycle' }}
      </button>
      <span class="city-name">{{ cityName }}</span>
      <span class="cycle-badge">Cycle {{ cycle }}</span>
      <span class="spacer"></span>
      <button class="btn-subtle btn-sm" @click="showSettings = true" style="margin-right:0.5rem">Settings</button>
      <button class="btn-subtle btn-sm" @click="$router.push('/')">← Title</button>
    </div>

    <LLMSettings v-if="showSettings" @close="showSettings = false" />

    <p v-if="error" class="error-bar">{{ error }}</p>

    <!-- Three panels -->
    <div class="panels">

      <!-- LEFT: Factions, grouped by domain -->
      <div class="panel panel-left">
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
              <span class="domain-cap muted">{{ d.cap ? Math.round(d.utilization) + ' / ' + d.cap : '' }}</span>
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

      <!-- CENTER: Mayor window (top) + Event log (bottom) -->
      <div class="panel panel-center">

        <div class="mayor-window">
          <div class="mayor-window-head">
            <span class="panel-title" style="margin:0">Mayor</span>
            <div class="mayor-actions-bar">
              <button class="btn-primary btn-sm" :disabled="!mayorData" @click="openStandaloneAudience">Request Audience ▸</button>
              <button class="btn-subtle btn-sm" :disabled="!mayorData" @click="showMayorModal = true">Actions ▸</button>
            </div>
          </div>

          <div class="mayor-grid">
            <!-- Treasury -->
            <div class="mayor-section">
              <div class="mayor-section-label">Treasury</div>
              <div v-if="treas" style="font-size:0.82rem">
                <div class="info-row"><span class="muted">Gold</span><span class="accent bold">{{ treas.gold }}</span></div>
                <div class="info-row"><span class="muted">Income</span><span class="green">+{{ treas.income_this_cycle }}</span></div>
                <div class="info-row"><span class="muted">Spent</span><span class="danger">-{{ treas.expenditure_this_cycle }}</span></div>
                <div class="info-row" v-if="treas.debt > 0"><span class="muted">Debt</span><span class="danger">{{ treas.debt }}</span></div>
                <div class="info-row" v-if="treas.invested > 0"><span class="muted">Invested</span><span>{{ treas.invested }} ({{ treas.invest_cycles_remaining }}cy)</span></div>
                <div class="info-row"><span class="muted">Max Tax</span><span>{{ (treas.max_tax_rate * 100).toFixed(0) }}%</span></div>
              </div>
              <div v-else class="muted mayor-stub">—</div>
            </div>

            <!-- Standing: AP + reputation -->
            <div class="mayor-section">
              <div class="mayor-section-label">Standing</div>
              <div v-if="mayorData" style="font-size:0.82rem">
                <div class="info-row">
                  <span class="muted">AP</span>
                  <span>{{ mayorData.action_points }} / {{ mayorData.action_cap }}</span>
                </div>
                <div v-for="(score, fid) in topReputation" :key="fid" class="info-row">
                  <span class="muted" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ fid }}</span>
                  <span :class="repColor(score)">{{ score > 0 ? '+' : '' }}{{ score }}</span>
                </div>
                <div v-if="Object.keys(mayorData.exemptions).length" style="margin-top:0.3rem;font-size:0.78rem;color:var(--muted)">
                  Exempt: {{ Object.keys(mayorData.exemptions).join(', ') }}
                </div>
              </div>
              <div v-else class="muted mayor-stub">—</div>
            </div>

            <!-- World -->
            <div class="mayor-section">
              <div class="mayor-section-label">World</div>
              <div v-if="world" style="font-size:0.82rem">
                <div>Chaos: <span class="accent">{{ chaosDisplay }}</span></div>
              </div>
              <div v-else class="muted mayor-stub">—</div>
            </div>
          </div>
        </div>

        <div class="center-log">
          <div class="panel-title">Event Log</div>
          <div class="log-scroll">
            <div v-for="entry in logsNewestFirst" :key="entry.cycle" class="log-cycle">
              <div class="log-cycle-header">Cycle {{ entry.cycle }}</div>
              <div v-for="(ev, i) in entry.events" :key="i"
                   class="log-event"
                   :class="{ dramatic: ev.dramatic }">
                {{ ev.narrative }}
              </div>
              <div v-if="!entry.events.length" class="muted log-event">No events this cycle.</div>
            </div>
            <div v-if="!logs.length" class="muted" style="padding:0.5rem; font-size:0.85rem">
              Run a cycle to see events.
            </div>
          </div>
        </div>

      </div>

      <!-- RIGHT: Projects -->
      <div class="panel panel-right">
        <div class="panel-title">Projects</div>
        <div v-if="projectList.length" class="project-list">
          <!-- In-progress first, with % complete -->
          <div v-for="p in buildingProjects" :key="p.id" class="project-row building"
               @click="selectedProject = p" title="View details">
            <span class="project-name">{{ p.name }}</span>
            <span class="project-pct accent">{{ projectPct(p) }}%</span>
          </div>
          <!-- Then active / other -->
          <div v-for="p in otherProjects" :key="p.id" class="project-row"
               @click="selectedProject = p" title="View details">
            <span class="project-name">{{ p.name }}</span>
            <span class="project-domain muted">{{ p.domain || p.status }}</span>
          </div>
        </div>
        <div v-else class="muted mayor-stub" style="font-size:0.8rem; padding:0.4rem">No projects.</div>
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

      <div v-if="selectedProject.status === 'under_construction'" class="proj-progress">
        <div class="proj-progress-head">
          <span class="muted">Construction</span>
          <span class="accent">{{ projectPct(selectedProject) }}% · {{ selectedProject.build_progress }}/4 units</span>
        </div>
        <div class="proj-bar"><div class="proj-bar-fill" :style="{ width: projectPct(selectedProject) + '%' }"></div></div>
      </div>
      <div v-else class="proj-progress">
        <div class="proj-progress-head">
          <span class="muted">Health</span>
          <span class="accent">{{ selectedProject.health }}%</span>
        </div>
        <div class="proj-bar"><div class="proj-bar-fill" :style="{ width: selectedProject.health + '%' }"></div></div>
      </div>

      <dl class="proj-detail-grid">
        <dt>Status</dt><dd>{{ projectStatusLabel(selectedProject.status) }}</dd>
        <dt>Domain</dt><dd>{{ domainName(selectedProject.domain) || '—' }}</dd>
        <dt>Type</dt><dd>{{ selectedProject.category }}</dd>
        <dt v-if="selectedProject.tax_level">Tax level</dt><dd v-if="selectedProject.tax_level">{{ selectedProject.tax_level }}</dd>
        <dt>Upkeep</dt><dd>{{ selectedProject.maintenance_cost }} gold/cycle</dd>
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
      audienceFactionId: null,
      showAudiencePicker: false,
    }
  },
  computed: {
    factionList() {
      if (!this.snapshot?.factions) return []
      return Object.values(this.snapshot.factions)
        .sort((a, b) => b.rating - a.rating)
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
      arr.forEach(g => g.factions.sort((a, b) => b.rating - a.rating))
      return arr
    },
    world() {
      return this.snapshot?.world || null
    },
    logsNewestFirst() {
      return [...this.logs].reverse()
    },
    chaosDisplay() {
      if (!this.world?.chaos) return '—'
      const entries = Object.entries(this.world.chaos)
      if (!entries.length) return 'none'
      return entries.map(([k, v]) => `${k}:${v.toFixed(1)}`).join(', ')
    },
    topReputation() {
      if (!this.mayorData?.reputation) return {}
      const rep = this.mayorData.reputation
      return Object.fromEntries(
        Object.entries(rep)
          .filter(([, v]) => Math.abs(v) >= 5)
          .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
          .slice(0, 5)
      )
    },
    activeProjects() {
      return this.projectList.filter(p => p.status === 'active')
    },
    buildingProjects() {
      return this.projectList.filter(p => p.status === 'under_construction')
    },
    otherProjects() {
      return this.projectList.filter(p => p.status !== 'under_construction')
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
        this.logs = rawLogs
        // Mayor/treasury/projects — don't block if missing
        await Promise.allSettled([
          treasuryApi.get(store.userId).then(t => { this.treas = t }),
          mayorApi.get(store.userId).then(m => { this.mayorData = m }),
          projectsApi.list(store.userId).then(p => {
            this.projectList = p
            // Keep an open details modal in sync with the refreshed data
            if (this.selectedProject) {
              this.selectedProject = p.find(x => x.id === this.selectedProject.id) || null
            }
          }),
        ])
      } catch (e) {
        this.error = e.message
      }
    },
    projectPct(p) {
      // Under-construction progress is build_progress out of 4 work units.
      return Math.round(((p.build_progress || 0) / 4) * 100)
    },
    projectStatusLabel(status) {
      return ({
        under_construction: 'Under construction',
        active: 'Active',
        damaged: 'Damaged',
        critical: 'Critical',
        destroyed: 'Destroyed',
      })[status] || status
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
        await sim.step(store.userId)
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
    toggleDomain(id) {
      this.expandedDomains[id] = !this.expandedDomains[id]
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
      // Wired in Slice 4 — opens the audience pre-targeted to this faction.
      this.audienceFactionId = factionId
    },
    openStandaloneAudience() {
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
    repColor(score) {
      if (score >= 10) return 'green'
      if (score <= -10) return 'danger'
      return 'muted'
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
.city-name {
  font-weight: 700;
  font-size: 1rem;
  color: var(--accent);
}
.cycle-badge {
  font-size: 0.85rem;
  color: var(--muted);
}
.spacer { flex: 1; }

.error-bar {
  background: rgba(176, 84, 94, 0.12);
  border-bottom: 1px solid var(--danger);
  color: var(--danger);
  font-size: 0.85rem;
  padding: 0.4rem 1rem;
  flex-shrink: 0;
}

/* Panels */
.panels {
  display: flex;
  flex: 1;
  overflow: hidden;
  gap: 0;
}

.panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-right: 1px solid var(--border);
  padding: 0.75rem;
}
.panel:last-child { border-right: none; }

.panel-left   { width: 300px; flex-shrink: 0; }
.panel-center { flex: 1; padding: 0; }
.panel-right  { width: 260px; flex-shrink: 0; }

/* Center column: Mayor window on top, Event Log below */
.panel-center { display: flex; flex-direction: column; gap: 0; }
.mayor-window {
  flex-shrink: 0;
  padding: 0.75rem;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}
.mayor-window-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.6rem;
}
.mayor-actions-bar { display: flex; gap: 0.5rem; }
.mayor-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}
.center-log {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0.75rem;
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

/* Mayor panel */
.mayor-section {
  margin-bottom: 1rem;
}
.mayor-section-label {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.3rem;
}
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
}
.picker-row:hover { border-color: var(--accent); background: rgba(116, 182, 164, 0.10); }
.project-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.project-domain { font-size: 0.72rem; }
</style>
