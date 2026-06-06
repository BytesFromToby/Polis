<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="mayor-modal">

      <!-- Header -->
      <div class="modal-header">
        <div>
          <span class="modal-title">Mayor Actions</span>
          <span class="ap-badge" :class="{ 'ap-low': ap <= 1 }">
            {{ ap }} / {{ apCap }} AP
          </span>
          <span class="gold-badge">{{ gold }} gold</span>
        </div>
        <button class="btn-subtle btn-sm" @click="$emit('close')">Close</button>
      </div>

      <!-- Result banner -->
      <div v-if="lastResult" class="result-banner" :class="lastResult.dramatic ? 'dramatic' : ''">
        <span class="result-outcome">{{ lastResult.outcome }}</span>
        {{ lastResult.narrative }}
      </div>
      <div v-if="actError" class="result-banner fail">{{ actError }}</div>

      <div class="action-columns">

        <!-- LEFT COLUMN -->
        <div class="action-col">

          <!-- Political -->
          <div class="action-group">
            <div class="group-label">Political</div>

            <!-- Endorse -->
            <div class="action-row" :class="{ disabled: ap < 1 || busy }">
              <div class="action-row-header">
                <span class="action-name">Endorse a Faction</span>
                <span class="ap-cost">1 AP</span>
              </div>
              <select v-model="targetFaction" class="act-select">
                <option value="">Select faction</option>
                <option v-for="f in factionList" :key="f.id" :value="f.id">{{ f.name }}</option>
              </select>
              <div class="action-hint">+10 rep · domain peers −3 · Public ±5</div>
              <button class="btn-primary btn-sm act-btn" :disabled="ap < 1 || busy" @click="doAct('PubliclyEndorse', targetFaction)">Act</button>
            </div>

            <!-- Condemn -->
            <div class="action-row" :class="{ disabled: ap < 1 || busy }">
              <div class="action-row-header">
                <span class="action-name">Condemn a Faction</span>
                <span class="ap-cost">1 AP</span>
              </div>
              <select v-model="targetFaction" class="act-select">
                <option value="">Select faction</option>
                <option v-for="f in factionList" :key="f.id" :value="f.id">{{ f.name }}</option>
              </select>
              <div class="action-hint">−15 rep · domain peers +3</div>
              <button class="btn-primary btn-sm act-btn" :disabled="ap < 1 || busy" @click="doAct('PubliclyCondemn', targetFaction)">Act</button>
            </div>
          </div>

        </div>

        <!-- RIGHT COLUMN -->
        <div class="action-col">

          <!-- Economic -->
          <div class="action-group">
            <div class="group-label">Economic</div>

            <!-- Grant Tax Exemption -->
            <div class="action-row" :class="{ disabled: ap < 1 || busy }">
              <div class="action-row-header">
                <span class="action-name">Grant Tax Exemption</span>
                <span class="ap-cost">1 AP</span>
              </div>
              <select v-model="exemptFaction" class="act-select">
                <option value="">Select faction</option>
                <option v-for="f in factionList" :key="f.id" :value="f.id">{{ f.name }}</option>
              </select>
              <div style="display:flex; align-items:center; gap:0.4rem; margin-top:0.25rem">
                <span class="action-hint" style="margin:0">Cycles:</span>
                <input v-model.number="exemptCycles" type="number" min="1" max="10"
                       style="width:48px; padding:0.2rem 0.3rem; font-size:0.8rem" />
                <span class="action-hint" style="margin:0">(1–10) · 1 per domain limit</span>
              </div>
              <button class="btn-primary btn-sm act-btn" :disabled="ap < 1 || busy" @click="doAct('GrantTaxExemption', exemptFaction, '', exemptCycles)">Act</button>
            </div>

            <!-- Sabotage -->
            <div class="action-row" :class="{ disabled: ap < 1 || gold < 50 || busy }">
              <div class="action-row-header">
                <span class="action-name">Sabotage</span>
                <span class="ap-cost">1 AP · 50g</span>
              </div>
              <select v-model="targetFaction" class="act-select">
                <option value="">Select faction</option>
                <option v-for="f in factionList" :key="f.id" :value="f.id">{{ f.name }}</option>
              </select>
              <div class="action-hint">rank −50% of margin · health −50% · rep −10 · 1 AP + 50 gold</div>
              <button class="btn-primary btn-sm act-btn" :disabled="ap < 1 || gold < 50 || busy" @click="doAct('Sabotage', targetFaction)">Act</button>
            </div>

            <!-- Build Project -->
            <div class="action-row" :class="{ disabled: ap < 1 || busy }">
              <div class="action-row-header">
                <span class="action-name">Build Project</span>
                <span class="ap-cost">1 AP · gold</span>
              </div>
              <select v-model="targetDomain" class="act-select">
                <option value="">Select domain</option>
                <option v-for="(d, id) in domains" :key="id" :value="id">{{ d.name || id }}</option>
              </select>
              <div class="action-hint">Break ground / fund a unit (50g) or repair (+25 health, 30g) · 1 AP</div>
              <button class="btn-primary btn-sm act-btn" :disabled="ap < 1 || busy" @click="doAct('BuildProject', targetDomain)">Act</button>
            </div>
          </div>

          <!-- Deals -->
          <div v-if="activeDeals.length" class="action-group">
            <div class="group-label">Deals</div>
            <div v-for="deal in activeDeals" :key="deal.deal_id" class="deal-row">
              <div class="deal-info">
                <span class="deal-faction">{{ factionName(deal.faction_id) }}</span>
                <span class="action-hint">{{ deal.cycles_remaining }} cycles left</span>
              </div>
              <button class="btn-danger btn-sm" :disabled="busy" @click="doAct('BreakADeal', deal.deal_id)">Break</button>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mayor as mayorApi } from '../api.js'
