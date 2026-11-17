<script setup>
import { ref, computed, onMounted } from 'vue'
import { getStudents, getExams, getResults } from '../api.js'
import { formatDate } from '../utils.js'

// ref() creates a reactive value. When you change students.value, Vue
// re-renders every part of the template that uses it.
const students = ref([])
const exams = ref([])
const results = ref([])
const loading = ref(true)
const error = ref('')

// computed() derives a value from other reactive values and recalculates it
// automatically when they change. You never set it yourself.
const passRate = computed(() => {
  if (results.value.length === 0) return 0
  const passed = results.value.filter((r) => r.passed).length
  return Math.round((passed / results.value.length) * 100)
})

const recentResults = computed(() => results.value.slice(-5).reverse())

// The tiles at the top of the page.
const tiles = computed(() => [
  { label: 'Students', value: students.value.length, icon: 'bi-people', color: 'primary', to: '/students' },
  { label: 'Exams', value: exams.value.length, icon: 'bi-journal-text', color: 'success', to: '/exams' },
  { label: 'Results', value: results.value.length, icon: 'bi-clipboard-data', color: 'warning', to: '/results' },
  { label: 'Pass rate', value: passRate.value + '%', icon: 'bi-graph-up-arrow', color: 'info', to: '/results' },
])

// onMounted runs once, after the component appears on the page. It's the
// usual place to load data from the backend.
onMounted(async () => {
  try {
    // Promise.all sends the three requests at the same time.
    const [studentList, examList, resultList] = await Promise.all([
      getStudents(),
      getExams(),
      getResults(),
    ])
    students.value = studentList
    exams.value = examList
    results.value = resultList
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="mb-4">
    <h1 class="h3 mb-1">Dashboard</h1>
    <p class="text-body-secondary mb-0">An overview of students, exams, and results.</p>
  </div>

  <div v-if="error" class="alert alert-danger"><i class="bi bi-exclamation-triangle me-2"></i>{{ error }}</div>

  <div v-if="loading" class="text-center py-5"><div class="spinner-border text-primary"></div></div>

  <template v-else>
    <div class="row g-3 mb-4">
      <div v-for="tile in tiles" :key="tile.label" class="col-6 col-lg-3">
        <router-link :to="tile.to" class="card border-0 shadow-sm h-100 text-decoration-none">
          <div class="card-body d-flex align-items-center gap-3">
            <div class="rounded-3 p-3 fs-4 lh-1" :class="`bg-${tile.color}-subtle text-${tile.color}-emphasis`">
              <i class="bi" :class="tile.icon"></i>
            </div>
            <div>
              <div class="text-body-secondary small">{{ tile.label }}</div>
              <div class="fs-3 fw-semibold text-body">{{ tile.value }}</div>
            </div>
          </div>
        </router-link>
      </div>
    </div>

    <div class="row g-3">
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-body fw-semibold"><i class="bi bi-calendar-event me-2"></i>Exams</div>
          <ul class="list-group list-group-flush">
            <li v-for="exam in exams" :key="exam.id" class="list-group-item d-flex justify-content-between align-items-center">
              <div>
                <div class="fw-medium">{{ exam.title }}</div>
                <small class="text-body-secondary">{{ exam.subject }}</small>
              </div>
              <span class="badge bg-secondary-subtle text-secondary-emphasis">{{ formatDate(exam.exam_date) }}</span>
            </li>
            <li v-if="exams.length === 0" class="list-group-item text-body-secondary">No exams yet.</li>
          </ul>
        </div>
      </div>

      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-body fw-semibold"><i class="bi bi-clock-history me-2"></i>Recent results</div>
          <ul class="list-group list-group-flush">
            <li v-for="r in recentResults" :key="r.id" class="list-group-item d-flex justify-content-between align-items-center">
              <div>
                <div class="fw-medium">{{ r.student_name }}</div>
                <small class="text-body-secondary">{{ r.exam_title }} · {{ r.marks }} marks</small>
              </div>
              <span class="badge" :class="r.passed ? 'text-bg-success' : 'text-bg-danger'">
                {{ r.passed ? 'Pass' : 'Fail' }}
              </span>
            </li>
            <li v-if="results.length === 0" class="list-group-item text-body-secondary">No results yet.</li>
          </ul>
        </div>
      </div>
    </div>
  </template>
</template>
