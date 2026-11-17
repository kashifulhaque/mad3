<script setup>
import { ref, computed, onMounted } from 'vue'
import { getStudents, getExams, getResults, createResult } from '../api.js'
import { percent } from '../utils.js'

const students = ref([])
const exams = ref([])
const results = ref([])
const loading = ref(true)
const error = ref('')

const form = ref({ student_id: '', exam_id: '', marks: '' })

// The exam chosen in the filter dropdown. An empty string means "all exams".
const filterExamId = ref('')

// The exam picked in the form, so the marks box can show its maximum.
const selectedExam = computed(() => exams.value.find((e) => e.id === form.value.exam_id))

// Looks up an exam's maximum marks, to show each result as "72.5 / 100".
function maxMarksFor(examId) {
  const exam = exams.value.find((e) => e.id === examId)
  return exam ? exam.max_marks : 0
}

async function loadResults() {
  try {
    results.value = await getResults(filterExamId.value)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function addResult() {
  error.value = ''
  try {
    await createResult(form.value)
    form.value = { student_id: '', exam_id: '', marks: '' }
    await loadResults()
  } catch (err) {
    error.value = err.message
  }
}

onMounted(async () => {
  try {
    // The dropdowns need the lists of students and exams.
    students.value = await getStudents()
    exams.value = await getExams()
    await loadResults()
  } catch (err) {
    error.value = err.message
  }
})
</script>

<template>
  <div class="mb-4">
    <h1 class="h3 mb-1">Results</h1>
    <p class="text-body-secondary mb-0">Record marks. A student passes with at least 40% of the maximum marks.</p>
  </div>

  <div v-if="error" class="alert alert-danger alert-dismissible">
    <i class="bi bi-exclamation-triangle me-2"></i>{{ error }}
    <button type="button" class="btn-close" aria-label="Close" @click="error = ''"></button>
  </div>

  <div class="card border-0 shadow-sm mb-4">
    <div class="card-body">
      <h2 class="h6 mb-3"><i class="bi bi-pencil-square me-2"></i>Record a result</h2>
      <form class="row g-3 align-items-end" @submit.prevent="addResult">
        <div class="col-md-4">
          <label class="form-label small" for="student">Student</label>
          <!-- v-model.number stores the selected ID as a number, not a string. -->
          <select id="student" v-model.number="form.student_id" class="form-select" required>
            <option value="" disabled>Choose a student</option>
            <option v-for="s in students" :key="s.id" :value="s.id">{{ s.name }} ({{ s.roll_no }})</option>
          </select>
        </div>
        <div class="col-md-4">
          <label class="form-label small" for="exam">Exam</label>
          <select id="exam" v-model.number="form.exam_id" class="form-select" required>
            <option value="" disabled>Choose an exam</option>
            <option v-for="e in exams" :key="e.id" :value="e.id">{{ e.title }} ({{ e.subject }})</option>
          </select>
        </div>
        <div class="col-md-2">
          <label class="form-label small" for="marks">Marks</label>
          <div class="input-group">
            <input id="marks" v-model.number="form.marks" type="number" step="0.5" min="0"
                   :max="selectedExam ? selectedExam.max_marks : null" class="form-control" required />
            <span v-if="selectedExam" class="input-group-text">/ {{ selectedExam.max_marks }}</span>
          </div>
        </div>
        <div class="col-md-2">
          <button class="btn btn-primary w-100"><i class="bi bi-plus-lg me-1"></i>Add</button>
        </div>
      </form>
    </div>
  </div>

  <div class="card border-0 shadow-sm">
    <div class="card-header bg-body d-flex flex-wrap gap-2 justify-content-between align-items-center py-3">
      <span class="fw-semibold">All results <span class="badge text-bg-secondary ms-1">{{ results.length }}</span></span>
      <div class="d-flex align-items-center gap-2">
        <label class="small text-body-secondary text-nowrap" for="filter"><i class="bi bi-funnel me-1"></i>Exam</label>
        <!-- @change reloads the table whenever you pick a different exam. -->
        <select id="filter" v-model="filterExamId" class="form-select form-select-sm" @change="loadResults">
          <option value="">All exams</option>
          <option v-for="e in exams" :key="e.id" :value="e.id">{{ e.title }}</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="text-center py-5"><div class="spinner-border text-primary"></div></div>

    <div v-else class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead class="small text-body-secondary">
          <tr><th class="ps-3">Student</th><th>Exam</th><th style="width: 30%">Marks</th><th class="pe-3">Status</th></tr>
        </thead>
        <tbody>
          <tr v-for="r in results" :key="r.id">
            <td class="ps-3 fw-medium">{{ r.student_name }}</td>
            <td>{{ r.exam_title }}</td>
            <td>
              <div class="d-flex align-items-center gap-2">
                <span class="text-nowrap small" style="min-width: 4.5rem">{{ r.marks }} / {{ maxMarksFor(r.exam_id) }}</span>
                <div class="progress flex-grow-1" style="height: 6px">
                  <div class="progress-bar" :class="r.passed ? 'bg-success' : 'bg-danger'"
                       :style="{ width: percent(r.marks, maxMarksFor(r.exam_id)) + '%' }"></div>
                </div>
              </div>
            </td>
            <td class="pe-3">
              <span v-if="r.passed" class="badge bg-success-subtle text-success-emphasis"><i class="bi bi-check-lg me-1"></i>Pass</span>
              <span v-else class="badge bg-danger-subtle text-danger-emphasis"><i class="bi bi-x-lg me-1"></i>Fail</span>
            </td>
          </tr>
          <tr v-if="results.length === 0">
            <td colspan="4" class="text-center text-body-secondary py-5">
              <i class="bi bi-clipboard-x fs-1 d-block mb-2"></i>No results yet.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
