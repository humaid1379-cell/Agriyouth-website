import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { StatusIndicator, statusKindFor } from '../src/components/StatusIndicator';
import { Layout } from '../src/app/Layout';
import { SessionProvider } from '../src/features/session/SessionContext';
import { renderWithProviders } from './helpers';

describe('status is never colour-only', () => {
  it('renders text, an icon and a distinct shape for the review status', () => {
    const { container } = renderWithProviders(<StatusIndicator kind="review" withDetail />);

    // 1. Wording.
    expect(screen.getByText('Human review required')).toBeInTheDocument();
    expect(
      screen.getByText(/material information, authority, or risk requires human review/i),
    ).toBeInTheDocument();

    // 2. An icon is drawn.
    const svg = container.querySelector('svg[data-shape]');
    expect(svg).not.toBeNull();

    // 3. A distinct shape, exposed for assertion and for anyone reading in grayscale.
    expect(svg?.getAttribute('data-shape')).toBe('triangle');
    expect(container.querySelector('[data-status-shape="triangle"]')).not.toBeNull();
  });

  it('renders a different shape and wording for the stop status', () => {
    const { container } = renderWithProviders(<StatusIndicator kind="stop" withDetail />);
    expect(screen.getByText('Cannot proceed under current conditions')).toBeInTheDocument();
    expect(
      screen.getByText(/a required control failed, conflict exists, or authority is absent/i),
    ).toBeInTheDocument();
    expect(container.querySelector('svg[data-shape]')?.getAttribute('data-shape')).toBe('octagon');
  });

  it('gives each status kind a shape that no other kind shares within review and stop', () => {
    const review = renderWithProviders(<StatusIndicator kind="review" />);
    const reviewShape = review.container.querySelector('svg[data-shape]')?.getAttribute('data-shape');
    review.unmount();

    const stop = renderWithProviders(<StatusIndicator kind="stop" />);
    const stopShape = stop.container.querySelector('svg[data-shape]')?.getAttribute('data-shape');
    stop.unmount();

    const closed = renderWithProviders(<StatusIndicator kind="closed" />);
    const closedShape = closed.container.querySelector('svg[data-shape]')?.getAttribute('data-shape');

    expect(new Set([reviewShape, stopShape, closedShape]).size).toBe(3);
  });

  it('never renders the informational readiness style for a case or route', () => {
    for (const [state, route] of [
      ['AWAITING_AUTHORIZED_HUMAN_REVIEW', 'HUMAN_REVIEW_REQUIRED'],
      ['CANNOT_PROCEED', 'CANNOT_PROCEED'],
      ['CLOSED_DECISION_SUPPORT_RECORD', 'HUMAN_REVIEW_REQUIRED'],
      ['AUTHORIZATION_PREFLIGHT', null],
      ['BOUNDED_DRAFT', null],
    ] as Array<[string, string | null]>) {
      expect(statusKindFor(state, route)).not.toBe('informational');
    }
  });

  it('maps each case state onto the correct status kind', () => {
    expect(statusKindFor('AWAITING_AUTHORIZED_HUMAN_REVIEW', 'HUMAN_REVIEW_REQUIRED')).toBe('review');
    expect(statusKindFor('CANNOT_PROCEED', 'CANNOT_PROCEED')).toBe('stop');
    expect(statusKindFor('CLOSED_DECISION_SUPPORT_RECORD', 'HUMAN_REVIEW_REQUIRED')).toBe('closed');
    expect(statusKindFor('AUTHORIZATION_PREFLIGHT', null)).toBe('pending');
    expect(statusKindFor('BOUNDED_DRAFT', null)).toBe('processing');
  });

  it('uses no green readiness colour for any case status', () => {
    for (const kind of ['review', 'stop', 'closed', 'pending', 'processing'] as const) {
      const view = renderWithProviders(<StatusIndicator kind={kind} />);
      expect(view.container.innerHTML).not.toContain('#2E8168');
      view.unmount();
    }
  });
});

describe('bilingual direction', () => {
  it('flips the document direction to rtl and back through the language toggle', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <SessionProvider>
        <Layout />
      </SessionProvider>,
    );

    expect(document.documentElement.dir).toBe('ltr');
    expect(document.documentElement.lang).toBe('en');

    await user.click(screen.getByRole('button', { name: 'العربية' }));
    expect(document.documentElement.dir).toBe('rtl');
    expect(document.documentElement.lang).toBe('ar');

    await user.click(screen.getByRole('button', { name: 'English' }));
    expect(document.documentElement.dir).toBe('ltr');
    expect(document.documentElement.lang).toBe('en');
  });

  it('translates the shell into Arabic', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <SessionProvider>
        <Layout />
      </SessionProvider>,
    );
    await user.click(screen.getByRole('button', { name: 'العربية' }));
    expect(screen.getByText('نبض للمراجعة والقرار')).toBeInTheDocument();
    expect(screen.getByText('ذكاء محكوم. سلطة بشرية.')).toBeInTheDocument();
  });

  it('offers a skip link and states the non-execution boundary in the footer', () => {
    renderWithProviders(
      <SessionProvider>
        <Layout />
      </SessionProvider>,
    );
    expect(screen.getByRole('link', { name: /skip to main content/i })).toBeInTheDocument();
    expect(
      screen.getByText(/does not approve, execute, transmit or activate any institutional action/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Built: NOT_EVIDENCED · Integration: NOT_EVIDENCED/),
    ).toBeInTheDocument();
  });
});
