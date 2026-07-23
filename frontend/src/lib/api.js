export const API_BASE = ""

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const data = await res.json()
      detail = data.detail || JSON.stringify(data)
    } catch {
      // ignore
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail))
  }
  return res.json()
}

export function postCalculatorAction(payload) {
  return request("/api/calculator/action", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function postCandySolve(ratings) {
  return request("/api/candy/solve", {
    method: "POST",
    body: JSON.stringify({ ratings }),
  })
}

export function postConcurrency(kind, mode) {
  const path = kind === "cpu" ? "/api/concurrency/cpu" : "/api/concurrency/io"
  return request(path, {
    method: "POST",
    body: JSON.stringify({ mode }),
  })
}

export function postMainChildThread(mode) {
  return request("/api/main-child-thread/run", {
    method: "POST",
    body: JSON.stringify({ mode }),
  })
}

export function postSyncAsync(mode) {
  return request("/api/sync-async/run", {
    method: "POST",
    body: JSON.stringify({ mode }),
  })
}

export function getFileIoContent() {
  return request("/api/file-io/content")
}

export function postFileIoAppend(line) {
  return request("/api/file-io/append", {
    method: "POST",
    body: JSON.stringify(line ? { line } : {}),
  })
}

export function postFileIoReset() {
  return request("/api/file-io/reset", {
    method: "POST",
    body: JSON.stringify({}),
  })
}
