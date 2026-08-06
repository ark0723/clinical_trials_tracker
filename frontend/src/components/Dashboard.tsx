import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import {
  createProfile,
  getMatches,
  getProfile,
  listSavedTrials,
  updateProfile,
} from '../api/client'
import type { TrialStatus, UserProfileCreate } from '../api/types'
import { MatchResults } from './MatchResults'
import { ProfileForm } from './ProfileForm'
import { ProfileSummary } from './ProfileSummary'
import { PushAlerts } from './PushAlerts'
import { PATIENT_DEFAULT_STATUSES, StatusFilter } from './StatusFilter'

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
  const [statusFilter, setStatusFilter] = useState<TrialStatus[]>([
    ...PATIENT_DEFAULT_STATUSES,
  ])

  const profileQuery = useQuery({
    queryKey: ['profile', userId],
    queryFn: () => getProfile(userId!),
    enabled: Boolean(userId),
  })

  const matchesQuery = useQuery({
    queryKey: ['matches', userId, statusFilter],
    queryFn: () => getMatches(userId!, 10, statusFilter),
    enabled: Boolean(userId) && !isEditingProfile,
  })

  const savedTrialsQuery = useQuery({
    queryKey: ['saved-trials', userId],
    queryFn: () => listSavedTrials(userId!),
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
      queryClient.setQueryData(['profile', profile.id], profile)
      void queryClient.invalidateQueries({ queryKey: ['profile', profile.id] })
      void queryClient.invalidateQueries({ queryKey: ['matches', profile.id] })
      void queryClient.invalidateQueries({ queryKey: ['saved-trials', profile.id] })
    },
    onError: (error: Error) => {
      setFormError(error.message)
    },
  })

  const showCreateForm = !userId
  const showEditForm = Boolean(userId) && isEditingProfile
  const showSummary =
    Boolean(userId) && !isEditingProfile && Boolean(profileQuery.data)

  return (
    <div className="dashboard">
      <section className="dashboard__section">
        <header className="section-header">
          <h2>{showSummary ? 'Your profile' : 'Your health profile'}</h2>
        </header>

        {showCreateForm ? (
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
        ) : null}

        {showEditForm ? (
          <>
            <p className="section-intro">
              Update your health details. Changes refresh your recommended trials.
            </p>
            {formError ? (
              <p className="status-message status-message--error" role="alert">
                {formError}
              </p>
            ) : null}
            {profileQuery.isLoading ? (
              <p className="status-message">Loading your profile…</p>
            ) : profileQuery.error ? (
              <p className="status-message status-message--error" role="alert">
                {profileQuery.error.message}
              </p>
            ) : profileQuery.data ? (
              <ProfileForm
                key={profileQuery.data.id}
                initialProfile={profileQuery.data}
                onSubmit={async (payload) => {
                  await saveProfileMutation.mutateAsync(payload)
                }}
                isSubmitting={saveProfileMutation.isPending}
              />
            ) : null}
            <button
              type="button"
              className="button-secondary"
              onClick={() => setIsEditingProfile(false)}
            >
              Cancel
            </button>
          </>
        ) : null}

        {userId && !isEditingProfile && profileQuery.isLoading ? (
          <p className="status-message">Loading your profile…</p>
        ) : null}

        {userId && !isEditingProfile && profileQuery.error ? (
          <p className="status-message status-message--error" role="alert">
            {profileQuery.error.message}
          </p>
        ) : null}

        {showSummary && profileQuery.data ? (
          <ProfileSummary
            profile={profileQuery.data}
            onEdit={() => setIsEditingProfile(true)}
          />
        ) : null}
      </section>

      {userId && !isEditingProfile ? (
        <>
          <section className="dashboard__section">
            <header className="section-header">
              <h2>Browser alerts</h2>
            </header>
            <PushAlerts userId={userId} />
          </section>
          <section className="dashboard__section">
            <header className="section-header">
              <h2>Recommended trials</h2>
            </header>
            <p className="section-intro">
              Matches are ranked by compatibility, then nearer sites. Trials beyond
              your max travel distance are hidden when site coordinates are known.
              Save trials to monitor later. These are potentially relevant options —
              not enrollment advice. Status labels match ClinicalTrials.gov.
            </p>
            <StatusFilter
              selected={statusFilter}
              onChange={setStatusFilter}
            />
            <MatchResults
              matches={matchesQuery.data?.matches ?? []}
              isLoading={matchesQuery.isLoading}
              error={matchesQuery.error}
              userId={userId}
              savedNctIds={
                new Set(
                  (savedTrialsQuery.data?.saved_trials ?? []).map(
                    (trial) => trial.nct_id,
                  ),
                )
              }
            />
          </section>
        </>
      ) : null}
    </div>
  )
}
