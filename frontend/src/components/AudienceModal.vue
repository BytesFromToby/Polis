<template>
  <div class="modal-overlay" @click.self="maybeClose">
    <div class="audience-modal">

      <div class="modal-header">
        <span class="modal-title">Audience — {{ factionName }}</span>
        <button class="btn-subtle btn-sm" @click="maybeClose">Close</button>
      </div>

      <p v-if="fatalError" class="err" style="margin-bottom:0.75rem">{{ fatalError }}</p>

      <!-- Transcript -->
      <div class="transcript">

        <!-- Step 1: faction opens -->
        <div v-if="step >= 1">
          <div class="turn faction-turn">
            <div class="turn-label">{{ factionName }}</div>
            <div class="turn-text">{{ step1 }}</div>
          </div>
          <div class="deal-status">{{ statusAfter1 }}</div>
        </div>

        <!-- Typing indicator for step 1 -->
        <div v-if="phase === 'loading-step1'" class="turn faction-turn loading-turn">
          <div class="turn-label">{{ factionName }}</div>
          <div class="typing-dots"><span></span><span></span><span></span></div>
        </div>

        <!-- Step 2: mayor's opening (once submitted) -->
        <div v-if="step >= 2" class="turn mayor-turn">
          <div class="turn-label">Mayor</div>
          <div class="turn-text">{{ mayorOpening }}</div>
        </div>

        <!-- Step 3: faction responds -->
        <div v-if="step >= 3">
          <div class="turn faction-turn">
            <div class="turn-label">{{ factionName }}</div>
            <div class="turn-text">{{ step3 }}</div>
          </div>
          <div class="deal-status">{{ statusAfter3 }}</div>
        </div>

        <!-- Typing indicator for step 3 -->
        <div v-if="phase === 'loading-step3'" class="turn faction-turn loading-turn">
          <div class="turn-label">{{ factionName }}</div>
          <div class="typing-dots"><span></span><span></span><span></span></div>
        </div>

        <!-- Step 4: mayor's closing (once submitted) -->
        <div v-if="step >= 4" class="turn mayor-turn">
          <div class="turn-label">Mayor</div>
          <div class="turn-text">{{ mayorClosing }}</div>
        </div>

        <!-- Step 5: faction concludes -->
        <div v-if="step >= 5">
          <div class="turn faction-turn" :class="step5TurnClass">
            <div class="turn-label">{{ factionName }}</div>
            <div class="turn-text">{{ step5 }}</div>
          </div>
          <div class="deal-status" :class="statusToneClass">{{ statusAfter5 }}</div>
        </div>

        <!-- Typing indicator for step 5 -->
        <div v-if="phase === 'loading-step5'" class="turn faction-turn loading-turn">
          <div class="turn-label">{{ factionName }}</div>
          <div class="typing-dots"><span></span><span></span><span></span></div>
        </div>

        <!-- Mayor confirmation — only when the faction accepted -->
        <div v-if="phase === 'await-confirm'" class="confirm-box">
          <div class="confirm-label">The faction accepts. Confirm the deal?</div>
          <div class="terms-grid">
            <div class="terms-col">
              <div class="terms-head">You give</div>
              <div v-if="proposedMayorTerms.length">
                <div v-for="(t, i) in proposedMayorTerms" :key="'m'+i" class="term-row">{{ termLabel(t) }}</div>
              </div>
              <div v-else class="term-row muted">—</div>
            </div>
            <div class="terms-col">
              <div class="terms-head">They give</div>
              <div v-if="proposedFactionTerms.length">
                <div v-for="(t, i) in proposedFactionTerms" :key="'f'+i" class="term-row">{{ termLabel(t) }}</div>
              </div>
              <div v-else class="term-row muted">—</div>
            </div>
          </div>
          <div class="confirm-actions">
            <button class="btn-subtle" :disabled="finalizeBusy" @click="confirm(false)">Decline</button>
            <button class="btn-primary" :disabled="finalizeBusy" @click="confirm(true)">
              {{ finalizeBusy ? 'Sealing…' : 'Accept' }}
            </button>
          </div>
        </div>

        <!-- Terminal outcome -->
        <div v-if="concluded">
          <div class="deal-banner" :class="bannerClass">
            <span class="deal-verdict">{{ verdictText }}</span>
            <span v-if="result && result.memory_note" class="deal-note">{{ result.memory_note }}</span>
            <span v-if="result && result.parse_error" class="deal-note warn">⚠ {{ result.parse_error }}</span>
            <span v-if="result && result.action_points != null" class="deal-note">AP remaining: {{ result.action_points }}</span>
          </div>
          <div style="display:flex; justify-content:flex-end; margin-top:0.6rem">
            <button class="btn-primary" @click="$emit('close')">OK</button>
          </div>
        </div>

      </div>

      <!-- Input area (outside transcript, always visible at bottom) -->
      <div v-if="phase === 'await-opening'" class="input-area">
        <textarea v-model="inputText" rows="3"
                  placeholder="Your opening offer — what do you want from this faction, and what will you offer in return?"
                  @keydown.enter.ctrl="submitOpening" />
        <div class="input-footer">
          <span class="hint muted">Ctrl+Enter to send</span>
          <button class="btn-primary" :disabled="!inputText.trim()" @click="submitOpening">Send ↵</button>
        </div>
      </div>

      <div v-if="phase === 'await-closing'" class="input-area">
        <textarea v-model="inputText" rows="3"
                  placeholder="Your closing position — final offer or last words before they decide…"
                  @keydown.enter.ctrl="submitClosing" />
        <div class="input-footer">
          <span class="hint muted">Ctrl+Enter to send</span>
          <button class="btn-primary" :disabled="!inputText.trim()" @click="submitClosing">Send ↵</button>
        </div>
      </div>

      <div v-if="phase === 'idle'" style="display:flex; justify-content:flex-end; margin-top:0.75rem">
        <button class="btn-primary" @click="begin">Begin Audience →</button>
      </div>

      <!-- Debug controls — always present, collapsed by default -->
      <div v-if="debugLog.length" class="debug-controls">
        <details class="debug-block">
          <summary>Show JSON</summary>
          <div v-for="(d, i) in debugLog" :key="'j'+i" class="debug-entry">
            <div class="debug-entry-label">{{ d.label }} — request</div>
            <pre class="json-dump">{{ requestJson(d) }}</pre>
          </div>
        </details>
        <details class="debug-block">
          <summary>Debug — all LLM calls</summary>
          <div v-for="(d, i) in debugLog" :key="'d'+i" class="debug-entry">
            <div class="debug-entry-label">{{ d.label }} — request</div>
            <pre class="json-dump">{{ requestJson(d) }}</pre>
            <div class="debug-entry-label">{{ d.label }} — raw response</div>
            <pre class="json-dump">{{ d.raw_response }}</pre>
          </div>
        </details>
      </div>

    </div>
  </div>
