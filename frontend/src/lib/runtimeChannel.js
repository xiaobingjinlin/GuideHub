export function postUserLog(message) {
  if (window.opener && !window.opener.closed) {
    window.opener.postMessage(
      { source: 'guidehub-user', type: 'log', message },
      window.location.origin,
    )
  }
}

export function postSessionEvent(event, payload = {}) {
  if (window.opener && !window.opener.closed) {
    window.opener.postMessage(
      { source: 'guidehub-user', type: event, ...payload },
      window.location.origin,
    )
  }
}

export function buildUserPageUrl(categoryId, exampleId) {
  const url = new URL(window.location.href)
  url.searchParams.set('view', 'user')
  url.searchParams.set('category', categoryId)
  url.searchParams.set('example', exampleId)
  return url.toString()
}

export function parseUserPageParams(search = window.location.search) {
  const params = new URLSearchParams(search)
  if (params.get('view') !== 'user') return null
  return {
    categoryId: params.get('category'),
    exampleId: params.get('example'),
  }
}
