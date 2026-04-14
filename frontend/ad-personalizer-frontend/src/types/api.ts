/**
 * TypeScript interfaces mirroring backend Pydantic schemas.
 * Keep in sync with: backend/app/api/schemas/personalize.py
 */

// ── Enums ──────────────────────────────────────────────────────────────────

export type AdTone =
  | 'urgent'
  | 'friendly'
  | 'professional'
  | 'playful'
  | 'luxurious'
  | 'inspirational'
  | 'fearful'
  | 'informative'
  | 'humorous'
  | 'neutral';

export type UrgencyLevel = 'none' | 'low' | 'medium' | 'high' | 'extreme';

export type MatchType = 'exact' | 'fuzzy';

export type GuardrailSeverity = 'info' | 'warning' | 'critical';

export type GuardrailCheckName =
  | 'fact_check'
  | 'scope_check'
  | 'schema_check'
  | 'html_safety_check';

export type EditType = string; // kept loose — backend uses an enum

// ── Ad Analysis ────────────────────────────────────────────────────────────

export interface AdAnalysis {
  headline: string;
  offer: string | null;
  value_proposition: string;
  product_or_service: string | null;
  target_audience: string;
  audience_pain_points: string[];
  tone: AdTone;
  secondary_tones: AdTone[];
  brand_voice_notes: string | null;
  cta_text: string | null;
  cta_urgency: UrgencyLevel;
  key_phrases: string[];
  visual_description: string | null;
  trust_signals: string[];
  confidence: number;
  raw_text_extracted: string | null;
  warnings: string[];
}

// ── Page Analysis ──────────────────────────────────────────────────────────

export interface SectionScore {
  section_id: string;
  score: number;
  notes: string | null;
}

export interface PageAnalysis {
  overall_score: number;
  section_scores: SectionScore[];
  identified_weaknesses: string[];
  recommendations: string[];
  summary: string | null;
}

// ── Edits ──────────────────────────────────────────────────────────────────

export interface AppliedEdit {
  section_id: string;
  edit_type: EditType;
  original_text: string;
  replacement_text: string;
  match_type: MatchType;
  confidence: number;
}

export interface SkippedEdit {
  section_id: string;
  edit_type: EditType;
  reason: string;
}

// ── Guardrails ─────────────────────────────────────────────────────────────

export interface GuardrailWarning {
  check_name: GuardrailCheckName;
  severity: GuardrailSeverity;
  section_id: string | null;
  message: string;
}

export interface GuardrailCheckResult {
  check_name: GuardrailCheckName;
  passed: boolean;
  warnings: GuardrailWarning[];
  blocked_section_ids: string[];
}

export interface GuardrailResult {
  overall_passed: boolean;
  checks: GuardrailCheckResult[];
  all_warnings: GuardrailWarning[];
  blocked_section_ids: string[];
}

// ── API Response / Error ───────────────────────────────────────────────────

export interface PersonalizeResponse {
  status: 'success';
  url: string;
  personalized_html: string;
  original_html: string;
  ad_analysis: AdAnalysis;
  page_analysis: PageAnalysis;
  edits_applied: AppliedEdit[];
  edits_skipped: SkippedEdit[];
  guardrail_result: GuardrailResult;
  confidence_score: number;
  warnings: string[];
}

export interface PersonalizeErrorResponse {
  status: 'error';
  error: string;
  detail: string | null;
}

// ── Input Mode ─────────────────────────────────────────────────────────────

export type AdInputMode = 'upload' | 'image_url' | 'page_url';