</template>

<script>
import { mayor as mayorApi } from '../api.js'
import { store } from '../store.js'

export default {
  name: 'AudienceModal',
  props: {
    faction: { type: Object, required: true },
  },
  emits: ['close', 'acted'],
  data() {
    return {
      // idle | loading-step1 | await-opening | loading-step3 | await-closing |
      // loading-step5 | await-confirm | loading-finalize | done
      phase: 'idle',
      step: 0,
      step1: '',
      step3: '',
      step5: '',
      mayorOpening: '',
      mayorClosing: '',
      inputText: '',
      result: null,
      fatalError: '',
      proposedMayorTerms: [],
      proposedFactionTerms: [],
      finalState: '',          // '' | 'faction_declined' | 'mayor_declined' | 'sealed'
      finalizeBusy: false,
      debugLog: [],            // [{ label, system, messages, raw_response }]
    }
  },
  computed: {
    factionName() {
      return this.faction?.name || this.faction?.id || 'Faction'
    },
    concluded() {
      return this.phase === 'done'
    },
    statusAfter1() {
      return 'No terms on the table yet'
    },
    statusAfter3() {
      return 'Negotiating'
    },
    statusAfter5() {
      if (this.phase === 'await-confirm') return 'They accept — your decision'
      if (this.finalState === 'sealed') return 'Deal sealed'
      if (this.finalState === 'mayor_declined') return 'You declined the terms'
      if (this.finalState === 'faction_declined') return 'They declined — no deal'
      return 'Awaiting their decision…'
    },
    statusToneClass() {
      if (this.finalState === 'sealed') return 'tone-yes'
      if (this.finalState === 'faction_declined' || this.finalState === 'mayor_declined') return 'tone-no'
      return ''
    },
    step5TurnClass() {
      if (this.finalState === 'sealed') return 'accepted'
      if (this.finalState === 'faction_declined') return 'rejected'
      return ''
    },
    bannerClass() {
      return this.finalState === 'sealed' ? 'deal-yes' : 'deal-no'
    },
    verdictText() {
      if (this.finalState === 'sealed') return 'Deal Sealed'
      if (this.finalState === 'mayor_declined') return 'You Declined'
      return 'No Deal'
    },
  },
  methods: {
    maybeClose() {
      if (this.phase === 'idle' || this.phase === 'done') this.$emit('close')
    },
    pushDebug(label, debug) {
      if (debug) this.debugLog.push({ label, ...debug })
    },
    requestJson(d) {
      return JSON.stringify({ system: d.system, messages: d.messages }, null, 2)
    },
    termLabel(t) {
      let s = t.type
      if (t.action) s += ` ${t.action}`
      if (t.target_id) s += ` → ${t.target_id}`
      if (t.duration) s += ` (${t.duration}cy)`
      return s
    },
    async begin() {
      this.fatalError = ''
      this.phase = 'loading-step1'
      try {
        const res = await mayorApi.audienceBegin(store.userId, this.faction.id)
        this.pushDebug('Step 1 — faction opens', res.debug)
        this.step1 = res.step1_narrative
        this.step = 1
        this.phase = 'await-opening'
        this.$nextTick(() => this.scrollDown())
      } catch (e) {
        this.fatalError = e.message
        this.phase = 'idle'
      }
    },
    async submitOpening() {
      if (!this.inputText.trim()) return
      this.mayorOpening = this.inputText.trim()
      this.inputText = ''
      this.step = 2
      this.phase = 'loading-step3'
      this.$nextTick(() => this.scrollDown())
      try {
        const res = await mayorApi.audienceReply(store.userId, this.mayorOpening)
        this.pushDebug('Step 3 — faction counters', res.debug)
        this.step3 = res.step3_narrative
        this.step = 3
        this.phase = 'await-closing'
        this.$nextTick(() => this.scrollDown())
      } catch (e) {
        this.fatalError = e.message
        this.phase = 'await-opening'
        this.step = 1
      }
    },
    async submitClosing() {
      if (!this.inputText.trim()) return
      this.mayorClosing = this.inputText.trim()
      this.inputText = ''
      this.step = 4
      this.phase = 'loading-step5'
      this.$nextTick(() => this.scrollDown())
      try {
        const res = await mayorApi.audienceConclude(store.userId, this.mayorClosing)
        this.pushDebug('Step 5 — faction concludes', res.debug)
        this.step5 = res.step5_narrative
        this.result = res
        this.step = 5
        this.$emit('acted', res)   // updates AP
        if (res.finalized) {
          // Faction declined — terminal, nothing to confirm.
          this.finalState = 'faction_declined'
          this.phase = 'done'
        } else {
          // Faction accepted — Mayor must confirm.
          this.proposedMayorTerms = res.proposed_mayor_terms || []
          this.proposedFactionTerms = res.proposed_faction_terms || []
          this.phase = 'await-confirm'
        }
        this.$nextTick(() => this.scrollDown())
      } catch (e) {
        this.fatalError = e.message
        this.phase = 'await-closing'
        this.step = 3
      }
    },
    async confirm(accept) {
      this.finalizeBusy = true
      try {
        const fin = await mayorApi.audienceFinalize(store.userId, accept)
        this.result = { ...this.result, ...fin }
        this.finalState = fin.accepted ? 'sealed' : 'mayor_declined'
        this.phase = 'done'
        this.$emit('acted', fin)   // updates AP
        this.$nextTick(() => this.scrollDown())
      } catch (e) {
        this.fatalError = e.message
      } finally {
        this.finalizeBusy = false
      }
    },
    scrollDown() {
      const el = this.$el?.querySelector('.audience-modal')
      if (el) el.scrollTop = el.scrollHeight
    },
  },
}
</script>

