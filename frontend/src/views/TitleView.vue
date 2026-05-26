<template>
  <div class="title-wrap">
    <div class="title-box">
      <div class="title-city">Rivers Point</div>
      <div class="title-sub">An emergent political simulation</div>

      <p v-if="error" class="error-msg" style="margin-bottom:1rem">{{ error }}</p>

      <div v-if="!showLoad" class="btn-group">
        <button class="btn-primary btn-large" @click="newGame" :disabled="busy">
          {{ busy === 'new' ? 'Starting…' : 'New Game' }}
        </button>
        <button class="btn-subtle btn-large" @click="openLoad" :disabled="busy">
          Load Game
        </button>
      </div>

      <!-- Load game panel -->
      <div v-else>
        <div class="panel-header" style="margin-bottom:0.75rem">
          <h3>Saved Runs</h3>
          <button class="btn-subtle btn-sm" @click="showLoad = false">← Back</button>
        </div>
        <div v-if="runs.length === 0" class="muted" style="font-size:0.85rem; margin-bottom:1rem">
          No saved runs found.
        </div>
        <div v-for="run in runs" :key="run.run_id" class="run-row" @click="loadRun(run.run_id)">
          <div style="font-weight:600">{{ run.city_name }}</div>
          <div class="muted" style="font-size:0.8rem">
            Cycle {{ run.current_cycle }} · {{ run.status }}
          </div>
          <div class="muted" style="font-size:0.75rem">{{ formatDate(run.updated_at) }}</div>
        </div>
        <div v-if="runs.length === 0" style="margin-top:0.75rem">
          <button class="btn-subtle btn-large" @click="showLoad = false">Back</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { auth, cities, city, sim } from '../api.js'
import { store } from '../store.js'

export default {
  name: 'TitleView',
  data() {
    return {
      busy: null,
      error: '',
      showLoad: false,
      runs: [],
    }
  },
  async mounted() {
    try {
      const data = await auth.guestLogin()
      const payload = JSON.parse(atob(data.access_token.split('.')[1]))
      store.setUser(payload.sub, payload.username)
    } catch (e) {
      this.error = 'Could not connect to server. Is the backend running?'
    }
  },
  methods: {
    async newGame() {
      this.error = ''
      this.busy = 'new'
      try {
        const cityList = await cities.list()
        const rp = cityList.find(c => c.city_name === 'Rivers Point')
        if (!rp) throw new Error('Rivers Point city not found. Check server seed.')

        await city.load(store.userId, rp.city_id, 'gm')
        await sim.start(store.userId)
        store.simStatus = null
        this.$router.push('/game')
      } catch (e) {
        this.error = e.message
      } finally {
        this.busy = null
      }
    },
    async openLoad() {
      this.error = ''
      this.showLoad = true
      try {
        const all = await sim.runs(store.userId)
        this.runs = all.filter(r => r.status === 'running' || r.status === 'paused')
      } catch (e) {
        this.error = e.message
      }
    },
    async loadRun(runId) {
      this.error = ''
      this.busy = 'load'
      try {
        await sim.switch(store.userId, runId)
        store.simStatus = null
        this.$router.push('/game')
      } catch (e) {
        this.error = e.message
      } finally {
        this.busy = null
      }
    },
    formatDate(iso) {
      if (!iso) return ''
      return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
    },
  },
}
</script>

<style scoped>
.title-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg);
}
.title-box {
  width: 380px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 2.5rem 2rem;
  text-align: center;
}
.title-city {
  font-size: 2rem;
  font-weight: 700;
  color: var(--accent);
  letter-spacing: 0.03em;
  margin-bottom: 0.25rem;
}
.title-sub {
  font-size: 0.85rem;
  color: var(--muted);
  margin-bottom: 2rem;
}
.btn-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.btn-large {
  width: 100%;
  padding: 0.7rem 1rem;
  font-size: 1rem;
}
.run-row {
  padding: 0.6rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  margin-bottom: 0.5rem;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s;
}
.run-row:hover {
  background: rgba(124, 106, 245, 0.08);
  border-color: var(--accent);
}
</style>
