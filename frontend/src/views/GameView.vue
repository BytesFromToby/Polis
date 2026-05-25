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

      <!-- LEFT: Factions -->
      <div class="panel panel-left">
        <div class="panel-title">Factions</div>
        <div class="faction-list">
          <div v-for="f in factionList" :key="f.id" class="faction-card">
            <div class="faction-header">
              <span class="faction-name">{{ f.name }}</span>
              <span class="faction-domain muted">{{ f.domain_primary }}</span>
            </div>
            <div class="rating-row">
              <div class="rating-bar-wrap">
                <div class="rating-bar" :style="{ width: ratingPct(f) + '%', background: ratingColor(f) }"></div>
              </div>
              <span class="rating-val">{{ f.rating.toFixed(1) }}</span>
            </div>
            <div class="faction-meta">
              <span :class="entrenchClass(f.entrench)">E:{{ f.entrench }}</span>
              <span class="muted" style="margin-left:0.5rem">
                {{ leaderName(f) }}
              </span>
            </div>
            <div class="trait-list" v-if="f.traits && f.traits.length">
              <span v-for="t in f.traits.slice(0,4)" :key="t.trait || t" class="trait-tag">{{ t.trait || t }}</span>
            </div>
          </div>
          <div v-if="!factionList.length" class="muted" style="font-size:0.85rem; padding:0.5rem">
            No faction data yet.
          </div>
        </div>
      </div>

      <!-- CENTER: Event log -->
      <div class="panel panel-center">
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

      <!-- RIGHT: Mayor -->
      <div class="panel panel-right">
        <div class="panel-title">Mayor</div>

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

        <!-- Mayor AP + rep -->
        <div class="mayor-section">
          <div class="mayor-section-label" style="display:flex;justify-content:space-between;align-items:center">
            <span>Actions</span>
            <button v-if="mayorData" class="btn-primary btn-sm" @click="showMayorModal = true"
                    style="font-size:0.7rem; padding:0.15rem 0.5rem">
              Act ▸
            </button>
          </div>
          <div v-if="mayorData" style="font-size:0.82rem">
            <div class="info-row">
              <span class="muted">AP</span>
              <span>{{ mayorData.action_points }} / {{ mayorData.action_cap }}</span>
            </div>
            <div v-for="(score, fid) in topReputation" :key="fid" class="info-row">
              <span class="muted" style="max-width:100px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ fid }}</span>
              <span :class="repColor(score)">{{ score > 0 ? '+' : '' }}{{ score }}</span>
            </div>
            <div v-if="Object.keys(mayorData.exemptions).length" style="margin-top:0.3rem;font-size:0.78rem;color:var(--muted)">
              Exempt: {{ Object.keys(mayorData.exemptions).join(', ') }}
            </div>
          </div>
          <div v-else class="muted mayor-stub">—</div>
        </div>

        <!-- Projects -->
        <div class="mayor-section">
          <div class="mayor-section-label">Projects</div>
          <div v-if="activeProjects.length || buildingProjects.length" style="font-size:0.8rem">
            <div v-for="p in activeProjects" :key="p.id" class="project-row">
              <span class="project-name">{{ p.name }}</span>
              <span class="project-domain muted">{{ p.domain }}</span>
            </div>
            <div v-for="p in buildingProjects" :key="p.id" class="project-row building">
              <span class="project-name">{{ p.name }}</span>
              <span class="muted">{{ p.health }}%</span>
            </div>
          </div>
          <div v-else class="muted mayor-stub">No projects.</div>
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
  </div>

  <MayorActionsModal
    v-if="showMayorModal"
    :factions="snapshot?.factions || {}"
    :domains="snapshot?.domains || {}"
    :mayor-data="mayorData"
    @close="showMayorModal = false"
    @acted="onActed"
  />
</template>

<script>
import { sim, state, treasury as treasuryApi, mayor as mayorApi, projects as projectsApi } from '../api.js'
import { store } from '../store.js'
import MayorActionsModal from '../components/MayorActionsModal.vue'
import LLMSettings from '../components/LLMSettings.vue'

const MAX_RATING = 10

export default {
  name: 'GameView',
  components: { MayorActionsModal, LLMSettings },
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
    }
  },
  computed: {
    factionList() {
      if (!this.snapshot?.factions) return []
      return Object.values(this.snapshot.factions)
        .sort((a, b) => b.rating - a.rating)
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
        this.cityName = status.city_name || 'Rivers Point'
        this.logs = rawLogs
        // Mayor/treasury/projects — don't block if missing
        await Promise.allSettled([
          treasuryApi.get(store.userId).then(t => { this.treas = t }),
          mayorApi.get(store.userId).then(m => { this.mayorData = m }),
          projectsApi.list(store.userId).then(p => { this.projectList = p }),
        ])
      } catch (e) {
        this.error = e.message
      }
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
      // Refresh mayor data (AP + rep) after an action without full page reload
      try {
        this.mayorData = await mayorApi.get(store.userId)
      } catch { /* non-fatal */ }
    },
    ratingPct(f) {
      return Math.min(100, (f.rating / MAX_RATING) * 100)
    },
    ratingColor(f) {
      const pct = this.ratingPct(f)
      if (pct >= 60) return 'var(--accent)'
      if (pct >= 30) return '#e2a740'
      return 'var(--danger)'
    },
    entrenchClass(v) {
      if (v >= 60) return 'green'
      if (v >= 30) return ''
      return 'danger'
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
  background: rgba(224, 92, 92, 0.1);
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

.panel-left   { width: 260px; flex-shrink: 0; }
.panel-center { flex: 1; }
.panel-right  { width: 220px; flex-shrink: 0; }

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
  gap: 0.5rem;
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
}
.faction-name { font-weight: 600; font-size: 0.85rem; }
.faction-domain { font-size: 0.72rem; }
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
.faction-meta { font-size: 0.75rem; margin-bottom: 0.25rem; }
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
  color: #e2c97a;
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
.project-row {
  display: flex;
  justify-content: space-between;
  padding: 0.15rem 0;
  font-size: 0.8rem;
}
.project-row.building { opacity: 0.7; }
.project-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.project-domain { font-size: 0.72rem; }
</style>
