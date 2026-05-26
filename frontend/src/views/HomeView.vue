<template>
  <div class="page">
    <nav>
      <span class="brand">Polis</span>
      <span class="nav-user">{{ store.username }}</span>
      <span class="spacer"></span>
      <button class="btn-subtle btn-sm" @click="showSettings = true" style="margin-right:0.5rem">Settings</button>
      <button class="btn-subtle btn-sm" @click="logout">Logout</button>
    </nav>

    <LLMSettings v-if="showSettings" @close="showSettings = false" />

    <div class="container" style="padding-top:2rem">
      <p v-if="error" class="error-msg" style="margin-bottom:1rem">{{ error }}</p>

      <!-- Your Runs -->
      <div style="margin-bottom:2rem">
        <div class="row" style="margin-bottom:0.75rem; align-items:center">
          <h2>Your Cities</h2>
          <span class="spacer"></span>
          <button class="btn-primary btn-sm" @click="showNewModal = true"
                  :disabled="atLimit">+ New City</button>
        </div>
        <p v-if="atLimit" class="muted" style="font-size:0.82rem; margin-bottom:0.5rem">
          City limit reached (5). Delete a city to create a new one.
        </p>

        <div v-if="loadingRuns" class="muted">Loading…</div>
        <div v-else-if="!runs.length" class="muted" style="font-size:0.85rem">
          No cities yet. Load a template below to get started.
        </div>
        <div v-else style="display:flex; flex-direction:column; gap:0.5rem">
          <div v-for="r in runs" :key="r.run_id" class="card"
               style="display:flex; align-items:center; gap:1rem">
            <div style="flex:1">
              <span style="font-weight:600">{{ r.city_name }}</span>
              <span class="tag" style="margin-left:0.5rem">{{ r.status }}</span>
            </div>
            <div class="muted" style="font-size:0.82rem">Cycle {{ r.current_cycle }}</div>
            <div style="display:flex; gap:0.5rem">
              <button v-if="r.status === 'running' || r.status === 'paused'"
                      class="btn-primary btn-sm" @click="resumeRun(r)">Resume →</button>
              <button v-else-if="r.status === 'setup'"
                      class="btn-subtle btn-sm" @click="$router.push('/builder')">
                Continue Setup →
              </button>
              <button class="btn-danger btn-sm" @click="confirmDelete(r)">Delete</button>
            </div>
          </div>
        </div>
      </div>

      <hr class="divider" />

      <!-- Templates -->
      <div style="margin-top:1.5rem">
        <h2 style="margin-bottom:0.75rem">City Templates</h2>
        <div v-if="loadingTemplates" class="muted">Loading…</div>
        <div v-else class="row" style="flex-wrap:wrap; gap:0.75rem">
          <div v-for="t in templates" :key="t.city_id" class="card"
               style="width:260px; cursor:pointer" @click="previewTemplate(t)">
            <div style="font-weight:600; margin-bottom:0.25rem">{{ t.city_name }}</div>
            <div class="muted" style="font-size:0.8rem; margin-bottom:0.4rem">by {{ t.author }}</div>
            <div style="font-size:0.82rem; margin-bottom:0.5rem">{{ t.description }}</div>
            <div style="font-size:0.78rem; color:var(--muted); display:flex; gap:0.75rem">
              <span>{{ t.faction_count }} factions</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Template Preview Modal -->
    <div v-if="previewCity" class="modal-overlay" @click.self="previewCity = null">
      <div class="card modal-box">
        <h2 style="margin-bottom:0.25rem">{{ previewCity.city_name }}</h2>
        <div class="muted" style="font-size:0.82rem; margin-bottom:0.75rem">
          by {{ previewCity.author }} &bull; {{ previewCity.setting }}
        </div>
        <p style="font-size:0.85rem; margin-bottom:0.75rem">{{ previewCity.description }}</p>
        <div style="display:flex; gap:1rem; font-size:0.82rem; margin-bottom:1rem">
          <span class="tag">{{ previewCity.faction_count }} factions</span>
        </div>
        <p v-if="atLimit" class="error-msg" style="margin-bottom:0.5rem">
          City limit reached (5). Delete a city first.
        </p>
        <div style="display:flex; gap:0.5rem; justify-content:flex-end">
          <button class="btn-subtle" @click="previewCity = null">Cancel</button>
          <button class="btn-primary" @click="loadTemplate(previewCity)"
                  :disabled="atLimit">Load this City →</button>
        </div>
      </div>
    </div>

    <!-- New City Modal -->
    <div v-if="showNewModal" class="modal-overlay" @click.self="showNewModal = false">
      <div class="card modal-box">
        <h2 style="margin-bottom:1rem">New Blank City</h2>
        <div class="field">
          <label>City Name</label>
          <input v-model="newCity.city_name" placeholder="e.g. Ashford" />
        </div>
        <div class="field">
          <label>Description</label>
          <input v-model="newCity.description" />
        </div>
        <div style="display:flex; gap:0.5rem; justify-content:flex-end; margin-top:1rem">
          <button class="btn-subtle" @click="showNewModal = false">Cancel</button>
          <button class="btn-primary" @click="createNew"
                  :disabled="!newCity.city_name || creating">
            {{ creating ? 'Creating…' : 'Create' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirm -->
    <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
      <div class="card modal-box">
        <h2 style="margin-bottom:0.75rem">Delete City?</h2>
        <p style="margin-bottom:1rem; font-size:0.9rem">
          Delete <strong>{{ deleteTarget.city_name }}</strong>? This cannot be undone.
        </p>
        <div style="display:flex; gap:0.5rem; justify-content:flex-end">
          <button class="btn-subtle" @click="deleteTarget = null">Cancel</button>
          <button class="btn-danger" @click="deleteRun" :disabled="deleting">
            {{ deleting ? 'Deleting…' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { auth, cities, city, sim } from '../api.js'
import { store } from '../store.js'
import LLMSettings from '../components/LLMSettings.vue'

const MAX_CITIES = 5

export default {
  name: 'HomeView',
  components: { LLMSettings },
  data() {
    return {
      store,
      runs: [],
      templates: [],
      loadingRuns: true,
      loadingTemplates: true,
      error: '',
      previewCity: null,
      showNewModal: false,
      showSettings: false,
      newCity: { city_name: '', description: '' },
      deleteTarget: null,
      creating: false,
      deleting: false,
    }
  },
  computed: {
    atLimit() { return this.runs.length >= MAX_CITIES },
  },
  async mounted() {
    await Promise.all([this.fetchRuns(), this.fetchTemplates()])
  },
  methods: {
    async fetchRuns() {
      try {
        this.runs = await sim.runs(store.userId)
      } catch (e) {
        this.error = e.message
      } finally {
        this.loadingRuns = false
      }
    },
    async fetchTemplates() {
      try {
        this.templates = await cities.list()
      } catch (e) {
        this.error = e.message
      } finally {
        this.loadingTemplates = false
      }
    },
    previewTemplate(t) {
      this.previewCity = t
    },
    async loadTemplate(t) {
      if (this.atLimit) return
      try {
        await city.load(store.userId, t.city_id)
        this.previewCity = null
        this.$router.push('/builder')
      } catch (e) {
        this.error = e.message
      }
    },
    async createNew() {
      if (this.atLimit || !this.newCity.city_name) return
      this.creating = true
      try {
        await city.create(store.userId, this.newCity)
        this.showNewModal = false
        this.$router.push('/builder')
      } catch (e) {
        this.error = e.message
      } finally {
        this.creating = false
      }
    },
    async resumeRun(run) {
      try {
        const status = await sim.switch(store.userId, run.run_id)
        store.simStatus = status
        this.$router.push('/dashboard')
      } catch (e) {
        this.error = e.message
      }
    },
    confirmDelete(run) {
      this.deleteTarget = run
    },
    async deleteRun() {
      this.deleting = true
      try {
        const r = this.deleteTarget
        this.deleteTarget = null
        await sim.deleteRun(store.userId, r.run_id)
        this.runs = this.runs.filter(x => x.run_id !== r.run_id)
        // Clear local sim status if we just deleted the active run
        if (store.simStatus && store.simStatus.run_id === r.run_id) {
          store.simStatus = null
        }
      } catch (e) {
        this.error = e.message
      } finally {
        this.deleting = false
      }
    },
    logout() {
      auth.logout()
      store.clearUser()
      this.$router.push('/')
    },
  },
}
</script>

<style scoped>
</style>
