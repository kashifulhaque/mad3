<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getTask, reportUrl } from '../api.js'

// props are inputs from the parent component, for example:
// <TaskStatus :task-id="id" label="Report: Mid-term" />
const props = defineProps({
  taskId: { type: String, required: true },
  label: { type: String, default: 'Background task' },
})

const task = ref({ state: 'PENDING', result: null })
const error = ref('')
let timer = null

// A Celery job runs in a separate worker process, so the backend can't send
// you the answer straight away. Instead you ask "is it done yet?" once every
// second (polling) until the state is SUCCESS or FAILURE.
async function checkTask() {
  try {
    task.value = await getTask(props.taskId)
    if (task.value.state === 'SUCCESS' || task.value.state === 'FAILURE') {
      clearInterval(timer)
    }
  } catch (err) {
    error.value = err.message
    clearInterval(timer)
  }
}

onMounted(() => {
  checkTask()
  timer = setInterval(checkTask, 1000)
})

// Stop polling if you leave the page before the task finishes.
onUnmounted(() => clearInterval(timer))

// The badge color for each Celery state.
const badgeClass = {
  PENDING: 'text-bg-secondary',
  STARTED: 'text-bg-primary',
  SUCCESS: 'text-bg-success',
  FAILURE: 'text-bg-danger',
}
</script>

<template>
  <li class="list-group-item">
    <div class="d-flex align-items-center gap-2">
      <span v-if="task.state === 'PENDING' || task.state === 'STARTED'"
            class="spinner-border spinner-border-sm text-primary"></span>
      <i v-else-if="task.state === 'SUCCESS'" class="bi bi-check-circle-fill text-success"></i>
      <i v-else class="bi bi-x-circle-fill text-danger"></i>

      <span class="fw-medium">{{ label }}</span>
      <span class="badge ms-auto" :class="badgeClass[task.state] || 'text-bg-secondary'">{{ task.state }}</span>
    </div>

    <div class="d-flex align-items-center gap-2 mt-1 small">
      <!-- Report task: the result holds the CSV filename to download. -->
      <a v-if="task.state === 'SUCCESS' && task.result && task.result.filename"
         :href="reportUrl(task.result.filename)" class="link-success">
        <i class="bi bi-download me-1"></i>{{ task.result.filename }}
      </a>

      <!-- Notify task: the result holds how many students got a message. -->
      <span v-if="task.state === 'SUCCESS' && task.result && task.result.notified !== undefined" class="text-success">
        <i class="bi bi-envelope-check me-1"></i>Notified {{ task.result.notified }} students
      </span>

      <span v-if="task.state === 'FAILURE' && task.result" class="text-danger">{{ task.result.error }}</span>
      <span v-if="error" class="text-danger">{{ error }}</span>
      <code class="text-body-secondary ms-auto" :title="taskId">{{ taskId.slice(0, 8) }}</code>
    </div>
  </li>
</template>
