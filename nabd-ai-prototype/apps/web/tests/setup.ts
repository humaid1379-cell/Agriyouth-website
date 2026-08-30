import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeEach, vi } from 'vitest';

/**
 * The component tests never reach a network. `fetch` is replaced with a stub that fails
 * loudly if a test forgets to mock a route, so a silently-passing test cannot mask a real
 * request leaving the browser.
 */
beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      throw new Error(`unmocked request to ${String(input)}`);
    }),
  );
  window.sessionStorage.clear();
  window.localStorage.clear();
  document.documentElement.lang = 'en';
  document.documentElement.dir = 'ltr';
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});
