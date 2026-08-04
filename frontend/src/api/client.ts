import type {
  MatchesResponse,
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
      ...options?.headers,
    },
  })

  if (!response.ok) {
    throw new Error(await parseError(response))
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
