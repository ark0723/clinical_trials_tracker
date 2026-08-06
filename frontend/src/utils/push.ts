export function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const raw = atob(base64)
  const output = new Uint8Array(raw.length)
  for (let i = 0; i < raw.length; i += 1) {
    output[i] = raw.charCodeAt(i)
  }
  return output
}

export function subscriptionToPayload(subscription: PushSubscription): {
  endpoint: string
  p256dh: string
  auth: string
} {
  const json = subscription.toJSON()
  const keys = json.keys
  if (!json.endpoint || !keys?.p256dh || !keys?.auth) {
    throw new Error('Push subscription is missing required keys')
  }
  return {
    endpoint: json.endpoint,
    p256dh: keys.p256dh,
    auth: keys.auth,
  }
}
