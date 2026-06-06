<template>
  <div class="page">
    <nav>
      <span class="brand">Polis</span>
      <span class="muted" style="font-size:0.85rem">
        Cycle <strong>{{ status.current_cycle }}</strong>
        <span class="tag" style="margin-left:0.5rem">{{ status.status }}</span>
      </span>
      <span class="spacer"></span>
      <button class="btn-subtle btn-sm" @click="showSettings = true" style="margin-right:0.5rem">Settings</button>
      <button class="btn-subtle btn-sm" @click="$router.push('/home')">← Home</button>
    </nav>

    <LLMSettings v-if="showSettings" @close="showSettings = false" />

    <div class="container" style="padding-top:1rem; flex:1">
      <p v-if="error" class="error-msg" style="margin-bottom:0.75rem">{{ error }}</p>

      <!-- Main split: World panel (left) + Narrative log (right) -->
      <div class="row" style="gap:0.75rem; margin-bottom:0.75rem; align-items:flex-start">

        <!-- LEFT: World panel (city info + sim controls + world state) -->
        <div class="col" style="flex:1">
          <div class="card">

            <!-- City name -->
            <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.4rem">
              <template v-if="!editingName">
                <span style="font-size:1.1rem; font-weight:700; flex:1">
                  {{ status.city_name || 'Unnamed City' }}
                </span>
                <button class="btn-subtle btn-sm" @click="startEditName">Edit</button>
              </template>
              <template v-else>
                <input v-model="editName" style="flex:1; font-size:1rem; font-weight:600"
                       @keyup.enter="saveName" @keyup.escape="cancelEditName"
                       placeholder="City name" />
                <button class="btn-primary btn-sm" @click="saveName" :disabled="savingInfo">Save</button>
                <button class="btn-subtle btn-sm" @click="cancelEditName">Cancel</button>
              </template>
            </div>

            <!-- Description -->
            <div style="margin-bottom:0.75rem; font-size:0.85rem">
              <template v-if="!editingDesc">
                <span class="muted">
                  {{ descTruncated
                  }}<template v-if="descOverflow && !descExpanded">…
                    <button class="btn-subtle btn-sm" style="padding:0 0.3rem; font-size:0.78rem"
                            @click="descExpanded = true">more</button>
                  </template>
                </span>
                <div style="margin-top:0.25rem">
                  <button class="btn-subtle btn-sm" style="font-size:0.78rem"
                          @click="startEditDesc">Edit description</button>
                </div>
              </template>
              <template v-else>
                <textarea v-model="editDesc" rows="3"
                          style="width:100%; resize:vertical; font-size:0.85rem"
                          @keyup.escape="cancelEditDesc"></textarea>
                <div style="display:flex; gap:0.5rem; margin-top:0.3rem">
                  <button class="btn-primary btn-sm" @click="saveDesc" :disabled="savingInfo">Save</button>
                  <button class="btn-subtle btn-sm" @click="cancelEditDesc">Cancel</button>
                </div>
              </template>
            </div>

            <!-- Sim controls -->
            <div style="display:flex; gap:0.5rem; align-items:center; flex-wrap:wrap;
                        padding-top:0.6rem; border-top:1px solid var(--border)">
              <button class="btn-primary" @click="step" :disabled="busy">Step</button>
              <div style="display:flex; gap:0.25rem; align-items:center">
                <button class="btn-subtle" @click="runN" :disabled="busy">Run</button>
                <input v-model.number="runCount" type="number" min="1" max="100"
                       style="width:60px; padding:0.35rem 0.5rem" />
                <span class="muted">cycles</span>
              </div>
              <button class="btn-subtle" @click="pause" :disabled="!busy">Pause</button>
              <span class="spacer"></span>
              <button class="btn-danger btn-sm" @click="confirmReset">Reset</button>
            </div>
            <p v-if="lastRunMsg" class="muted" style="font-size:0.8rem; margin-top:0.5rem">
              {{ lastRunMsg }}
            </p>

            <!-- Domain fill -->
            <div v-if="snapshot && domainFills.length"
                 style="margin-top:0.75rem; padding-top:0.6rem; border-top:1px solid var(--border)">
              <div style="font-size:0.75rem; color:var(--muted); margin-bottom:0.4rem; text-transform:uppercase; letter-spacing:0.05em">Domains</div>
              <div style="display:flex; flex-direction:column; gap:0.3rem">
                <div v-for="d in domainFills" :key="d.id"
                     style="display:flex; align-items:center; gap:0.5rem; font-size:0.8rem">
                  <span style="width:90px; flex-shrink:0; color:var(--muted)">{{ d.name }}</span>
                  <div style="flex:1; height:6px; background:var(--border); border-radius:3px; overflow:hidden">
                    <div :style="{ width: d.pct + '%', background: d.pct >= 90 ? 'var(--danger)' : d.pct >= 60 ? 'var(--accent2)' : 'var(--accent)', height: '100%' }"></div>
                  </div>
                  <span style="width:70px; text-align:right; flex-shrink:0">
                    {{ Math.round(d.utilization) }} / {{ d.cap }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- RIGHT: Narrative log -->
        <div class="col" style="flex:1">
          <div class="card" style="height:100%">
            <div class="panel-header">
              <h3>Narrative Log</h3>
              <button class="btn-subtle btn-sm" @click="fetchLogs">↺</button>
            </div>
            <div style="max-height:260px; overflow-y:auto; display:flex; flex-direction:column; gap:0.5rem">
              <div v-for="entry in logs" :key="entry.cycle">
                <div class="muted" style="font-size:0.7rem; margin-bottom:0.15rem">
                  Cycle {{ entry.cycle }}
                </div>
                <div v-for="(ev, i) in entry.events.filter(e => e.dramatic)" :key="i"
                     style="font-size:0.82rem; padding:0.2rem 0; border-bottom:1px solid var(--border)">
                  {{ ev.narrative }}
                </div>
              </div>
              <div v-if="!logs.length" class="muted" style="font-size:0.85rem">
                No narrative yet.
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Factions panel -->
      <div class="card" style="margin-bottom:0.75rem">
        <div class="panel-header"><h3>Factions</h3></div>
        <table>
          <thead>
            <tr>
              <th>Domain</th><th>Name</th><th>Level</th>
              <th>Health</th><th>Leader</th>
            </tr>
          </thead>
          <tbody v-for="(group, domain) in factionsByDomain" :key="domain">
            <tr class="domain-group-header" @click="toggleDomain(domain)" style="cursor:pointer">
              <td colspan="5">
                <span style="font-size:0.75rem; font-weight:600; text-transform:uppercase;
                             letter-spacing:0.05em; color:var(--accent)">
                  {{ domain }}
                </span>
                <span class="muted" style="font-size:0.75rem; margin-left:0.5rem">
                  {{ group.length }} faction{{ group.length !== 1 ? 's' : '' }}
                </span>
                <span style="float:right; color:var(--muted)">
                  {{ collapsedDomains[domain] ? '▸' : '▾' }}
                </span>
              </td>
            </tr>
            <template v-if="!collapsedDomains[domain]">
              <tr v-for="f in group" :key="f.id">
                <td class="muted"></td>
                <td>{{ f.name }}</td>
                <td>{{ Math.floor(f.rating) }}</td>
                <td>{{ f.health }}</td>
                <td>{{ f.leader?.name || '—' }}</td>
              </tr>
            </template>
          </tbody>
          <tbody v-if="!factionList.length">
            <tr><td colspan="5" class="muted">No factions.</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { sim, state } from '../api.js'
import { store } from '../store.js'
import LLMSettings from '../components/LLMSettings.vue'

const DESC_LIMIT = 100

export default {
  name: 'DashboardView',
  components: { LLMSettings },
  data() {
    return {
      store,
      status: store.simStatus || { current_cycle: 0, status: 'unknown', city_name: '', description: '' },
      snapshot: null,
      logs: [],
      error: '',
      busy: false,
      runCount: 5,
      lastRunMsg: '',
      pollTimer: null,
      collapsedDomains: {},
      // Inline editing: city name
      editingName: false,
      editName: '',
      // Inline editing: description
      editingDesc: false,
      editDesc: '',
      descExpanded: false,
      savingInfo: false,
      showSettings: false,
    }
  },
  computed: {
    descTruncated() {
      const desc = this.status.description || ''
      if (this.descExpanded || desc.length <= DESC_LIMIT) return desc
      return desc.slice(0, DESC_LIMIT)
    },
    descOverflow() {
      return (this.status.description || '').length > DESC_LIMIT
    },
    factionList() {
      if (!this.snapshot) return []
      return Object.values(this.snapshot.factions)
    },
    factionsByDomain() {
      const groups = {}
      for (const f of this.factionList) {
        const d = f.domain_primary || 'Unknown'
        if (!groups[d]) groups[d] = []
        groups[d].push(f)
      }
      return Object.fromEntries(Object.entries(groups).sort())
    },
    domainFills() {
      if (!this.snapshot?.domains) return []
      return Object.values(this.snapshot.domains)
        .filter(d => !d.name.toLowerCase().includes('social'))
        .sort((a, b) => a.name.localeCompare(b.name))
        .map(d => ({
          id: d.id,
          name: d.name,
          cap: d.cap,
          utilization: d.utilization,
          pct: d.cap > 0 ? Math.min(100, Math.round((d.utilization / d.cap) * 100)) : 0,
        }))
    },
  },
  async mounted() {
    await this.refresh()
    this.pollTimer = setInterval(this.pollStatus, 5000)
  },
  beforeUnmount() {
    clearInterval(this.pollTimer)
  },
  methods: {
    async refresh() {
      try {
        const [snap, s] = await Promise.all([
          state.full(store.userId),
          sim.status(store.userId),
        ])
        this.snapshot = snap
        this.status = s
        store.simStatus = s
      } catch (e) {
        this.error = e.message
      }
      await this.fetchLogs()
    },
    async fetchLogs() {
      try {
        const raw = await state.logs(store.userId, 20)
        this.logs = raw.reverse()
      } catch { /* ignore */ }
    },
    async pollStatus() {
      try {
        const s = await sim.status(store.userId)
        this.status = s
        store.simStatus = s
      } catch { /* ignore */ }
    },

    // ── Sim controls ──
    async step() {
      this.error = ''; this.busy = true
      try {
        await sim.step(store.userId)
        await this.refresh()
      } catch (e) {
        this.error = e.message
      } finally {
        this.busy = false
      }
    },
    async runN() {
      this.error = ''; this.lastRunMsg = ''; this.busy = true
      try {
        const res = await sim.run(store.userId, this.runCount)
        this.lastRunMsg = `Ran ${res.cycles_run} cycle(s) to cycle ${res.final_cycle}.`
          + (res.stopped_early ? ` Stopped: ${res.stop_reason}.` : '')
        await this.refresh()
      } catch (e) {
        this.error = e.message
      } finally {
        this.busy = false
      }
    },
    async pause() {
      try { await sim.pause(store.userId) } catch (e) { this.error = e.message }
    },
    async confirmReset() {
      if (!confirm('Reset to cycle 0? All progress will be lost.')) return
      try {
        await sim.reset(store.userId)
        store.simStatus = null
        this.$router.push('/home')
      } catch (e) {
        this.error = e.message
      }
    },

    // ── City name edit ──
    startEditName() {
      this.editName = this.status.city_name || ''
      this.editingName = true
    },
    cancelEditName() {
      this.editingName = false
    },
    async saveName() {
      if (!this.editName.trim()) return
      this.savingInfo = true
      try {
        await sim.patchInfo(store.userId, { city_name: this.editName.trim() })
        this.status = { ...this.status, city_name: this.editName.trim() }
        store.simStatus = this.status
        this.editingName = false
      } catch (e) {
        this.error = e.message
      } finally {
        this.savingInfo = false
      }
    },

    // ── Description edit ──
    startEditDesc() {
      this.editDesc = this.status.description || ''
      this.editingDesc = true
    },
    cancelEditDesc() {
      this.editingDesc = false
    },
    async saveDesc() {
      this.savingInfo = true
      try {
        await sim.patchInfo(store.userId, { description: this.editDesc.trim() })
        this.status = { ...this.status, description: this.editDesc.trim() }
        store.simStatus = this.status
        this.editingDesc = false
        this.descExpanded = false
      } catch (e) {
        this.error = e.message
      } finally {
        this.savingInfo = false
      }
    },

    // ── Domain collapse ──
    toggleDomain(domain) {
      this.collapsedDomains[domain] = !this.collapsedDomains[domain]
    },
  },
}
</script>

<style scoped>
.domain-group-header td { background: rgba(116,182,164,0.07); padding: 0.35rem 0.5rem; }
</style>
