import { createRouter, createWebHashHistory } from 'vue-router'
import { auth } from './api.js'

import TitleView     from './views/TitleView.vue'
import GameView      from './views/GameView.vue'
import LoginView     from './views/LoginView.vue'
import HomeView      from './views/HomeView.vue'
import BuilderView   from './views/BuilderView.vue'
import DashboardView from './views/DashboardView.vue'

const routes = [
  { path: '/',          component: TitleView },
  { path: '/game',      component: GameView,      meta: { requiresAuth: true } },
  { path: '/login',     component: LoginView },
  { path: '/home',      component: HomeView,      meta: { requiresAuth: true } },
  { path: '/builder',   component: BuilderView,   meta: { requiresAuth: true } },
  { path: '/dashboard', component: DashboardView, meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !auth.getToken()) {
    return '/'
  }
})

export default router