<style scoped>
.audience-modal {
  background: var(--bg, #1a1a2e);
  border: 1px solid var(--border, #333);
  border-radius: var(--radius, 8px);
  width: 580px;
  max-width: 96vw;
  max-height: 90vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  padding: 1rem;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  flex-shrink: 0;
}
.modal-title { font-size: 1rem; font-weight: 700; }

.err { font-size: 0.82rem; color: var(--danger); }

/* Transcript */
.transcript {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-bottom: 0.75rem;
}

.turn {
  border-radius: var(--radius, 6px);
  padding: 0.5rem 0.7rem;
}
.faction-turn {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  align-self: flex-start;
  max-width: 90%;
}
.mayor-turn {
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  border-left: 3px solid #555;
  align-self: flex-end;
  max-width: 90%;
}
.faction-turn.accepted { border-left-color: #4caf7d; }
.faction-turn.rejected { border-left-color: var(--danger); }

.turn-label {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted);
  margin-bottom: 0.25rem;
}
.turn-text { font-size: 0.83rem; line-height: 1.5; white-space: pre-wrap; }

/* Per-step deal status */
.deal-status {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted);
  margin: 0.15rem 0 0.1rem 0.2rem;
}
.deal-status.tone-yes { color: #4caf7d; }
.deal-status.tone-no  { color: var(--danger); }

/* Typing indicator */
.loading-turn { opacity: 0.7; }
.typing-dots { display: flex; gap: 4px; align-items: center; height: 18px; }
.typing-dots span {
  display: block;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--muted);
  animation: bounce 1.2s infinite;
}
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-6px); }
}

