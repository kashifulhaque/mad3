import { createRouter, createWebHistory } from 'vue-router'

import DashboardView from './views/DashboardView.vue'
import StudentsView from './views/StudentsView.vue'
import ExamsView from './views/ExamsView.vue'
import ResultsView from './views/ResultsView.vue'

// Each route maps a URL path to the view that <router-view> in App.vue shows.
// The browser doesn't reload the page when you switch routes; Vue swaps the
// component instead, which is what makes this a single-page app (SPA).
const routes = [
  { path: '/', component: DashboardView },
  { path: '/students', component: StudentsView },
  { path: '/exams', component: ExamsView },
  { path: '/results', component: ResultsView },
]

export default createRouter({
  // createWebHistory gives clean URLs such as /students instead of /#/students.
  history: createWebHistory(),
  routes,
})
