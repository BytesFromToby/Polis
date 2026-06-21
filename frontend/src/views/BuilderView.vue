<template>
  <div class="page">
    <nav>
      <span class="brand">Polis</span>
      <span class="muted">City Builder</span>
      <span class="spacer"></span>
      <button class="btn-subtle btn-sm" @click="$router.push('/home')">← Home</button>
    </nav>

    <div class="container" style="padding-top:1.5rem">
      <p v-if="error" class="error-msg" style="margin-bottom:1rem">{{ error }}</p>

      <!-- City info -->
      <div class="card" style="margin-bottom:1rem">
        <div class="panel-header">
          <div v-if="!editingCity" style="display:flex; align-items:center; gap:0.75rem; flex:1">
            <h2 style="margin:0">{{ cityData.city_name || 'Unnamed City' }}</h2>
            <button class="btn-subtle btn-sm" @click="startEditCity">Edit</button>
          </div>
          <div v-else style="display:flex; align-items:center; gap:0.5rem; flex:1">
            <input v-model="cityEdit.city_name" style="font-size:1.1rem; font-weight:600; flex:1" />
            <button class="btn-primary btn-sm" @click="saveCity" :disabled="savingCity">
              {{ savingCity ? '…' : 'Save' }}
            </button>
            <button class="btn-subtle btn-sm" @click="editingCity = false">Cancel</button>
          </div>
          <button class="btn-primary" @click="startSim" :disabled="starting" style="margin-left:auto">
            {{ starting ? 'Starting…' : 'Start Sim →' }}
          </button>
        </div>
        <div v-if="!editingCity">
          <p class="muted" style="font-size:0.85rem">{{ cityData.description || 'No description.' }}</p>
        </div>
        <div v-else style="margin-top:0.5rem">
          <textarea v-model="cityEdit.description" rows="2"
                    style="width:100%; resize:vertical; font-size:0.85rem"
                    placeholder="City description…"></textarea>
        </div>
      </div>

      <div class="row">
        <!-- Factions -->
        <div class="col">
          <div class="card">
            <div class="panel-header">
              <h3>Factions</h3>
              <button class="btn-subtle btn-sm"
                      @click="showFactionForm = !showFactionForm; editingFactionId = null">
                {{ showFactionForm ? 'Cancel' : '+ Add' }}
              </button>
            </div>

            <div v-if="showFactionForm || editingFactionId"
                 style="margin-bottom:1rem; padding-bottom:1rem; border-bottom:1px solid var(--border)">
              <FactionForm
                :key="editingFactionId || 'new-faction'"
                :submit-label="editingFactionId ? 'Save Changes' : 'Add Faction'"
                :initial="editingFactionId ? factions[editingFactionId] : null"
                @submit="editingFactionId ? saveFaction(editingFactionId, $event) : addFaction($event)"
                @cancel="editingFactionId = null; showFactionForm = false" />
            </div>

            <table>
              <thead>
                <tr><th>Name</th><th>Domain</th><th>Rating</th><th>Traits</th><th></th></tr>
              </thead>
              <tbody>
                <tr v-for="(f, id) in factions" :key="id">
                  <td>{{ f.name }}</td>
                  <td class="muted">{{ f.domain_primary }}</td>
                  <td>{{ f.rating }}</td>
                  <td class="muted" style="font-size:0.78rem">
                    {{ (f.traits || []).join(', ') || '—' }}
                  </td>
                  <td style="text-align:right; white-space:nowrap">
                    <button class="btn-subtle btn-sm" style="margin-right:0.25rem"
                            @click="editingFactionId = id; showFactionForm = false">Edit</button>
                    <button class="btn-danger btn-sm" @click="deleteFaction(id)">✕</button>
                  </td>
                </tr>
                <tr v-if="!Object.keys(factions).length">
                  <td colspan="5" class="muted">No factions yet.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Start Sim modal — AI profile selector -->
  <div v-if="showStartModal" class="modal-overlay" @click.self="showStartModal = false">
    <div class="card modal-box" style="width:420px; max-width:95vw">
      <h2 style="margin-bottom:1rem">Start Sim</h2>
      <div class="field" style="margin-bottom:1rem">
        <label>Difficulty</label>
        <select v-model="selectedDifficulty" style="padding:0.4rem 0.5rem; width:100%">
          <option value="easy">Easy — forgiving (the self-balancing city)</option>
          <option value="normal">Normal</option>
          <option value="hard">Hard — real stakes</option>
        </select>
      </div>
      <div class="field" style="margin-bottom:1.25rem">
        <label>AI Profile</label>
        <select v-model="selectedProfileId" style="padding:0.4rem 0.5rem; width:100%">
          <option value="">None (stub mode)</option>
          <option v-for="p in llmProfileList" :key="p.profile_id" :value="p.profile_id">
            {{ p.name }} ({{ p.provider }} · {{ p.model }})
          </option>
        </select>
        <div class="muted" style="font-size:0.78rem; margin-top:0.3rem">
          Select an AI to power faction conversations. None = scripted fallback.
        </div>
      </div>
      <div style="display:flex; gap:0.5rem; justify-content:flex-end">
        <button class="btn-subtle" @click="showStartModal = false">Cancel</button>
        <button class="btn-primary" @click="confirmStart" :disabled="starting">
          {{ starting ? 'Starting…' : 'Start Sim →' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { city, sim, llmProfiles } from '../api.js'
import { store } from '../store.js'
import FactionForm from '../components/FactionForm.vue'

export default {
  name: 'BuilderView',
  components: { FactionForm },
  data() {
    return {
      cityData: {},
      factions: {},
      error: '',
      starting: false,
      showFactionForm: false,
      editingFactionId: null,
      editingCity: false,
      savingCity: false,
      cityEdit: { city_name: '', description: '' },
      showStartModal: false,
      selectedProfileId: '',
      selectedDifficulty: 'normal',
      llmProfileList: [],
    }
  },
  computed: {
    factionList() {
      return Object.entries(this.factions).map(([id, f]) => ({ id, name: f.name }))
    },
  },
  async mounted() {
    await this.load()
    try {
      this.llmProfileList = await llmProfiles.list()
      // Pre-select the saved new-game default if it still exists
      const dflt = store.defaultLlmProfileId
      if (dflt && this.llmProfileList.some(p => p.profile_id === dflt)) {
        this.selectedProfileId = dflt
      }
    } catch {
      // non-fatal — profiles just won't appear in dropdown
    }
  },
  methods: {
    async load() {
      try {
        const c = await city.get(store.userId)
        this.cityData = c
        if (typeof c.factions_json === 'string') {
          this.factions = JSON.parse(c.factions_json)
        }
      } catch (e) {
        this.error = e.message
      }
    },
    startEditCity() {
      this.cityEdit = { city_name: this.cityData.city_name || '', description: this.cityData.description || '' }
      this.editingCity = true
    },
    async saveCity() {
      this.savingCity = true
      try {
        const updated = await city.patch(store.userId, this.cityEdit)
        this.cityData = updated
        this.editingCity = false
      } catch (e) {
        this.error = e.message
      } finally {
        this.savingCity = false
      }
    },
    async addFaction(payload) {
      try {
        const f = await city.addFaction(store.userId, payload)
        this.factions = { ...this.factions, [f.id]: f }
        this.showFactionForm = false
      } catch (e) {
        this.error = e.message
      }
    },
    async saveFaction(id, payload) {
      try {
        const f = await city.patchFaction(store.userId, id, payload)
        this.factions = { ...this.factions, [id]: f }
        this.editingFactionId = null
      } catch (e) {
        this.error = e.message
      }
    },
    async deleteFaction(id) {
      try {
        await city.deleteFaction(store.userId, id)
        const updated = { ...this.factions }
        delete updated[id]
        this.factions = updated
      } catch (e) {
        this.error = e.message
      }
    },
    startSim() {
      this.showStartModal = true
    },
    async confirmStart() {
      this.starting = true
      try {
        const status = await sim.start(store.userId, this.selectedProfileId || null,
                                       { difficulty: this.selectedDifficulty })
        store.simStatus = status
        this.$router.push('/dashboard')
      } catch (e) {
        this.error = e.message
        this.showStartModal = false
      } finally {
        this.starting = false
      }
    },
  },
}
</script>
