/**
 * API client for the Ad Personalizer backend.
 * Handles both JSON and multipart/form-data endpoints.
 */

import type { PersonalizeResponse } from '../types/api';

const BASE_URL = '/api/v1';

// ── Shared fetch helper ────────────────────────────────────────────────────

async function handleResponse<T>(res: Response): Promise<T> {
  const data = await res.json();
  if (!res.ok) {
    const errorMsg =
      data?.detail || data?.error || `HTTP ${res.status}: ${res.statusText}`;
    throw new Error(errorMsg);
  }
  return data as T;
}

// ── Endpoint 1: JSON payload ───────────────────────────────────────────────

export interface JsonAdInput {
  ad_image_url?: string;
  ad_page_url?: string;
}

export async function personalizeWithJSON(
  adInput: JsonAdInput,
  landingPageUrl: string,
  signal?: AbortSignal
): Promise<PersonalizeResponse> {
  const res = await fetch(`${BASE_URL}/personalize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    signal,
    body: JSON.stringify({
      ad_input: adInput,
      landing_page_url: landingPageUrl,
    }),
  });
  return handleResponse<PersonalizeResponse>(res);
}

// ── Endpoint 2: Multipart file upload ──────────────────────────────────────

export async function personalizeWithUpload(
  file: File,
  landingPageUrl: string,
  signal?: AbortSignal
): Promise<PersonalizeResponse> {
  const form = new FormData();
  form.append('landing_page_url', landingPageUrl);
  form.append('ad_image', file);

  const res = await fetch(`${BASE_URL}/personalize/upload`, {
    method: 'POST',
    signal,
    body: form,
  });
  return handleResponse<PersonalizeResponse>(res);
}

// ── Smart dispatcher ───────────────────────────────────────────────────────

export interface SmartPersonalizeArgs {
  mode: 'upload' | 'image_url' | 'page_url';
  uploadedFile?: File | null;
  adUrl?: string;
  landingPageUrl: string;
  signal?: AbortSignal;
}

export async function personalize({
  mode,
  uploadedFile,
  adUrl,
  landingPageUrl,
  signal,
}: SmartPersonalizeArgs): Promise<PersonalizeResponse> {
  if (mode === 'upload' && uploadedFile) {
    return personalizeWithUpload(uploadedFile, landingPageUrl, signal);
  }

  if (mode === 'image_url' && adUrl) {
    return personalizeWithJSON({ ad_image_url: adUrl }, landingPageUrl, signal);
  }

  if (mode === 'page_url' && adUrl) {
    return personalizeWithJSON({ ad_page_url: adUrl }, landingPageUrl, signal);
  }

  throw new Error('Invalid input: please provide a valid ad input and landing page URL.');
}
