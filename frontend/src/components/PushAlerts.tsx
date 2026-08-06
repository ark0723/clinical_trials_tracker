import { useState } from 'react'

import { getVapidPublicKey, registerPushSubscription } from '../api/client'
import { subscriptionToPayload, urlBase64ToUint8Array } from '../utils/push'

interface PushAlertsProps {
  userId: string
}

export function PushAlerts({ userId }: PushAlertsProps) {
  const [status, setStatus] = useState<string | null>(null)
  const [isBusy, setIsBusy] = useState(false)

  async function enablePush() {
    setIsBusy(true)
    setStatus(null)
    try {
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        setStatus('Browser push is not supported in this browser.')
        return
      }

      const permission = await Notification.requestPermission()
      if (permission !== 'granted') {
        setStatus('Notification permission was not granted.')
        return
      }

      const registration = await navigator.serviceWorker.register('/sw.js')
      await navigator.serviceWorker.ready

      const { public_key } = await getVapidPublicKey()
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(public_key),
      })

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

  return (
    <div className="push-alerts">
      <p className="section-intro">
        Enable browser notifications to learn when a saved trial changes status
        (connected to sync change detection).
      </p>
      <button
        type="button"
        className="button-secondary"
        onClick={() => void enablePush()}
        disabled={isBusy}
      >
        {isBusy ? 'Enabling…' : 'Enable browser push'}
      </button>
      {status ? <p className="status-message">{status}</p> : null}
    </div>
  )
}
