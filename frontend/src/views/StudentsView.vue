<script setup>
import { ref, computed, onMounted } from 'vue'
import { getStudents, createStudent, deleteStudent } from '../api.js'
import { initials } from '../utils.js'

const students = ref([])
const loading = ref(true)
const error = ref('')
const search = ref('')

// v-model in the template keeps these fields in sync with the input boxes.
const form = ref({ name: '', roll_no: '', email: '' })

// computed() recalculates the filtered list whenever you type in the search
// box or the student list changes. Filtering happens in the browser, so it
// needs no extra request to the backend.
const filteredStudents = computed(() => {
  const term = search.value.toLowerCase()
  return students.value.filter((s) =>
    [s.name, s.roll_no, s.email].some((field) => field.toLowerCase().includes(term)),
  )
})

async function loadStudents() {
  try {
    students.value = await getStudents()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function addStudent() {
  error.value = ''
  try {
    await createStudent(form.value)
    form.value = { name: '', roll_no: '', email: '' }
    await loadStudents()
  } catch (err) {
    error.value = err.message
  }
}

async function removeStudent(student) {
  if (!confirm(`Delete ${student.name} and all of their results?`)) return
  error.value = ''
  try {
    await deleteStudent(student.id)
    await loadStudents()
  } catch (err) {
    error.value = err.message
  }
}

onMounted(loadStudents)
</script>

<template>
  <div class="mb-4">
    <h1 class="h3 mb-1">Students</h1>
    <p class="text-body-secondary mb-0">Register students so you can record their exam results.</p>
  </div>

  <div v-if="error" class="alert alert-danger alert-dismissible">
    <i class="bi bi-exclamation-triangle me-2"></i>{{ error }}
    <button type="button" class="btn-close" aria-label="Close" @click="error = ''"></button>
  </div>

  <div class="card border-0 shadow-sm mb-4">
    <div class="card-body">
      <h2 class="h6 mb-3"><i class="bi bi-person-plus me-2"></i>Add a student</h2>
      <!-- .prevent stops the browser from reloading the page on submit. -->
      <form class="row g-3 align-items-end" @submit.prevent="addStudent">
        <div class="col-md-4">
          <label class="form-label small" for="name">Full name</label>
          <input id="name" v-model="form.name" class="form-control" placeholder="Asha Verma" required />
        </div>
        <div class="col-md-3">
          <label class="form-label small" for="roll">Roll number</label>
          <input id="roll" v-model="form.roll_no" class="form-control" placeholder="CS007" required />
        </div>
        <div class="col-md-3">
          <label class="form-label small" for="email">Email</label>
          <input id="email" v-model="form.email" type="email" class="form-control" placeholder="name@college.edu" required />
        </div>
        <div class="col-md-2">
          <button class="btn btn-primary w-100"><i class="bi bi-plus-lg me-1"></i>Add</button>
        </div>
      </form>
    </div>
  </div>

  <div class="card border-0 shadow-sm">
    <div class="card-header bg-body d-flex flex-wrap gap-2 justify-content-between align-items-center py-3">
      <span class="fw-semibold">All students <span class="badge text-bg-secondary ms-1">{{ students.length }}</span></span>
      <div class="input-group input-group-sm" style="max-width: 260px">
        <span class="input-group-text"><i class="bi bi-search"></i></span>
        <input v-model="search" class="form-control" placeholder="Search name, roll, or email" />
      </div>
    </div>

    <div v-if="loading" class="text-center py-5"><div class="spinner-border text-primary"></div></div>

    <div v-else class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead class="small text-body-secondary">
          <tr><th class="ps-3">Student</th><th>Roll number</th><th>Email</th><th></th></tr>
        </thead>
        <tbody>
          <!-- :key gives Vue a stable ID for each row so it can update rows efficiently. -->
          <tr v-for="student in filteredStudents" :key="student.id">
            <td class="ps-3">
              <div class="d-flex align-items-center gap-2">
                <span class="rounded-circle bg-primary-subtle text-primary-emphasis fw-semibold small d-inline-flex align-items-center justify-content-center"
                      style="width: 36px; height: 36px">{{ initials(student.name) }}</span>
                {{ student.name }}
              </div>
            </td>
            <td><code>{{ student.roll_no }}</code></td>
            <td class="text-body-secondary">{{ student.email }}</td>
            <td class="text-end pe-3">
              <button class="btn btn-sm btn-outline-danger" title="Delete student" @click="removeStudent(student)">
                <i class="bi bi-trash"></i>
              </button>
            </td>
          </tr>
          <tr v-if="filteredStudents.length === 0">
            <td colspan="4" class="text-center text-body-secondary py-5">
              <i class="bi bi-people fs-1 d-block mb-2"></i>
              {{ students.length === 0 ? 'No students yet. Add one above.' : 'No students match your search.' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
