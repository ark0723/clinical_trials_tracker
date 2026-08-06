import { useEffect, useState } from 'react'

import {
  getVapidPublicKey,
  registerPushSubscription,
  sendTestPush,
} from '../api/client'
import { subscriptionToPayload, urlBase64ToUint8Array } from '../utils/push'

interface PushAlertsProps {
  userId: string
}

let cachedVapidPublicKey: string | null = null
let vapidPublicKeyPromise: Promise<string> | null = null
let serviceWorkerReadyPromise: Promise<ServiceWorkerRegistration> | null = null

function prefetchVapidPublicKey(): Promise<string> {
  if (cachedVapidPublicKey) {
    return Promise.resolve(cachedVapidPublicKey)
  }
  if (!vapidPublicKeyPromise) {
    vapidPublicKeyPromise = getVapidPublicKey()
      .then(({ public_key }) => {
        cachedVapidPublicKey = public_key
        return public_key
      })
      .catch((error) => {
        vapidPublicKeyPromise = null
        throw error
      })
  }
  return vapidPublicKeyPromise
}

function ensureServiceWorker(): Promise<ServiceWorkerRegistration> {
  if (!('serviceWorker' in navigator)) {
    return Promise.reject(new Error('Service workers are not supported.'))
  }
  if (!serviceWorkerReadyPromise) {
    serviceWorkerReadyPromise = navigator.serviceWorker
      .register('/sw.js')
      .then(() => navigator.serviceWorker.ready)
      .catch((error) => {
        serviceWorkerReadyPromise = null
        throw error
      })
  }
  return serviceWorkerReadyPromise
}

export function PushAlerts({ userId }: PushAlertsProps) {
  const [status, setStatus] = useState<string | null>(null)
  const [isBusy, setIsBusy] = useState(false)

  useEffect(() => {
    // Warm the slow parts before the user clicks Enable.
    void prefetchVapidPublicKey().catch(() => undefined)
    if ('serviceWorker' in navigator) {
      void ensureServiceWorker().catch(() => undefined)
    }
  }, [])

  async function enablePush() {
    setIsBusy(true)
    setStatus('Preparing browser push…')
    try {
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        setStatus('Browser push is not supported in this browser.')
        return
      }

      setStatus('Waiting for notification permission…')
      const permission = await Notification.requestPermission()
      if (permission !== 'granted') {
        setStatus('Notification permission was not granted.')
        return
      }

      setStatus('Finishing subscription…')
      const [publicKey, registration] = await Promise.all([
        prefetchVapidPublicKey(),
        ensureServiceWorker(),
      ])

      const existing = await registration.pushManager.getSubscription()
      const subscription =
        existing ??
        (await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(publicKey),
        }))

      setStatus('Saving subscription…')
      await registerPushSubscription(userId, subscriptionToPayload(subscription))
      setStatus('Browser push enabled for saved-trial updates.')
    } catch (error) {
      setStatus(
        error instanceof Error
          ? error.message
          : 'Could not enable browser push. Check VAPID keys on the server.',
      )
    } finally {
      setIsBusy(false)
    }
  }

  async function testPush() {
    setIsBusy(true)
    setStatus(null)
    try {
      const result = await sendTestPush(userId)
      setStatus(`Test notification sent (${result.sent}). Check this device.`)
    } catch (error) {
      setStatus(
        error instanceof Error
          ? error.message
          : 'Could not send test notification.',
      )
    } finally {
      setIsBusy(false)
    }
  }

  return (
    <div className="push-alerts">
      <p className="section-intro">
        Enable browser notifications to learn when a saved trial changes status
        after sync detects an update. Use Send test notification to verify this
        device without waiting for a trial change.
      </p>
      <div className="push-alerts__actions">
        <button
          type="button"
          className="button-secondary"
          onClick={() => void enablePush()}
          disabled={isBusy}
        >
          {isBusy ? 'Working…' : 'Enable browser push'}
        </button>
        <button
          type="button"
          className="button-secondary"
          onClick={() => void testPush()}
          disabled={isBusy}
        >
          Send test notification
        </button>
      </div>
      {status ? <p className="status-message">{status}</p> : null}
    </div>
  )
}
