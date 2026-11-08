import { test, mock } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { spawnSync } from 'node:child_process';
const require = createRequire(import.meta.url);
const logger = require('firebase-functions/logger');
const { run } = require('./job.cjs');
const { filter } = require('./policy.cjs');
const MSG = 'nightly job failed';

test('the job hands the logger the message the filter expects', async () => {
  const error = mock.method(logger, 'error', () => {});
  await run(async () => { throw new Error('boom'); });
  assert.equal(error.mock.calls[0].arguments[0], MSG);
  error.mock.restore();
});
test('the filter matches that message exactly', () => {
  assert.ok(filter.includes(`jsonPayload.message="${MSG}"`));
});
test('the entry the real logger writes has that message', () => {
  const r = spawnSync(process.execPath, ['-e',
    "require('./job.cjs').run(async () => { throw new Error('boom'); })"], { encoding: 'utf8' });
  const entry = JSON.parse((r.stdout + r.stderr).trim().split('\n').pop());
  assert.equal(entry.message, MSG);
});
