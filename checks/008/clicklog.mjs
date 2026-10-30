import { webkit, devices } from 'playwright';
import { pathToFileURL } from 'node:url';
const browser = await webkit.launch();
const page = await (await browser.newContext({ ...devices['iPhone 13'] })).newPage();
await page.goto(pathToFileURL(process.argv[2]).href);
await page.locator('#start').click();
console.log('title:', await page.title(), ' scrollY:', await page.evaluate(() => scrollY));
await browser.close();
