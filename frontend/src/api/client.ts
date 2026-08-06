import type {
  MatchesResponse,
  SavedTrial,
  UserProfile,
  UserProfileCreate,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string }
    if (typeof body.detail === 'string') {
      return body.detail
    }
  } catch {
    // ignore JSON parse errors
  }
  return response.statusText || 'Request failed'
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      // Free ngrok interstitial otherwise blocks browser fetch to the API.
      ...(API_BASE.includes('ngrok')
        ? { 'ngrok-skip-browser-warning': 'true' }
        : {}),
      ...options?.headers,
    },
  })

  if (!response.ok) {
    throw new Error(await parseError(response))
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export function createProfile(payload: UserProfileCreate): Promise<UserProfile> {
  return request<UserProfile>('/api/users/profile', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getProfile(userId: string): Promise<UserProfile> {
  return request<UserProfile>(`/api/users/profile/${userId}`)
}

export function updateProfile(
  userId: string,
  payload: UserProfileCreate,
): Promise<UserProfile> {
  return request<UserProfile>(`/api/users/profile/${userId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function getMatches(
  userId: string,
  limit = 10,
): Promise<MatchesResponse> {
  return request<MatchesResponse>(
    `/api/matches/${userId}?limit=${limit}`,
  )
}

export function saveTrial(userId: string, nctId: string): Promise<SavedTrial> {
  return request<SavedTrial>(`/api/users/${userId}/saved-trials`, {
    method: 'POST',
    body: JSON.stringify({ nct_id: nctId }),
  })
}

export function listSavedTrials(
  userId: string,
): Promise<{ saved_trials: SavedTrial[] }> {
  return request<{ saved_trials: SavedTrial[] }>(
    `/api/users/${userId}/saved-trials`,
  )
}

export function unsaveTrial(userId: string, nctId: string): Promise<void> {
  return request<void>(`/api/users/${userId}/saved-trials/${nctId}`, {
    method: 'DELETE',
  })
}

export function getVapidPublicKey(): Promise<{ public_key: string }> {
  return request<{ public_key: string }>('/api/notifications/vapid-public-key')
}

export function registerPushSubscription(
  userId: string,
  subscription: { endpoint: string; p256dh: string; auth: string },
): Promise<{ endpoint: string; created_at: string }> {
  return request(`/api/notifications/users/${userId}/subscriptions`, {
    method: 'POST',
    body: JSON.stringify(subscription),
  })
}
