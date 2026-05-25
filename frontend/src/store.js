/**
 * store.js — Minimal shared state using Vue reactive().
 * Holds the current user, active sim status, and latest state snapshot.
 */
import { reactive } from 'vue'

export const store = reactive({
  userId: localStorage.getItem('userId') || null,
  username: localStorage.getItem('username') || null,

  simStatus: null,   // { run_id, current_cycle, status }
  snapshot: null,    // { world, factions, units, domains }
  logs: [],

  setUser(userId, username) {
    this.userId = userId
    this.username = username
    localStorage.setItem('userId', userId)
    localStorage.setItem('username', username)
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
