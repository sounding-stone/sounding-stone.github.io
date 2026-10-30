import { webkit, devices } from 'playwright';
import { pathToFileURL } from 'node:url';
const browser = await webkit.launch();
const page = await (await browser.newContext({ ...devices['iPhone 13'] })).newPage();
await page.goto(pathToFileURL(process.argv[2]).href);
const b = await page.locator('#start').boundingBox();
await page.mouse.click(b.x + b.width / 2, b.y + b.height / 2);
console.log(`mouse.click at centre -> title "${await page.title()}"  scrollY ${await page.evaluate(() => scrollY)}`);
await browser.close();
