/* Clinical Trial Navigator — Web Push service worker */
self.addEventListener('push', (event) => {
  let payload = { title: 'Clinical Trial Navigator', body: 'A saved trial was updated.', data: {} }
  try {
    if (event.data) {
      payload = { ...payload, ...event.data.json() }
    }
  } catch {
    // keep defaults
  }
  event.waitUntil(
    self.registration.showNotification(payload.title, {
      body: payload.body,
      data: payload.data,
    }),
  )
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  event.waitUntil(clients.openWindow('/'))
})
