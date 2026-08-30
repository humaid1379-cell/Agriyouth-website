import js from '@eslint/js';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import reactHooks from 'eslint-plugin-react-hooks';
import globals from 'globals';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['dist', 'coverage', 'node_modules'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2022,
      globals: { ...globals.browser, ...globals.es2021 },
    },
    plugins: { 'react-hooks': reactHooks, 'jsx-a11y': jsxA11y },
    rules: {
      ...reactHooks.configs.recommended.rules,
      ...jsxA11y.configs.recommended.rules,
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      '@typescript-eslint/consistent-type-imports': 'error',
      'no-restricted-globals': ['error', { name: 'fetch', message: 'Use the api client in src/api/client.ts.' }],
      // Nothing in this interface may reach an external origin or open a new context.
      'no-restricted-properties': [
        'error',
        { object: 'window', property: 'open', message: 'The prototype does not link out.' },
      ],
    },
  },
  {
    files: ['src/api/client.ts', 'tests/**/*.{ts,tsx}'],
    rules: { 'no-restricted-globals': 'off' },
  },
);
