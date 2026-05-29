<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="card modal-box" style="width:560px; max-width:95vw">
      <div class="panel-header" style="margin-bottom:1rem">
        <h2 style="margin:0">AI Settings</h2>
        <button class="btn-subtle btn-sm" @click="$emit('close')">Close</button>
      </div>

      <p v-if="error" class="error-msg" style="margin-bottom:0.75rem">{{ error }}</p>

      <!-- Active city LLM -->
      <div v-if="simStatus" class="card" style="padding:0.6rem 0.75rem; margin-bottom:1rem; display:flex; align-items:center; gap:0.75rem; flex-wrap:wrap">
        <div style="flex:1; min-width:180px">
          <div style="font-size:0.72rem; font-weight:600; color:var(--muted); text-transform:uppercase; letter-spacing:0.04em; margin-bottom:0.15rem">Active city AI</div>
          <div style="font-size:0.83rem">
            <span v-if="activeProfileName" style="font-weight:600">{{ activeProfileName }}</span>
            <span v-else class="muted" style="font-style:italic">None (stub mode)</span>
          </div>
        </div>
        <div style="display:flex; align-items:center; gap:0.4rem">
          <select v-model="changeProfileId" style="padding:0.3rem 0.4rem; font-size:0.8rem">
            <option value="">None (stub mode)</option>
            <option v-for="p in profiles" :key="p.profile_id" :value="p.profile_id">{{ p.name }}</option>
          </select>
          <button class="btn-primary btn-sm" :disabled="changingProfile" @click="applyProfileChange">
            {{ changingProfile ? '…' : 'Apply' }}
          </button>
        </div>
      </div>

      <!-- Profile list -->
      <div v-if="!showForm" style="display:flex; flex-direction:column; gap:0.5rem; margin-bottom:1rem">
        <div v-if="!profiles.length" class="muted" style="font-size:0.85rem; padding:0.5rem 0">
          No profiles yet. Add one below to use an AI.
        </div>
        <div v-for="p in profiles" :key="p.profile_id"
             class="card" style="display:flex; align-items:center; gap:0.75rem; padding:0.6rem 0.75rem">
          <div style="flex:1">
            <span style="font-weight:600">{{ p.name }}</span>
            <span class="tag" style="margin-left:0.4rem; font-size:0.72rem">{{ p.provider }}</span>
            <div class="muted" style="font-size:0.78rem; margin-top:0.15rem">
              {{ p.model }}<span v-if="p.base_url"> · {{ p.base_url }}</span>
            </div>
          </div>
          <div style="display:flex; align-items:center; gap:0.4rem">
            <span v-if="testResults[p.profile_id]" class="tag"
                  :style="{ background: testResults[p.profile_id].ok ? 'var(--accent)' : 'var(--danger)', color: testResults[p.profile_id].ok ? 'var(--on-accent)' : 'var(--on-danger)' }"
                  style="font-size:0.72rem">
              {{ testResults[p.profile_id].ok ? 'ok' : 'fail' }}
            </span>
            <button class="btn-subtle btn-sm" @click="testProfile(p)"
                    :disabled="testing === p.profile_id">
              {{ testing === p.profile_id ? '…' : 'Test' }}
            </button>
            <button class="btn-subtle btn-sm" @click="editProfile(p)">Edit</button>
            <button class="btn-danger btn-sm" @click="deleteProfile(p)"
                    :disabled="deleting === p.profile_id">
              {{ deleting === p.profile_id ? '…' : 'Delete' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Add/Edit form -->
      <div v-if="showForm" class="card" style="margin-bottom:1rem; padding:1rem">
        <h3 style="margin:0 0 0.75rem">{{ editingId ? 'Edit Profile' : 'Add Profile' }}</h3>

        <div class="field">
          <label>Name</label>
          <input v-model="form.name" placeholder="e.g. Claude API" />
        </div>

        <div class="field">
          <label>Provider</label>
          <select v-model="form.provider" style="padding:0.4rem 0.5rem">
            <option value="anthropic">Anthropic</option>
            <option value="openai_compat">OpenAI-compatible (Ollama, OpenAI, LM Studio…)</option>
          </select>
        </div>

        <div class="field">
          <label>Model</label>
          <input v-model="form.model"
                 :placeholder="form.provider === 'anthropic' ? 'claude-sonnet-4-6' : 'llama3.2'" />
        </div>

        <div class="field" v-if="form.provider === 'openai_compat'">
          <label>Base URL</label>
          <input v-model="form.base_url" placeholder="http://localhost:11434/v1" />
        </div>

        <div class="field">
          <label>API Key{{ editingId ? ' (leave blank to keep existing)' : '' }}</label>
          <input v-model="form.api_key" type="password"
                 :placeholder="form.provider === 'openai_compat' ? 'ollama (or leave blank)' : 'sk-ant-...'" />
        </div>

        <details style="margin-bottom:0.75rem; font-size:0.82rem; cursor:pointer">
          <summary class="muted">Advanced</summary>
          <div style="margin-top:0.5rem; display:flex; gap:1rem">
            <div class="field" style="flex:1">
              <label>Temperature</label>
              <input v-model.number="form.temperature" type="number" min="0" max="1" step="0.1" />
            </div>
            <div class="field" style="flex:1">
              <label>Max Tokens</label>
              <input v-model.number="form.max_tokens" type="number" min="1" />
            </div>
            <div class="field" style="flex:1">
              <label>Timeout (s)</label>
              <input v-model.number="form.timeout" type="number" min="1" />
            </div>
          </div>
        </details>

        <div style="display:flex; gap:0.5rem; justify-content:flex-end">
          <button class="btn-subtle" @click="cancelForm">Cancel</button>
          <button class="btn-primary" @click="saveProfile" :disabled="saving || !form.name || !form.model">
            {{ saving ? 'Saving…' : (editingId ? 'Update' : 'Add Profile') }}
          </button>
        </div>
      </div>

      <button v-if="!showForm" class="btn-subtle btn-sm" @click="openAddForm">+ Add Profile</button>
    </div>
  </div>
</template>

<script>
import { llmProfiles, sim as simApi } from '../api.js'
import { store } from '../store.js'

const DEFAULT_FORM = () => ({
  name: '',
  provider: 'anthropic',
  model: '',
  api_key: '',
  base_url: '',
  temperature: 0.7,
  max_tokens: 1200,
  timeout: 30,
})

export default {
  name: 'LLMSettings',
  emits: ['close'],
  data() {
    return {
      profiles: [],
      showForm: false,
      editingId: null,
      form: DEFAULT_FORM(),
      saving: false,
      deleting: null,
      testing: null,
      testResults: {},
      error: null,
      simStatus: null,
      changeProfileId: '',
      changingProfile: false,
    }
  },
  computed: {
    activeProfileName() {
      if (!this.simStatus?.llm_profile_id) return null
      const p = this.profiles.find(x => x.profile_id === this.simStatus.llm_profile_id)
      return p ? p.name : this.simStatus.llm_profile_id
    },
  },
  async created() {
    await this.loadProfiles()
    if (store.userId) {
      try {
        this.simStatus = await simApi.status(store.userId)
        this.changeProfileId = this.simStatus.llm_profile_id || ''
      } catch { /* no active run — hide the section */ }
    }
  },
  methods: {
    async loadProfiles() {
      try {
        this.profiles = await llmProfiles.list()
      } catch (e) {
        this.error = e.message
      }
    },
    openAddForm() {
      this.editingId = null
      this.form = DEFAULT_FORM()
      this.showForm = true
      this.error = null
    },
    editProfile(p) {
      this.editingId = p.profile_id
      this.form = {
        name: p.name,
        provider: p.provider,
        model: p.model,
        api_key: '',
        base_url: p.base_url,
        temperature: p.temperature,
        max_tokens: p.max_tokens,
        timeout: p.timeout,
      }
      this.showForm = true
      this.error = null
    },
    cancelForm() {
      this.showForm = false
      this.editingId = null
      this.form = DEFAULT_FORM()
    },
    async saveProfile() {
      this.saving = true
      this.error = null
      try {
        const payload = { ...this.form }
        if (this.editingId && !payload.api_key) delete payload.api_key
        if (this.editingId) {
          await llmProfiles.update(this.editingId, payload)
        } else {
          await llmProfiles.create(payload)
        }
        await this.loadProfiles()
        this.cancelForm()
      } catch (e) {
        this.error = e.message
      } finally {
        this.saving = false
      }
    },
    async applyProfileChange() {
      this.changingProfile = true
      this.error = null
      try {
        await simApi.setLlmProfile(store.userId, this.changeProfileId || null)
        if (this.simStatus) this.simStatus.llm_profile_id = this.changeProfileId || null
      } catch (e) {
        this.error = e.message
      } finally {
        this.changingProfile = false
      }
    },
    async deleteProfile(p) {
      this.deleting = p.profile_id
      this.error = null
      try {
        await llmProfiles.remove(p.profile_id)
        this.profiles = this.profiles.filter(x => x.profile_id !== p.profile_id)
        delete this.testResults[p.profile_id]
      } catch (e) {
        this.error = e.message
      } finally {
        this.deleting = null
      }
    },
    async testProfile(p) {
      this.testing = p.profile_id
      this.error = null
      try {
        const result = await llmProfiles.test(p.profile_id)
        this.testResults = { ...this.testResults, [p.profile_id]: result }
        if (!result.ok) this.error = `Test failed: ${result.error}`
      } catch (e) {
        this.testResults = { ...this.testResults, [p.profile_id]: { ok: false } }
        this.error = e.message
      } finally {
        this.testing = null
      }
    },
  },
}
</script>
