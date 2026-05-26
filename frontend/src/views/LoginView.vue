<template>
  <div class="login-wrap">
    <div class="login-box">
      <h1>Polis</h1>
      <p class="sub">GM Interface</p>

      <div class="login-tabs">
        <button :class="{ active: tab === 'login' }" @click="tab = 'login'">Login</button>
        <button :class="{ active: tab === 'register' }" @click="tab = 'register'">Register</button>
      </div>

      <form @submit.prevent="submit">
        <div class="field">
          <label>Username</label>
          <input v-model="username" type="text" autocomplete="username" required />
        </div>
        <div class="field">
          <label>Password</label>
          <input v-model="password" type="password" autocomplete="current-password" required />
        </div>
        <div v-if="tab === 'register'" class="field">
          <label>Email <span class="muted">(optional)</span></label>
          <input v-model="email" type="email" />
        </div>

        <button type="submit" class="btn-primary" style="width:100%" :disabled="loading">
          {{ loading ? 'Please wait…' : (tab === 'login' ? 'Login' : 'Create account') }}
        </button>
        <p v-if="error" class="error-msg">{{ error }}</p>
      </form>
    </div>
  </div>
</template>

<script>
import { auth } from '../api.js'
import { store } from '../store.js'

export default {
  name: 'LoginView',
  data() {
    return {
      tab: 'login',
      username: '',
      password: '',
      email: '',
      loading: false,
      error: '',
    }
  },
  methods: {
    async submit() {
      this.error = ''
      this.loading = true
      try {
        let res
        if (this.tab === 'login') {
          res = await auth.login(this.username, this.password)
        } else {
          res = await auth.register(this.username, this.password, this.email || undefined)
        }
        auth.setToken(res.access_token)
        // Decode user_id from JWT payload (middle segment)
        const payload = JSON.parse(atob(res.access_token.split('.')[1]))
        store.setUser(payload.sub, this.username)
        this.$router.push('/home')
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
  },
}
</script>
