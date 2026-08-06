import { useState, type FormEvent } from 'react'

import type {
  BrainMetastasisStatus,
  CancerStage,
  CurrentTreatment,
  EcogStatus,
  UserProfile,
  UserProfileCreate,
} from '../api/types'
import {
  BRAIN_METASTASIS_OPTIONS,
  CURRENT_TREATMENT_OPTIONS,
  ECOG_OPTIONS,
} from '../api/types'
import { FieldHelp } from './FieldHelp'

interface ProfileFormProps {
  initialProfile?: UserProfile
  onSubmit: (payload: UserProfileCreate) => void | Promise<void>
  isSubmitting?: boolean
}

const STAGE_OPTIONS: CancerStage[] = ['I', 'II', 'III', 'IV']

const ECOG_DEFINITION =
  'ECOG performance status is a 0–4 score doctors use to describe how cancer affects daily activity. 0 means fully active; higher numbers mean more limitation.'

const BRAIN_METASTASIS_DEFINITION =
  'Brain metastases are cancer spots that have spread to the brain. Some trials exclude people with active brain metastases, while others specifically study that situation.'

export function ProfileForm({
  initialProfile,
  onSubmit,
  isSubmitting = false,
}: ProfileFormProps) {
  const [age, setAge] = useState(String(initialProfile?.age ?? 45))
  const [stage, setStage] = useState<CancerStage>(
    initialProfile?.stage ?? 'III',
  )
  const [her2Positive, setHer2Positive] = useState(
    initialProfile?.biomarkers.includes('HER2-positive') ?? true,
  )
  const [currentTreatment, setCurrentTreatment] = useState<CurrentTreatment>(
    initialProfile?.current_treatment ?? 'unknown',
  )
  const [postalCode, setPostalCode] = useState(
    initialProfile?.postal_code ?? '',
  )
  const [ecog, setEcog] = useState(
    initialProfile?.ecog === null || initialProfile?.ecog === undefined
      ? 'unknown'
      : String(initialProfile.ecog),
  )
  const [brainMetastasis, setBrainMetastasis] = useState<BrainMetastasisStatus>(
    initialProfile?.brain_metastasis ?? 'unknown',
  )
  const [maxTravelMiles, setMaxTravelMiles] = useState(
    String(initialProfile?.max_travel_distance_miles ?? 50),
  )
  const [browserNotifications, setBrowserNotifications] = useState(
    initialProfile?.notification_channels.includes('browser') ??
      initialProfile?.notification_channels.includes('email') ??
      true,
  )

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const payload: UserProfileCreate = {
      age: Number(age),
      cancer_type: 'HER2_POSITIVE_BREAST',
      stage,
      biomarkers: her2Positive ? ['HER2-positive'] : [],
      current_treatment: currentTreatment,
      postal_code: postalCode.trim() || null,
      ecog: ecog === 'unknown' ? null : (Number(ecog) as EcogStatus),
      brain_metastasis: brainMetastasis,
      max_travel_distance_miles: Number(maxTravelMiles),
      notification_channels: ['browser'],
    }

    await onSubmit(payload)
  }

  return (
    <form className="profile-form" onSubmit={handleSubmit}>
      <div className="form-field">
        <label htmlFor="profile-age">Age</label>
        <input
          id="profile-age"
          type="number"
          min={18}
          max={120}
          required
          value={age}
          onChange={(event) => setAge(event.target.value)}
        />
      </div>

      <div className="form-field">
        <label htmlFor="profile-stage">Cancer stage</label>
        <select
          id="profile-stage"
          value={stage}
          onChange={(event) => setStage(event.target.value as CancerStage)}
        >
          {STAGE_OPTIONS.map((option) => (
            <option key={option} value={option}>
              Stage {option}
            </option>
          ))}
        </select>
      </div>

      <div className="form-field form-field--checkbox">
        <label htmlFor="profile-her2">
          <input
            id="profile-her2"
            type="checkbox"
            checked={her2Positive}
            onChange={(event) => setHer2Positive(event.target.checked)}
          />
          HER2-positive
        </label>
      </div>

      <div className="form-field">
        <label htmlFor="profile-treatment">Current or most recent treatment</label>
        <select
          id="profile-treatment"
          value={currentTreatment}
          onChange={(event) =>
            setCurrentTreatment(event.target.value as CurrentTreatment)
          }
        >
          {CURRENT_TREATMENT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="form-field">
        <label htmlFor="profile-postal">ZIP / postal code (optional)</label>
        <input
          id="profile-postal"
          type="text"
          inputMode="numeric"
          autoComplete="postal-code"
          value={postalCode}
          onChange={(event) => setPostalCode(event.target.value)}
          placeholder="e.g. 10001"
        />
      </div>

      <div className="form-field">
        <div className="form-field__label-row">
          <label htmlFor="profile-ecog">ECOG performance status</label>
          <FieldHelp term="ECOG performance status" definition={ECOG_DEFINITION} />
        </div>
        <select
          id="profile-ecog"
          value={ecog}
          onChange={(event) => setEcog(event.target.value)}
        >
          {ECOG_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="form-field">
        <div className="form-field__label-row">
          <label htmlFor="profile-brain">Brain metastases</label>
          <FieldHelp
            term="brain metastases"
            definition={BRAIN_METASTASIS_DEFINITION}
          />
        </div>
        <select
          id="profile-brain"
          value={brainMetastasis}
          onChange={(event) =>
            setBrainMetastasis(event.target.value as BrainMetastasisStatus)
          }
        >
          {BRAIN_METASTASIS_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="form-field">
        <label htmlFor="profile-travel">Max travel distance (miles)</label>
        <input
          id="profile-travel"
          type="number"
          min={0}
          max={10000}
          required
          value={maxTravelMiles}
          onChange={(event) => setMaxTravelMiles(event.target.value)}
        />
      </div>

      <div className="form-field form-field--checkbox">
        <label htmlFor="profile-browser-push">
          <input
            id="profile-browser-push"
            type="checkbox"
            checked={browserNotifications}
            onChange={(event) => setBrowserNotifications(event.target.checked)}
          />
          Browser push alerts for saved trials
        </label>
        <p className="field-hint">
          Works on desktop and Android browsers. On iPhone/iPad, add this app to
          your Home Screen (Safari) to receive pushes. Email and Telegram come
          later.
        </p>
      </div>

      <button type="submit" disabled={isSubmitting || !her2Positive || !browserNotifications}>
        Save profile
      </button>
    </form>
  )
}
