import { useState } from 'react'

import {
  getVapidPublicKey,
  registerPushSubscription,
  sendTestPush,
} from '../api/client'
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
        (connected to sync change detection).
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
