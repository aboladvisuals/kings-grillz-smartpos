import assert from 'node:assert/strict';
import test from 'node:test';
import { allowedStatuses, statusAction } from '../src/lib/orderStatus.ts';

test('pickup actions match the API, without dispatch', () => {
  assert.deepEqual(allowedStatuses('pending', 'Pickup'), ['preparing', 'cancelled']);
  assert.deepEqual(allowedStatuses('preparing', 'Pickup'), ['ready', 'cancelled']);
  assert.deepEqual(allowedStatuses('ready', 'Pickup'), ['completed', 'cancelled']);
  assert.deepEqual(allowedStatuses('dispatched', 'Pickup'), ['completed']);
  assert.equal(statusAction('completed', 'Pickup'), 'Mark collected');
  assert.equal(statusAction('ready', 'Pickup'), 'Ready for pickup');
});

test('delivery can dispatch or complete directly when ready', () => {
  assert.deepEqual(allowedStatuses('pending', 'Delivery'), ['preparing', 'cancelled']);
  assert.deepEqual(allowedStatuses('preparing', 'Delivery'), ['ready', 'cancelled']);
  assert.deepEqual(allowedStatuses('ready', 'Delivery'), ['dispatched', 'completed', 'cancelled']);
  assert.deepEqual(allowedStatuses('dispatched', 'Delivery'), ['completed']);
  assert.equal(statusAction('completed', 'Delivery'), 'Mark delivered');
  assert.equal(statusAction('ready', 'Delivery'), 'Ready for delivery');
});

test('terminal and unrecognised statuses offer no transitions', () => {
  for (const fulfilment of ['Pickup', 'Delivery']) {
    for (const status of ['completed', 'cancelled', 'unknown', 'toString']) {
      assert.deepEqual(allowedStatuses(status, fulfilment), []);
    }
  }
});
