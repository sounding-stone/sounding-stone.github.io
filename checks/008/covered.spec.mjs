import { test, expect } from '@playwright/test';
import { pathToFileURL } from 'node:url';

for (const file of ['page.html', 'page-fixed.html']) {
  test.describe(file, () => {
    test.beforeEach(async ({ page }) => { await page.goto(pathToFileURL(file).href); });

    test('toBeVisible', async ({ page }) => {
      await expect(page.locator('#start')).toBeVisible();
    });
    test('toBeInViewport', async ({ page }) => {
      await expect(page.locator('#start')).toBeInViewport({ ratio: 1 });
    });
    test('click opens question 1', async ({ page }) => {
      await page.locator('#start').click();
      await expect(page).toHaveTitle('question 1');
    });
    test('centre of the button is the button', async ({ page }) => {
      const hit = await page.locator('#start').evaluate((el) => {
        const r = el.getBoundingClientRect();
        return document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2) === el;
      });
      expect(hit).toBe(true);
    });
  });
}
