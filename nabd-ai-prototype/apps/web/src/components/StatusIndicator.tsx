import { useTranslate } from '../i18n/LanguageProvider';
import type { MessageKey } from '../i18n/messages';

/**
 * Status is never colour-only.
 *
 * Every status renders three independent signals: a distinct **shape** (triangle, octagon,
 * circle, square), an **icon** drawn inside that shape, and the required **wording** in
 * text. The colour is a fourth signal, not the carrier. Anyone reading in grayscale, with a
 * colour vision deficiency, or through a screen reader gets the same information.
 *
 * The informational readiness style exists only for non-V1 explanatory components. It never
 * means approval or execution, and no case, packet, route or disposition may use it.
 */

export type StatusKind = 'review' | 'stop' | 'closed' | 'pending' | 'processing' | 'informational';

type Shape = 'triangle' | 'octagon' | 'circle' | 'square';

interface StatusDefinition {
  shape: Shape;
  colour: string;
  labelKey: MessageKey;
  detailKey: MessageKey;
}

const DEFINITIONS: Record<Exclude<StatusKind, 'informational'>, StatusDefinition> = {
  review: {
    shape: 'triangle',
    colour: '#B9852E',
    labelKey: 'status.review.label',
    detailKey: 'status.review.detail',
  },
  stop: {
    shape: 'octagon',
    colour: '#A9474F',
    labelKey: 'status.stop.label',
    detailKey: 'status.stop.detail',
  },
  closed: {
    shape: 'square',
    colour: '#133047',
    labelKey: 'status.closed.label',
    detailKey: 'status.closed.detail',
  },
  pending: {
    shape: 'circle',
    colour: '#133047',
    labelKey: 'status.pending.label',
    detailKey: 'status.pending.detail',
  },
  processing: {
    shape: 'circle',
    colour: '#133047',
    labelKey: 'status.processing.label',
    detailKey: 'status.processing.detail',
  },
};

/** Map a case state and route onto a status kind. */
export function statusKindFor(state: string | null, route: string | null): StatusKind {
  if (route === 'CANNOT_PROCEED' || state === 'CANNOT_PROCEED') return 'stop';
  if (state === 'CLOSED_DECISION_SUPPORT_RECORD') return 'closed';
  if (state === 'AWAITING_AUTHORIZED_HUMAN_REVIEW' || route === 'HUMAN_REVIEW_REQUIRED') {
    return 'review';
  }
  if (state === 'AUTHORIZATION_PREFLIGHT' || state === null) return 'pending';
  return 'processing';
}

function ShapeMark({ shape, colour, size }: { shape: Shape; colour: string; size: number }) {
  const common = { fill: 'none', stroke: colour, strokeWidth: 2, strokeLinejoin: 'round' as const };
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      aria-hidden="true"
      focusable="false"
      data-shape={shape}
      className="shrink-0"
    >
      {shape === 'triangle' && (
        <>
          <path d="M12 3 L22 20 H2 Z" {...common} />
          {/* attention mark */}
          <path d="M12 10 V14" stroke={colour} strokeWidth={2} strokeLinecap="round" />
          <circle cx="12" cy="17" r="1.1" fill={colour} />
        </>
      )}
      {shape === 'octagon' && (
        <>
          <path d="M8 2 H16 L22 8 V16 L16 22 H8 L2 16 V8 Z" {...common} />
          {/* stop bar */}
          <path d="M7.5 12 H16.5" stroke={colour} strokeWidth={2.4} strokeLinecap="round" />
        </>
      )}
      {shape === 'circle' && (
        <>
          <circle cx="12" cy="12" r="9.5" {...common} />
          <path d="M12 7 V12 L15.5 14" stroke={colour} strokeWidth={2} strokeLinecap="round" fill="none" />
        </>
      )}
      {shape === 'square' && (
        <>
          <rect x="3" y="3" width="18" height="18" rx="2" {...common} />
          <path d="M7.5 12.5 L10.5 15.5 L16.5 8.5" stroke={colour} strokeWidth={2} strokeLinecap="round" fill="none" />
        </>
      )}
    </svg>
  );
}

interface StatusIndicatorProps {
  kind: StatusKind;
  /** Show the explanatory sentence beneath the label. */
  withDetail?: boolean;
  /** Compact form for table cells. The shape, icon and label all remain. */
  compact?: boolean;
  /** Override the label, for example with a raw state name. The status wording still shows. */
  suffix?: string;
}

export function StatusIndicator({
  kind,
  withDetail = false,
  compact = false,
  suffix,
}: StatusIndicatorProps) {
  const t = useTranslate();

  if (kind === 'informational') {
    // Explanatory use only. Never applied to a case, packet, route or disposition.
    return (
      <span className="inline-flex items-center gap-2 text-sm text-status-informational">
        <ShapeMark shape="circle" colour="#2E8168" size={16} />
        <span>Informational</span>
      </span>
    );
  }

  const definition = DEFINITIONS[kind];
  const label = t(definition.labelKey);
  const detail = t(definition.detailKey);

  return (
    <span
      className={compact ? 'inline-flex items-start gap-2' : 'flex items-start gap-3'}
      data-status-kind={kind}
      data-status-shape={definition.shape}
    >
      <ShapeMark shape={definition.shape} colour={definition.colour} size={compact ? 18 : 24} />
      <span className="min-w-0">
        <span
          className={compact ? 'block text-sm font-semibold' : 'block text-base font-semibold'}
          style={{ color: definition.colour }}
        >
          {label}
          {suffix ? <span className="font-normal text-navy-slate"> — {suffix}</span> : null}
        </span>
        {withDetail ? (
          <span className="mt-1 block max-w-prose text-sm text-navy-slate">{detail}</span>
        ) : null}
      </span>
    </span>
  );
}
