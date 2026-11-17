<script setup>
import { ref, computed, onMounted } from 'vue'
import { getExams, createExam, deleteExam, getExamStats, startReport, startNotify } from '../api.js'
import { formatDate, percent } from '../utils.js'
import TaskStatus from '../components/TaskStatus.vue'

const exams = ref([])
const loading = ref(true)
const error = ref('')
const form = ref({ title: '', subject: '', exam_date: '', max_marks: 100 })

// The stats of the exam you last clicked "Stats" on, or null.
const stats = ref(null)
const statsExam = ref(null)

// Background tasks you started from this page. Each one gets a <TaskStatus>.
const tasks = ref([])

// The share of students who passed, for the progress bar.
const passPercent = computed(() => (stats.value ? percent(stats.value.pass_count, stats.value.count) : 0))

async function loadExams() {
  try {
    exams.value = await getExams()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function addExam() {
  error.value = ''
  try {
    await createExam(form.value)
    form.value = { title: '', subject: '', exam_date: '', max_marks: 100 }
    await loadExams()
  } catch (err) {
    error.value = err.message
  }
}

async function removeExam(exam) {
  if (!confirm(`Delete ${exam.title} and all of its results?`)) return
  error.value = ''
  try {
    await deleteExam(exam.id)
    if (statsExam.value && statsExam.value.id === exam.id) stats.value = null
    await loadExams()
  } catch (err) {
    error.value = err.message
  }
}

async function showStats(exam) {
  error.value = ''
  try {
    stats.value = await getExamStats(exam.id)
    statsExam.value = exam
  } catch (err) {
    error.value = err.message
  }
}

// startJob is startReport or startNotify. Both return {task_id} at once.
async function runTask(startJob, exam, label) {
  error.value = ''
  try {
    const { task_id } = await startJob(exam.id)
    tasks.value.unshift({ id: task_id, label: `${label}: ${exam.title}` })
  } catch (err) {
    error.value = err.message
  }
}

onMounted(loadExams)
</script>

<template>
  <div class="mb-4">
    <h1 class="h3 mb-1">Exams</h1>
    <p class="text-body-secondary mb-0">Schedule exams, check their statistics, and run background jobs.</p>
  </div>

  <div v-if="error" class="alert alert-danger alert-dismissible">
    <i class="bi bi-exclamation-triangle me-2"></i>{{ error }}
    <button type="button" class="btn-close" aria-label="Close" @click="error = ''"></button>
  </div>

  <div class="card border-0 shadow-sm mb-4">
    <div class="card-body">
      <h2 class="h6 mb-3"><i class="bi bi-calendar-plus me-2"></i>Schedule an exam</h2>
      <form class="row g-3 align-items-end" @submit.prevent="addExam">
        <div class="col-md-3">
          <label class="form-label small" for="title">Title</label>
          <input id="title" v-model="form.title" class="form-control" placeholder="Mid-term" required />
        </div>
        <div class="col-md-3">
          <label class="form-label small" for="subject">Subject</label>
          <input id="subject" v-model="form.subject" class="form-control" placeholder="DBMS" required />
        </div>
        <div class="col-md-2">
          <label class="form-label small" for="date">Date</label>
          <input id="date" v-model="form.exam_date" type="date" class="form-control" required />
        </div>
        <div class="col-md-2">
          <label class="form-label small" for="max">Max marks</label>
          <!-- .number converts the typed text to a number before storing it. -->
          <input id="max" v-model.number="form.max_marks" type="number" min="1" class="form-control" required />
        </div>
        <div class="col-md-2">
          <button class="btn btn-primary w-100"><i class="bi bi-plus-lg me-1"></i>Add</button>
        </div>
      </form>
    </div>
  </div>

  <div class="row g-4">
    <div class="col-lg-8">
      <div class="card border-0 shadow-sm">
        <div class="card-header bg-body fw-semibold py-3">
          All exams <span class="badge text-bg-secondary ms-1">{{ exams.length }}</span>
        </div>

        <div v-if="loading" class="text-center py-5"><div class="spinner-border text-primary"></div></div>

        <div v-else class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead class="small text-body-secondary">
              <tr><th class="ps-3">Exam</th><th>Date</th><th>Max</th><th class="text-end pe-3">Actions</th></tr>
            </thead>
            <tbody>
              <!-- table-active highlights the exam whose stats are showing. -->
              <tr v-for="exam in exams" :key="exam.id" :class="{ 'table-active': statsExam && stats && statsExam.id === exam.id }">
                <td class="ps-3">
                  <div class="fw-medium">{{ exam.title }}</div>
                  <small class="text-body-secondary">{{ exam.subject }}</small>
                </td>
                <td class="text-nowrap">{{ formatDate(exam.exam_date) }}</td>
                <td>{{ exam.max_marks }}</td>
                <td class="text-end pe-3 text-nowrap">
                  <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" title="Show statistics" @click="showStats(exam)">
                      <i class="bi bi-bar-chart"></i>
                    </button>
                    <button class="btn btn-outline-success" title="Generate CSV report" @click="runTask(startReport, exam, 'Report')">
                      <i class="bi bi-file-earmark-spreadsheet"></i>
                    </button>
                    <button class="btn btn-outline-secondary" title="Email results to students" @click="runTask(startNotify, exam, 'Notify')">
                      <i class="bi bi-envelope"></i>
                    </button>
                    <button class="btn btn-outline-danger" title="Delete exam" @click="removeExam(exam)">
                      <i class="bi bi-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="exams.length === 0">
                <td colspan="4" class="text-center text-body-secondary py-5">
                  <i class="bi bi-journal-x fs-1 d-block mb-2"></i>No exams yet. Schedule one above.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="col-lg-4">
      <!-- Statistics panel -->
      <div class="card border-0 shadow-sm mb-4">
        <div class="card-header bg-body fw-semibold py-3 d-flex align-items-center">
          <i class="bi bi-bar-chart me-2"></i>Statistics
          <!-- "cached" is true when the backend answered from Redis instead of SQLite. -->
          <span v-if="stats" class="badge ms-auto" :class="stats.cached ? 'text-bg-success' : 'text-bg-secondary'">
            <i class="bi me-1" :class="stats.cached ? 'bi-lightning-charge' : 'bi-database'"></i>
            {{ stats.cached ? 'From Redis cache' : 'Computed from DB' }}
          </span>
        </div>
        <div v-if="stats" class="card-body">
          <p class="fw-medium mb-3">{{ statsExam.title }} · {{ statsExam.subject }}</p>
          <div class="row g-2 text-center mb-3">
            <div class="col-4"><div class="border rounded p-2"><div class="small text-body-secondary">Average</div><div class="fw-semibold">{{ stats.average }}</div></div></div>
            <div class="col-4"><div class="border rounded p-2"><div class="small text-body-secondary">Highest</div><div class="fw-semibold">{{ stats.highest }}</div></div></div>
            <div class="col-4"><div class="border rounded p-2"><div class="small text-body-secondary">Lowest</div><div class="fw-semibold">{{ stats.lowest }}</div></div></div>
          </div>
          <div class="d-flex justify-content-between small mb-1">
            <span class="text-success">{{ stats.pass_count }} passed</span>
            <span class="text-danger">{{ stats.fail_count }} failed</span>
          </div>
          <div class="progress" style="height: 10px">
            <div class="progress-bar bg-success" :style="{ width: passPercent + '%' }"></div>
            <div v-if="stats.count" class="progress-bar bg-danger" :style="{ width: 100 - passPercent + '%' }"></div>
          </div>
          <p class="small text-body-secondary mt-2 mb-0">{{ stats.count }} results · {{ passPercent }}% pass rate</p>
        </div>
        <div v-else class="card-body text-body-secondary small">
          Click <i class="bi bi-bar-chart"></i> on an exam to see its statistics. Click it again to see the Redis cache at work.
        </div>
      </div>

      <!-- Background tasks panel -->
      <div class="card border-0 shadow-sm">
        <div class="card-header bg-body fw-semibold py-3"><i class="bi bi-gear-wide-connected me-2"></i>Background tasks</div>
        <ul v-if="tasks.length > 0" class="list-group list-group-flush">
          <TaskStatus v-for="task in tasks" :key="task.id" :task-id="task.id" :label="task.label" />
        </ul>
        <div v-else class="card-body text-body-secondary small">
          Click <i class="bi bi-file-earmark-spreadsheet"></i> or <i class="bi bi-envelope"></i> to start a Celery job. It runs in the worker while the page stays responsive.
        </div>
      </div>
    </div>
  </div>
</template>
