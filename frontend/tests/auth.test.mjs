import assert from 'node:assert/strict';
import { after, beforeEach, test } from 'node:test';
import { apiGet, apiSend, ApiError, setCsrfToken } from '../src/lib/api.ts';

const originalFetch = globalThis.fetch;
const originalWindow = globalThis.window;
beforeEach(() => { globalThis.window = new EventTarget(); setCsrfToken(null); });
after(() => { globalThis.fetch = originalFetch; globalThis.window = originalWindow; });

test('mutations send same-origin cookies and CSRF header without bearer credentials', async () => {
  setCsrfToken('test-csrf-value');
  globalThis.fetch = async (path, options) => {
    assert.equal(path, '/api/orders/1/payments');
    assert.equal(options.credentials, 'same-origin');
    assert.equal(options.cache, 'no-store');
    assert.equal(options.headers['X-CSRF-Token'], 'test-csrf-value');
    assert.equal(options.headers.Authorization, undefined);
    assert.deepEqual(JSON.parse(options.body), { amount: 100 });
    return Response.json({ payment_id: 1 });
  };
  assert.deepEqual(await apiSend('/api/orders/1/payments', 'POST', { amount: 100 }), { payment_id: 1 });
});

test('an expired session clears CSRF and informs the UI', async () => {
  let expired = 0;
  window.addEventListener('staff-session-expired', () => expired++);
  setCsrfToken('test-csrf-value');
  globalThis.fetch = async () => Response.json({ detail: 'Staff sign-in required' }, { status: 401 });
  await assert.rejects(apiGet('/api/orders'), error => error instanceof ApiError && error.status === 401);
  assert.equal(expired, 1);
  globalThis.fetch = async (_, options) => {
    assert.equal(options.headers['X-CSRF-Token'], undefined);
    return Response.json({});
  };
  await apiSend('/api/auth/login', 'POST', { username: 'test-user', password: 'test-only-value' });
});

test('permission failures preserve the session and present backend errors', async () => {
  let expired = false;
  window.addEventListener('staff-session-expired', () => { expired = true; });
  globalThis.fetch = async () => Response.json({ detail: 'Cashier permission required' }, { status: 403 });
  await assert.rejects(apiSend('/api/orders/1/payments', 'POST', {}), /Cashier permission required/);
  assert.equal(expired, false);
});

test('validation errors are readable and logout supports an empty response', async () => {
  globalThis.fetch = async () => Response.json({ detail: [{ msg: 'Invalid amount' }] }, { status: 422 });
  await assert.rejects(apiSend('/api/orders/1/payments', 'POST', {}), /Invalid amount/);
  globalThis.fetch = async () => new Response(null, { status: 204 });
  assert.equal(await apiSend('/api/auth/logout', 'POST', {}), undefined);
});
