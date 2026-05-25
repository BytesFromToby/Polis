<template>
  <div class="faction-form">
    <div class="field">
      <label>Name</label>
      <input v-model="form.name" required placeholder="Faction name" />
    </div>

    <div class="field">
      <label>Description <span class="muted">(optional)</span></label>
      <textarea v-model="form.description" rows="2" placeholder="Faction notes…"></textarea>
    </div>

    <div style="display:flex; gap:0.75rem">
      <div class="col field">
        <label>Primary Domain</label>
        <select v-model="form.domain_primary" required>
          <option value="">— Select domain —</option>
          <option v-for="d in DOMAINS" :key="d.id" :value="d.id">{{ d.name }}</option>
        </select>
      </div>
      <div style="width:90px" class="field">
        <label>Rating (1–6)</label>
        <input v-model.number="form.rating" type="number" min="1" max="6" step="1" />
      </div>
    </div>

    <!-- Traits -->
    <div style="margin-bottom:0.75rem">
      <label style="margin-bottom:0.4rem; display:block">Traits</label>
      <div style="display:flex; flex-wrap:wrap; gap:0.4rem">
        <label v-for="t in FACTION_TRAITS" :key="t"
               style="display:flex; align-items:center; gap:0.3rem; cursor:pointer;
                      background:var(--bg); border:1px solid var(--border);
                      border-radius:var(--radius); padding:0.2rem 0.5rem; font-size:0.8rem"
               :style="form.traits.includes(t) ? 'border-color:var(--accent); color:var(--accent)' : ''">
          <input type="checkbox" :value="t" v-model="form.traits" style="width:auto" />
          {{ t }}
        </label>
      </div>
    </div>

    <div style="display:flex; gap:0.5rem; justify-content:flex-end; margin-top:1rem">
      <button type="button" class="btn-subtle btn-sm" @click="$emit('cancel')">Cancel</button>
      <button type="button" class="btn-primary btn-sm" @click="submit"
              :disabled="!isValid">{{ submitLabel }}</button>
    </div>
  </div>
</template>

<script>
import { DOMAINS, FACTION_TRAITS } from '../constants.js'

export default {
  name: 'FactionForm',
  emits: ['submit', 'cancel'],
  props: {
    initial: { type: Object, default: null },
    submitLabel: { type: String, default: 'Save' },
  },
  data() {
    const base = this.initial || {}
    return {
      DOMAINS,
      FACTION_TRAITS,
      form: {
        name:           base.name           || '',
        description:    base.description    || '',
        domain_primary: base.domain_primary || '',
        rating:         base.rating         || 3,
        traits:         [...(base.traits    || [])],
      },
    }
  },
  computed: {
    isValid() {
      return this.form.name.trim() &&
             this.form.domain_primary &&
             this.form.rating >= 1 &&
             this.form.rating <= 6
    },
  },
  methods: {
    submit() {
      if (!this.isValid) return
      this.$emit('submit', {
        name:           this.form.name.trim(),
        description:    this.form.description.trim(),
        domain_primary: this.form.domain_primary,
        rating:         Math.round(this.form.rating),
        traits:         this.form.traits,
      })
    },
  },
}
</script>

<style scoped>
textarea { resize: vertical; }
</style>
