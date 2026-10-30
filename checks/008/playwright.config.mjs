import { devices } from '@playwright/test';
export default { testMatch: 'covered.spec.mjs', reporter: 'line', workers: 1,
  projects: [{ name: 'iPhone 13', use: { ...devices['iPhone 13'] } }] };
