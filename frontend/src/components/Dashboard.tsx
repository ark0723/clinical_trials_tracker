import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { createProfile, getMatches, updateProfile } from '../api/client'
import type { UserProfileCreate } from '../api/types'
import { MatchResults } from './MatchResults'
import { ProfileForm } from './ProfileForm'

const USER_ID_KEY = 'clinical_tracker_user_id'

function readStoredUserId(): string | null {
  return localStorage.getItem(USER_ID_KEY)
}

function storeUserId(userId: string) {
  localStorage.setItem(USER_ID_KEY, userId)
}

export function Dashboard() {
  const queryClient = useQueryClient()
  const [userId, setUserId] = useState<string | null>(() => readStoredUserId())
  const [isEditingProfile, setIsEditingProfile] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const matchesQuery = useQuery({
    queryKey: ['matches', userId],
    queryFn: () => getMatches(userId!),
    enabled: Boolean(userId) && !isEditingProfile,
  })

  const saveProfileMutation = useMutation({
    mutationFn: async (payload: UserProfileCreate) => {
      if (userId) {
        return updateProfile(userId, payload)
      }
      return createProfile(payload)
    },
    onSuccess: (profile) => {
      storeUserId(profile.id)
      setUserId(profile.id)
      setIsEditingProfile(false)
      setFormError(null)
      queryClient.invalidateQueries({ queryKey: ['matches', profile.id] })
    },
    onError: (error: Error) => {
      setFormError(error.message)
    },
  })

  const showProfileForm = !userId || isEditingProfile

  return (
    <div className="dashboard">
      <section className="dashboard__section">
        <header className="section-header">
          <h2>Your health profile</h2>
          {userId && !isEditingProfile ? (
            <button
              type="button"
              className="button-secondary"
              onClick={() => setIsEditingProfile(true)}
            >
              Edit profile
            </button>
          ) : null}
        </header>

        {showProfileForm ? (
          <>
            <p className="section-intro">
              Enter your health details to find HER2+ breast cancer trials that
              may fit your situation. This information is encrypted on the server.
            </p>
            {formError ? (
              <p className="status-message status-message--error" role="alert">
                {formError}
              </p>
            ) : null}
            <ProfileForm
              onSubmit={async (payload) => {
                await saveProfileMutation.mutateAsync(payload)
              }}
              isSubmitting={saveProfileMutation.isPending}
            />
          </>
        ) : (
          <p className="section-intro">
            Profile saved. Review recommended trials below or edit your profile
            to refresh matches.
          </p>
        )}
      </section>

      {userId && !isEditingProfile ? (
        <section className="dashboard__section">
          <header className="section-header">
            <h2>Recommended trials</h2>
          </header>
          <p className="section-intro">
            Matches are ranked by compatibility, then nearer sites. Trials beyond
            your max travel distance are hidden when site coordinates are known.
          </p>
          <MatchResults
            matches={matchesQuery.data?.matches ?? []}
            isLoading={matchesQuery.isLoading}
            error={matchesQuery.error}
          />
        </section>
      ) : null}
    </div>
  )
}
