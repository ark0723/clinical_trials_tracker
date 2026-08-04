import type { MatchScore, UserProfile } from '../api/types'

export const sampleProfile: UserProfile = {
  id: 'user-123',
  age: 45,
  cancer_type: 'HER2_POSITIVE_BREAST',
  stage: 'III',
  biomarkers: ['HER2-positive'],
  current_treatment: 'trastuzumab',
  postal_code: '02115',
  ecog: 1,
  brain_metastasis: 'no',
  max_travel_distance_miles: 100,
  notification_channels: ['email'],
}

export const sampleMatch: MatchScore = {
  trial: {
    nct_id: 'NCT01234567',
    title: 'Phase 2 Study of Trastuzumab Deruxtecan in HER2+ Breast Cancer',
    phase: 'PHASE_2',
    status: 'RECRUITING',
    eligibility_criteria_raw: 'Inclusion: HER2 positive...',
    eligibility_criteria_simplified: 'Adults with HER2-positive breast cancer.',
    enrollment_count: 120,
    has_results: false,
    locations: [
      {
        facility: 'Dana-Farber Cancer Institute',
        city: 'Boston',
        country: 'United States',
        latitude: 42.337,
        longitude: -71.102,
      },
      {
        facility: 'Memorial Sloan Kettering',
        city: 'New York',
        country: 'United States',
        latitude: 40.764,
        longitude: -73.957,
      },
    ],
    last_updated: '2026-01-15T12:00:00Z',
  },
  total: 0.85,
  factors: { biomarker: 1, age: 1, stage: 0.5 },
  matched_criteria: ['HER2-positive biomarker', 'Age within trial range'],
  missing_criteria: ['Required prior treatment'],
  unknown_criteria: ['Age: unable to verify'],
  confidence: 0.78,
  rationale:
    'This trial targets HER2-positive breast cancer and your age fits the stated range. ECOG status could not be verified from your profile.',
}