/* Mayor confirmation box */
.confirm-box {
  border: 1px solid var(--accent);
  border-radius: var(--radius, 6px);
  padding: 0.6rem 0.75rem;
  background: rgba(124, 106, 245, 0.06);
}
.confirm-label { font-size: 0.82rem; font-weight: 600; margin-bottom: 0.5rem; }
.terms-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 0.6rem; }
.terms-head {
  font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--muted); margin-bottom: 0.25rem;
}
.term-row { font-size: 0.8rem; padding: 0.1rem 0; }
.confirm-actions { display: flex; justify-content: flex-end; gap: 0.5rem; }

/* Deal outcome */
.deal-banner {
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius, 6px);
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  flex-shrink: 0;
}
.deal-yes { background: rgba(76, 175, 125, 0.12); border: 1px solid rgba(76, 175, 125, 0.4); }
.deal-no  { background: rgba(224, 92, 92, 0.08);  border: 1px solid rgba(224, 92, 92, 0.35); }
.deal-verdict { font-weight: 700; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.04em; }
.deal-yes .deal-verdict { color: #4caf7d; }
.deal-no  .deal-verdict { color: var(--danger); }
.deal-note { font-size: 0.78rem; color: var(--muted); }
.deal-note.warn { color: #e2a740; }

/* Input */
.input-area {
  flex-shrink: 0;
  border-top: 1px solid var(--border);
  padding-top: 0.6rem;
}
.input-area textarea {
  width: 100%;
  resize: none;
  padding: 0.4rem 0.5rem;
  font-size: 0.85rem;
  line-height: 1.4;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius, 4px);
  color: var(--text);
}
.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.35rem;
}
.hint { font-size: 0.72rem; }

/* Debug controls */
.debug-controls {
  margin-top: 0.75rem;
  border-top: 1px solid var(--border);
  padding-top: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.debug-block summary {
  font-size: 0.72rem;
  color: var(--muted);
  cursor: pointer;
}
.debug-entry { margin-top: 0.35rem; }
.debug-entry-label {
  font-size: 0.66rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
  margin: 0.3rem 0 0.15rem;
}
.json-dump {
  font-size: 0.72rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius, 4px);
  padding: 0.5rem;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--muted);
}
</style>
