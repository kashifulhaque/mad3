// All communication with the Flask backend goes through this one file.
// Views call these named functions instead of calling fetch() directly, so if
// a URL changes you fix it here once, and the views stay short and readable.

// Vite exposes variables that start with VITE_ through import.meta.env.
// To point the app at another server, set VITE_API_URL in a .env file.
export const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000/api'

// Sends one HTTP request and returns the parsed JSON body.
// If the backend replies with an error status, this throws an Error that
// carries the backend's {"error": "..."} message, so views can show it.
async function request(path, method = 'GET', body = null) {
  const options = { method, headers: {} }
  if (body !== null) {
    options.headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(body)
  }

  const response = await fetch(BASE_URL + path, options)

  // 204 No Content (for example, after a DELETE) has no body to parse.
  if (response.status === 204) {
    return null
  }

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const message = data && data.error ? data.error : `Request failed (${response.status})`
    throw new Error(message)
  }
  return data
}

// Students
export const getStudents = () => request('/students')
export const createStudent = (student) => request('/students', 'POST', student)
export const deleteStudent = (id) => request(`/students/${id}`, 'DELETE')

// Exams
export const getExams = () => request('/exams')
export const createExam = (exam) => request('/exams', 'POST', exam)
export const deleteExam = (id) => request(`/exams/${id}`, 'DELETE')

// Results. Pass an exam ID to get only that exam's results.
export const getResults = (examId) =>
  request(examId ? `/results?exam_id=${examId}` : '/results')
export const createResult = (result) => request('/results', 'POST', result)

// Stats. The backend caches these in Redis and sets "cached" to true when the
// answer comes from the cache.
export const getExamStats = (examId) => request(`/exams/${examId}/stats`)

// Background jobs. These return {task_id} immediately; the work runs later in
// a Celery worker. Poll getTask() to find out when it finishes.
export const startReport = (examId) => request(`/exams/${examId}/report`, 'POST')
export const startNotify = (examId) => request(`/exams/${examId}/notify`, 'POST')
export const getTask = (taskId) => request(`/tasks/${taskId}`)

// Returns the download link for a generated CSV report. This is a plain URL
// for an <a href>, not a fetch call, because the browser downloads the file.
export const reportUrl = (filename) => `${BASE_URL}/reports/${encodeURIComponent(filename)}`
