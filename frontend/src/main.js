import { createApp } from 'vue'

// Import Bootstrap's CSS and its icon font once here, so every component can
// use their classes, such as "card" or "bi bi-people".
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap-icons/font/bootstrap-icons.min.css'

import App from './App.vue'
import router from './router.js'

// Create the Vue app, plug in the router, and attach it to <div id="app">
// in index.html.
createApp(App).use(router).mount('#app')