import { store } from '../store.js'

export default {
  name: 'MayorActionsModal',
  props: {
    factions: { type: Object, default: () => ({}) },
    domains:  { type: Object, default: () => ({}) },
    mayorData: { type: Object, default: null },
    gold: { type: Number, default: 0 },
  },
  emits: ['close', 'acted'],
  data() {
    return {
      ap: this.mayorData?.action_points ?? 0,
      apCap: this.mayorData?.action_cap ?? 6,
      lastResult: null,
      actError: null,
      busy: false,
      targetFaction: '',
      targetDomain: '',
      exemptFaction: '',
      exemptCycles: 5,
    }
  },
  watch: {
    mayorData(val) {
      if (val) {
        this.ap = val.action_points
        this.apCap = val.action_cap
      }
    },
  },
  computed: {
    factionList() {
      return Object.values(this.factions || {})
    },
    activeDeals() {
      if (!this.mayorData?.deals) return []
      return Object.values(this.mayorData.deals).filter(d => d.status === 'active')
    },
  },
  methods: {
    factionName(id) {
      return this.factions[id]?.name || id
    },
    async doAct(action, targetId = '', targetId2 = '', cycles = this.exemptCycles) {
      this.actError = null
      this.lastResult = null
      this.busy = true
      try {
        const result = await mayorApi.act(
          store.userId,
          action,
          targetId || '',
          typeof targetId2 === 'number' ? '' : (targetId2 || ''),
          typeof targetId2 === 'number' ? targetId2 : cycles,
        )
        this.ap = result.action_points
        this.lastResult = result
        this.$emit('acted', result)
      } catch (e) {
        this.actError = e.message
      } finally {
        this.busy = false
      }
    },
  },
}
</script>

<style scoped>
.mayor-modal {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius, 8px);
  width: 860px;
  max-width: 96vw;
  max-height: 90vh;
  overflow-y: auto;
  padding: 1rem;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}
.modal-title {
  font-size: 1rem;
  font-weight: 700;
  margin-right: 0.75rem;
}
.ap-badge {
  font-size: 0.8rem;
  font-weight: 600;
  background: var(--surface, #252540);
  border: 1px solid var(--border, #333);
  border-radius: 12px;
  padding: 0.15rem 0.6rem;
}
.ap-low { color: var(--danger, #e05c5c); }
.gold-badge {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--accent2, #c99f5c);
  background: var(--surface, #252540);
  border: 1px solid var(--border, #333);
  border-radius: 12px;
  padding: 0.15rem 0.6rem;
  margin-left: 0.4rem;
}

.result-banner {
  font-size: 0.82rem;
  padding: 0.4rem 0.6rem;
  border-radius: var(--radius, 6px);
  margin-bottom: 0.75rem;
  background: rgba(116, 182, 164, 0.1);
  border: 1px solid rgba(116, 182, 164, 0.3);
}
.result-banner.dramatic {
  background: rgba(201, 159, 92, 0.12);
  border-color: rgba(201, 159, 92, 0.4);
  color: var(--accent2);
}
.result-banner.fail {
  background: rgba(176, 84, 94, 0.12);
  border-color: var(--danger);
  color: var(--danger);
}
.result-outcome {
  font-weight: 700;
  text-transform: uppercase;
  font-size: 0.72rem;
  margin-right: 0.4rem;
  opacity: 0.7;
}

.action-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.action-group {
  margin-bottom: 1rem;
}
.group-label {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--muted, #888);
  margin-bottom: 0.4rem;
  padding-bottom: 0.2rem;
  border-bottom: 1px solid var(--border, #333);
}

.action-row {
  background: var(--surface, #252540);
  border: 1px solid var(--border, #333);
  border-radius: var(--radius, 6px);
  padding: 0.5rem 0.6rem;
  margin-bottom: 0.4rem;
  transition: opacity 0.15s;
}
.action-row.disabled { opacity: 0.45; }

.action-row-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.3rem;
}
.action-name { font-size: 0.83rem; font-weight: 600; }
.ap-cost {
  font-size: 0.72rem;
  color: var(--accent, #7c6fcd);
  font-weight: 600;
}
.act-select {
  padding: 0.3rem 0.4rem;
  font-size: 0.8rem;
  width: 100%;
  margin-bottom: 0.25rem;
}
.action-hint {
  font-size: 0.72rem;
  color: var(--muted, #888);
  margin-bottom: 0.3rem;
}
.act-btn { margin-top: 0.25rem; }

.deal-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.35rem 0.5rem;
  background: var(--surface, #252540);
  border: 1px solid var(--border, #333);
  border-radius: var(--radius, 6px);
  margin-bottom: 0.3rem;
}
.deal-info { display: flex; flex-direction: column; gap: 0.1rem; }
.deal-faction { font-size: 0.82rem; font-weight: 600; }
</style>
