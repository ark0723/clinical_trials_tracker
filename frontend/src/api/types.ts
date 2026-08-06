export type CancerStage = 'I' | 'II' | 'III' | 'IV'

export type NotificationChannel = 'browser' | 'email' | 'telegram'

export type CurrentTreatment =
  | 'trastuzumab'
  | 'pertuzumab'
  | 'trastuzumab_emtansine'
  | 'trastuzumab_deruxtecan'
  | 'tucatinib'
  | 'neratinib'
  | 'lapatinib'
  | 'chemotherapy'
  | 'endocrine_therapy'
  | 'none'
  | 'other'
  | 'unknown'

export type BrainMetastasisStatus = 'yes' | 'no' | 'unknown'

export type EcogStatus = 0 | 1 | 2 | 3 | 4

export type TrialPhase =
  | 'PHASE_1'
  | 'PHASE_2'
  | 'PHASE_3'
  | 'PHASE_4'
  | 'NOT_APPLICABLE'

export type TrialStatus =
  | 'RECRUITING'
  | 'NOT_YET_RECRUITING'
  | 'ACTIVE_NOT_RECRUITING'
  | 'ENROLLING_BY_INVITATION'
  | 'SUSPENDED'
  | 'COMPLETED'
  | 'TERMINATED'
  | 'WITHDRAWN'
  | 'AVAILABLE'
  | 'NO_LONGER_AVAILABLE'
  | 'APPROVED_FOR_MARKETING'
  | 'WITHHELD'
  | 'UNKNOWN'

export interface UserProfileCreate {
  age: number
  cancer_type?: 'HER2_POSITIVE_BREAST'
  stage: CancerStage
  biomarkers: string[]
  current_treatment: CurrentTreatment
  postal_code?: string | null
  ecog?: EcogStatus | null
  brain_metastasis: BrainMetastasisStatus
  max_travel_distance_miles: number
  notification_channels: NotificationChannel[]
}

export interface UserProfile extends UserProfileCreate {
  id: string
}

export interface TrialLocation {
  facility?: string | null
  city?: string | null
  country?: string | null
  latitude?: number | null
  longitude?: number | null
}

export interface ClinicalTrial {
  nct_id: string
  title: string
  phase: TrialPhase
  status: TrialStatus
  eligibility_criteria_raw: string
  eligibility_criteria_simplified: string | null
  enrollment_count: number | null
  has_results: boolean
  locations?: TrialLocation[]
  last_updated: string
}

export interface MatchScore {
  trial: ClinicalTrial
  total: number
  factors: Record<string, number>
  matched_criteria: string[]
  missing_criteria: string[]
  unknown_criteria: string[]
  confidence: number
  rationale: string
  nearest_site_miles?: number | null
  things_to_confirm?: string[]
  questions_for_doctor?: string[]
}

export interface SavedTrial {
  user_id: string
  nct_id: string
  status_at_save: string
  saved_at: string
}

export interface MatchesResponse {
  matches: MatchScore[]
}


export const CURRENT_TREATMENT_OPTIONS: {
  value: CurrentTreatment
  label: string
}[] = [
  { value: 'unknown', label: "I don't know / not sure" },
  { value: 'trastuzumab', label: 'Trastuzumab (Herceptin)' },
  { value: 'pertuzumab', label: 'Pertuzumab (Perjeta)' },
  { value: 'trastuzumab_emtansine', label: 'Trastuzumab emtansine / T-DM1 (Kadcyla)' },
  {
    value: 'trastuzumab_deruxtecan',
    label: 'Trastuzumab deruxtecan / T-DXd (Enhertu)',
  },
  { value: 'tucatinib', label: 'Tucatinib (Tukysa)' },
  { value: 'neratinib', label: 'Neratinib (Nerlynx)' },
  { value: 'lapatinib', label: 'Lapatinib (Tykerb)' },
  { value: 'chemotherapy', label: 'Chemotherapy' },
  { value: 'endocrine_therapy', label: 'Endocrine (hormone) therapy' },
  { value: 'none', label: 'Not currently on treatment' },
  { value: 'other', label: 'Other / not listed' },
]

export const ECOG_OPTIONS: { value: string; label: string }[] = [
  { value: 'unknown', label: "I don't know / not sure" },
  { value: '0', label: '0 — Fully active' },
  { value: '1', label: '1 — Restricted in strenuous activity' },
  { value: '2', label: '2 — Ambulatory, unable to work' },
  { value: '3', label: '3 — Limited self-care' },
  { value: '4', label: '4 — Completely disabled' },
]

export const BRAIN_METASTASIS_OPTIONS: {
  value: BrainMetastasisStatus
  label: string
}[] = [
  { value: 'unknown', label: "I don't know / not sure" },
  { value: 'no', label: 'No' },
  { value: 'yes', label: 'Yes' },
]
