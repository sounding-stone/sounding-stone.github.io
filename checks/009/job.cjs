const logger = require('firebase-functions/logger');
exports.run = async (work) => {
  try { await work(); }
  catch { logger.error('nightly job failed', { category: 'nightly' }); }
};
