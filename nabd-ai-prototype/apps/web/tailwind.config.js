/**
 * NABD AI brand palette and type scale.
 *
 * Status colours are declared here but are never used alone: every status renders text, an
 * icon and a distinct shape as well, so the interface stays legible in grayscale and to
 * anyone who does not perceive the colour difference.
 */
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: { deep: '#081321', slate: '#133047' },
        soft: '#F4F7F9',
        cyan: { nabd: '#10BFE5' },
        violet: { authority: '#735ACB' },
        status: { review: '#B9852E', stop: '#A9474F', informational: '#2E8168' },
      },
      fontFamily: {
        sans: ['"Noto Sans"', 'system-ui', 'sans-serif'],
        arabic: ['"Noto Sans Arabic"', '"Noto Sans"', 'sans-serif'],
        kufi: ['"Noto Kufi Arabic"', '"Noto Sans Arabic"', 'sans-serif'],
        mono: ['"Noto Sans Mono"', 'ui-monospace', 'monospace'],
      },
      maxWidth: { prose: '72ch' },
    },
  },
  plugins: [],
};
