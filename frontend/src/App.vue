<script setup>
import { ref } from 'vue'

// The links in the navbar. v-for in the template builds one link per item.
const links = [
  { to: '/', label: 'Dashboard', icon: 'bi-speedometer2' },
  { to: '/students', label: 'Students', icon: 'bi-people' },
  { to: '/exams', label: 'Exams', icon: 'bi-journal-text' },
  { to: '/results', label: 'Results', icon: 'bi-clipboard-data' },
]

// On small screens, the menu folds behind a button. Bootstrap's own
// JavaScript would normally do this; a ref does the same job in two lines.
const menuOpen = ref(false)

// Bootstrap 5.3 has a built-in dark theme. Setting data-bs-theme="dark" on
// the <html> element switches every Bootstrap component at once.
const dark = ref(false)
function toggleTheme() {
  dark.value = !dark.value
  document.documentElement.setAttribute('data-bs-theme', dark.value ? 'dark' : 'light')
}
</script>

<template>
  <nav class="navbar navbar-expand-md bg-body border-bottom shadow-sm sticky-top">
    <div class="container">
      <router-link class="navbar-brand fw-semibold d-flex align-items-center gap-2" to="/">
        <i class="bi bi-mortarboard-fill text-primary fs-4"></i>
        Exam Manager
      </router-link>

      <button class="navbar-toggler" type="button" aria-label="Toggle menu" @click="menuOpen = !menuOpen">
        <span class="navbar-toggler-icon"></span>
      </button>

      <!-- :class adds "show" while menuOpen is true, which unfolds the menu. -->
      <div class="collapse navbar-collapse" :class="{ show: menuOpen }">
        <div class="navbar-nav ms-auto gap-md-1">
          <!-- router-link changes the page without a full reload.
               exact-active-class highlights only the link for this page. -->
          <router-link
            v-for="link in links"
            :key="link.to"
            :to="link.to"
            class="nav-link px-3 rounded"
            exact-active-class="active bg-primary-subtle text-primary-emphasis"
            @click="menuOpen = false"
          >
            <i class="bi me-1" :class="link.icon"></i>{{ link.label }}
          </router-link>
        </div>
        <button class="btn btn-outline-secondary btn-sm ms-md-3 mt-2 mt-md-0" type="button"
                :title="dark ? 'Switch to light mode' : 'Switch to dark mode'" @click="toggleTheme">
          <i class="bi" :class="dark ? 'bi-sun' : 'bi-moon-stars'"></i>
        </button>
      </div>
    </div>
  </nav>

  <main class="container py-4">
    <!-- The router renders the view that matches the current URL here. -->
    <router-view />
  </main>
</template>

<style>
/* A light grey page behind white cards, so the cards stand out. */
body {
  background-color: var(--bs-tertiary-bg);
  min-height: 100vh;
}
</style>
