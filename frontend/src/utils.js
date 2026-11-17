// Small display helpers that more than one view uses.

// Turns "2026-12-01" into a friendlier "1 Dec 2026".
export function formatDate(isoDate) {
  return new Date(isoDate + 'T00:00:00').toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

// Turns "Asha Verma" into "AV" for the round avatar next to a name.
export function initials(name) {
  return name
    .split(' ')
    .map((word) => word[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

// Returns marks as a percentage of the maximum, rounded to a whole number.
export function percent(marks, maxMarks) {
  return maxMarks ? Math.round((marks / maxMarks) * 100) : 0
}
