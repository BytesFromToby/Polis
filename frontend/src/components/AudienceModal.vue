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
        <div v-if="step >= 1" class="turn faction-turn">
          <div class="turn-label">{{ factionName }}</div>
          <div class="turn-text">{{ step1 }}</div>
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
        <div v-if="step >= 3" class="turn faction-turn">
          <div class="turn-label">{{ factionName }}</div>
          <div class="turn-text">{{ step3 }}</div>
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
        <div v-if="step >= 5" class="turn faction-turn" :class="concluded ? (result.accepted ? 'accepted' : 'rejected') : ''">
          <div class="turn-label">{{ factionName }}</div>
          <div class="turn-text">{{ step5 }}</div>
        </div>

        <!-- Typing indicator for step 5 -->
        <div v-if="phase === 'loading-step5'" class="turn faction-turn loading-turn">
          <div class="turn-label">{{ factionName }}</div>
          <div class="typing-dots"><span></span><span></span><span></span></div>
        </div>

        <!-- Deal outcome + Done button — inside transcript so scrollDown() reaches them -->
        <div v-if="concluded">
          <div class="deal-banner" :class="result.accepted ? 'deal-yes' : 'deal-no'">
            <span class="deal-verdict">{{ result.accepted ? 'Deal Accepted' : 'No Deal' }}</span>
            <span v-if="result.memory_note" class="deal-note">{{ result.memory_note }}</span>
            <span v-if="result.parse_error" class="deal-note warn">⚠ {{ result.parse_error }}</span>
            <span class="deal-note">AP remaining: {{ result.action_points }}</span>
          </div>
          <div style="display:flex; justify-content:flex-end; margin-top:0.6rem">
            <button class="btn-primary" @click="$emit('close')">OK</button>
          </div>
          <details style="margin-top:0.5rem">
            <summary style="font-size:0.72rem; color:var(--muted); cursor:pointer">Raw JSON</summary>
            <pre class="json-dump">{{ JSON.stringify(result, null, 2) }}</pre>
          </details>
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
      phase: 'idle',   // idle | loading-step1 | await-opening | loading-step3 | await-closing | loading-step5 | done
      step: 0,
      step1: '',
      step3: '',
      step5: '',
      mayorOpening: '',
      mayorClosing: '',
      inputText: '',
      result: null,
      fatalError: '',
    }
  },
  computed: {
    factionName() {
      return this.faction?.name || this.faction?.id || 'Faction'
    },
    concluded() {
      return this.phase === 'done'
    },
  },
  methods: {
    maybeClose() {
      if (this.phase === 'idle' || this.phase === 'done') this.$emit('close')
    },
    async begin() {
      this.fatalError = ''
      this.phase = 'loading-step1'
      try {
        const res = await mayorApi.audienceBegin(store.userId, this.faction.id)
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
        this.step5 = res.step5_narrative
        this.result = res
        this.step = 5
        this.phase = 'done'
        this.$nextTick(() => this.scrollDown())
        this.$emit('acted', res)
      } catch (e) {
        this.fatalError = e.message
        this.phase = 'await-closing'
        this.step = 3
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

.json-dump {
  font-size: 0.72rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius, 4px);
  padding: 0.5rem;
  overflow-x: auto;
  white-space: pre;
  color: var(--muted);
  margin-top: 0.35rem;
}
</style>
