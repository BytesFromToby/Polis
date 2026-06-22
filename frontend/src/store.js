/**
 * store.js — Minimal shared state using Vue reactive().
 * Holds the current user, active sim status, and latest state snapshot.
 */
import { reactive } from 'vue'

export const store = reactive({
  userId: localStorage.getItem('userId') || null,
  username: localStorage.getItem('username') || null,

  // Preferred AI profile applied to new games (empty string = None / stub mode).
  // Per-browser preference; the run itself stores its own llm_profile_id once started.
  defaultLlmProfileId: localStorage.getItem('defaultLlmProfileId') || '',

  simStatus: null,   // { run_id, current_cycle, status }
  snapshot: null,    // { world, factions, units, domains }
  logs: [],
  devMode: false,    // server POLIS_DEV_MODE — enables dev tools (e.g. override audiences)

  setUser(userId, username) {
    this.userId = userId
    this.username = username
    localStorage.setItem('userId', userId)
    localStorage.setItem('username', username)
  },

  setDefaultLlmProfile(profileId) {
    this.defaultLlmProfileId = profileId || ''
    if (profileId) {
      localStorage.setItem('defaultLlmProfileId', profileId)
    } else {
      localStorage.removeItem('defaultLlmProfileId')
    }
  },

  clearUser() {
    this.userId = null
    this.username = null
    this.simStatus = null
    this.snapshot = null
    this.logs = []
    localStorage.removeItem('userId')
    localStorage.removeItem('username')
  },
})
