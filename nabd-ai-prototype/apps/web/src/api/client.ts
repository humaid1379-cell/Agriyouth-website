import type { z } from 'zod';

import { errorEnvelopeSchema } from './types';

/**
 * The single place the browser talks to the API.
 *
 * Every response is parsed against its schema before it reaches a component, and every
 * failure becomes an {@link ApiError} carrying the server's reason code. The interface
 * never invents a message of its own for a governed failure.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';
const TOKEN_STORAGE_KEY = 'nabd.demo.session';

export class ApiError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly status: number,
    readonly correlationId: string,
    readonly caseId: string | null = null,
    readonly state: string | null = null,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export function readToken(): string | null {
  try {
    return window.sessionStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function writeToken(token: string | null): void {
  try {
    if (token === null) {
      window.sessionStorage.removeItem(TOKEN_STORAGE_KEY);
    } else {
      window.sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
    }
  } catch {
    // A browser with storage disabled simply loses the demo session on reload.
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST';
  body?: unknown;
  token?: string | null;
}

export async function request<T>(
  path: string,
  schema: z.ZodType<T>,
  options: RequestOptions = {},
): Promise<T> {
  const token = options.token === undefined ? readToken() : options.token;
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (options.body !== undefined) headers['Content-Type'] = 'application/json';
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${BASE_URL}${path}`, {
    method: options.method ?? 'GET',
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    credentials: 'omit',
    redirect: 'error',
    referrerPolicy: 'no-referrer',
  });

  const text = await response.text();
  const payload: unknown = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const envelope = errorEnvelopeSchema.safeParse(payload);
    if (envelope.success) {
      const { code, message, correlation_id, case_id, state } = envelope.data.error;
      throw new ApiError(code, message, response.status, correlation_id, case_id, state);
    }
    throw new ApiError(
      'INTERNAL_CONTROL_FAILURE',
      'The request failed and the response could not be interpreted.',
      response.status,
      'unknown',
    );
  }

  const parsed = schema.safeParse(payload);
  if (!parsed.success) {
    throw new ApiError(
      'INTERNAL_CONTROL_FAILURE',
      'The response did not match the published API contract.',
      response.status,
      response.headers.get('X-Correlation-Id') ?? 'unknown',
    );
  }
  return parsed.data;
}
