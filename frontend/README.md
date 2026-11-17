# Examination Management System: frontend

A Vue 3 single-page app that talks to the Flask backend described in
`../API_CONTRACT.md`.

## Run it

```sh
npm install
npm run dev
```

Open http://localhost:5173. The app expects the backend at
`http://127.0.0.1:5000/api`. To use another address, create a `.env` file:

```sh
VITE_API_URL=http://localhost:8000/api
```

## Where things live

- `src/api.js`: every backend call, wrapped as a named function.
- `src/utils.js`: small display helpers for dates, initials, and percentages.
- `src/router.js`: maps each URL to a page.
- `src/App.vue`: the navigation bar and the `<router-view>` that shows the page.
- `src/views/`: one file per page (dashboard, students, exams, results).
- `src/components/TaskStatus.vue`: polls a Celery background task until it finishes.
