/**
 * api.js — Thin wrapper around the FastAPI backend.
 * All fetch calls go through here. Token stored in localStorage.
 */

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function getToken() {
  return localStorage.getItem('token')
}

function setToken(token) {
  localStorage.setItem('token', token)
}

function clearToken() {
  localStorage.removeItem('token')
}

async function request(method, path, body) {
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body != null ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }

  if (res.status === 204) return null
  return res.json()
}

const get  = (path)        => request('GET', path)
const post = (path, body)  => request('POST', path, body)
const patch= (path, body)  => request('PATCH', path, body)
const del  = (path)        => request('DELETE', path)

// ── Auth ──────────────────────────────────────────────────────────────────────

export const auth = {
  guestLogin: async () => {
    const data = await post('/auth/guest')
    setToken(data.access_token)
    return data
  },
  register: (username, password, email) =>
    post('/auth/register', { username, password, email }),
  login: (username, password) =>
    post('/auth/login', { username, password }),
  logout: () => {
    clearToken()
  },
  setToken,
  getToken,
  clearToken,
}

// ── Cities ────────────────────────────────────────────────────────────────────

export const cities = {
  list: ()             => get('/cities'),
  get:  (id)           => get(`/cities/${id}`),
}

// ── User City ─────────────────────────────────────────────────────────────────

export const city = {
  load:   (userId, cityId) => post(`/users/${userId}/city/load`, { city_id: cityId }),
  create: (userId, data)    => post(`/users/${userId}/city/new`, data),
  get:    (userId)          => get(`/users/${userId}/city`),
  patch:  (userId, data)    => patch(`/users/${userId}/city`, data),
  publish:(userId)          => post(`/users/${userId}/city/publish`),

  addFaction:    (userId, data)    => post(`/users/${userId}/city/factions`, data),
  patchFaction:  (userId, id, data)=> patch(`/users/${userId}/city/factions/${id}`, data),
  deleteFaction: (userId, id)      => del(`/users/${userId}/city/factions/${id}`),
}

// ── Sim ───────────────────────────────────────────────────────────────────────

export const sim = {
  runs:      (userId)          => get(`/users/${userId}/runs`),
  deleteRun: (userId, runId)   => del(`/users/${userId}/runs/${runId}`),
  switch:    (userId, runId)   => post(`/users/${userId}/sim/switch/${runId}`),
  start:  (userId, llmProfileId, identity = {}) => post(`/users/${userId}/sim/start`, {
    llm_profile_id: llmProfileId || null,
    player_name: identity.player_name || null,
    player_title: identity.player_title || null,
  }),
  step:   (userId)    => post(`/users/${userId}/sim/step`),
  run:    (userId, n) => post(`/users/${userId}/sim/run/${n}`),
  pause:   (userId)       => post(`/users/${userId}/sim/pause`),
  reset:   (userId)       => post(`/users/${userId}/sim/reset`),
  status:  (userId)       => get(`/users/${userId}/sim/status`),
  patchInfo: (userId, data) => patch(`/users/${userId}/sim/info`, data),
  setLlmProfile: (userId, llm_profile_id) =>
    patch(`/users/${userId}/sim/llm-profile`, { llm_profile_id: llm_profile_id || null }),
}

// ── State ─────────────────────────────────────────────────────────────────────

export const state = {
  full:       (userId)        => get(`/users/${userId}/state`),
  factions:   (userId)        => get(`/users/${userId}/factions`),
  faction:    (userId, id)    => get(`/users/${userId}/factions/${id}`),
  domains:    (userId)        => get(`/users/${userId}/domains`),
  logs:       (userId, limit) => get(`/users/${userId}/logs${limit ? `?limit=${limit}` : ''}`),
  cycles:     (userId)        => get(`/users/${userId}/cycles`),
  cycle:      (userId, n)     => get(`/users/${userId}/cycles/${n}`),

  patchFaction:   (userId, id, data)  => patch(`/users/${userId}/factions/${id}`, data),
  addFaction:     (userId, data)      => post(`/users/${userId}/factions`, data),
  deleteFaction:  (userId, id)        => del(`/users/${userId}/factions/${id}`),
  triggerEvent:   (userId, data)      => post(`/users/${userId}/events/trigger`, data),
}

// ── Treasury ─────────────────────────────────────────────────────────────────

export const treasury = {
  get:        (userId)              => get(`/users/${userId}/treasury`),
  setTaxRate: (userId, domain_id, rate) =>
    patch(`/users/${userId}/treasury/tax-rate`, { domain_id, rate }),
  borrow:     (userId, amount)      => post(`/users/${userId}/treasury/borrow`, { amount }),
  invest:     (userId, amount, term)=> post(`/users/${userId}/treasury/invest`, { amount, term }),
  publicWorks:(userId)              => post(`/users/${userId}/treasury/public-works`),
  guardSurge: (userId)              => post(`/users/${userId}/treasury/guard-surge`),
}

// ── Mayor ─────────────────────────────────────────────────────────────────────

export const mayor = {
  get:         (userId)                        => get(`/users/${userId}/mayor`),
  exempt:      (userId, faction_id, cycles)    =>
    post(`/users/${userId}/mayor/exempt`, { faction_id, cycles }),
  act: (userId, action, targetId = '', targetId2 = '', cycles = 5) =>
    post(`/users/${userId}/mayor/act`, {
      action,
      target_id: targetId,
      target_id_2: targetId2,
      cycles,
    }),
  audienceBegin:    (userId, faction_id)   => post(`/users/${userId}/mayor/audience/begin`,    { faction_id }),
  audienceReply:    (userId, mayor_opening) => post(`/users/${userId}/mayor/audience/reply`,    { mayor_opening }),
  audienceConclude: (userId, mayor_closing) => post(`/users/${userId}/mayor/audience/conclude`, { mayor_closing }),
  audienceFinalize: (userId, mayor_accepts) => post(`/users/${userId}/mayor/audience/finalize`, { mayor_accepts }),
}

// ── Projects ──────────────────────────────────────────────────────────────────

export const projects = {
  list:       (userId)            => get(`/users/${userId}/projects`),
  catalog:    (userId)            => get(`/users/${userId}/projects/catalog`),
  commission: (userId, project_id)=> post(`/users/${userId}/projects/commission`, { project_id }),
}


// ── Members ──────────────────────────────────────────────────────────────────

export const members = {
  list:   (cityId)          => get(`/cities/${cityId}/members`),
  add:    (cityId, data)    => post(`/cities/${cityId}/members`, data),
  remove: (cityId, userId)  => del(`/cities/${cityId}/members/${userId}`),
}

// ── LLM Profiles ─────────────────────────────────────────────────────────────

export const llmProfiles = {
  list:    ()               => get('/llm-profiles'),
  create:  (data)           => post('/llm-profiles', data),
  update:  (id, data)       => request('PUT', `/llm-profiles/${id}`, data),
  remove:  (id)             => del(`/llm-profiles/${id}`),
  test:    (id)             => post(`/llm-profiles/${id}/test`),
}
