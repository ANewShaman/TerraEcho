/**
 * TerraEcho — eventBus.js
 * Responsibility: Pub/sub singleton. Cross-module event communication only.
 * No domain logic. No state. No DOM.
 *
 * Usage:
 *   import eventBus from '../eventBus.js';
 *   eventBus.on('timeline:yearChanged', handler);
 *   eventBus.emit('timeline:yearChanged', { year: 1970 });
 *   eventBus.off('timeline:yearChanged', handler);
 *
 * Known events (Phase 2):
 *   timeline:yearChanged   → { year: number }
 *   timeline:playStarted   → {}
 *   timeline:playStopped   → {}
 *
 * Known events (Phase 3, reserved):
 *   actions:incremented    → { action: string, totalCount: number }
 *
 * Known events (Phase 4, reserved):
 *   audio:zoneChanged      → { zone: string }
 *
 * Known events (Phase 5, reserved):
 *   ml:predictionReady     → { year: number, values: object }
 */

const eventBus = (() => {
  /** @type {Map<string, Set<Function>>} */
  const listeners = new Map();

  /**
   * Subscribe to an event.
   * @param {string}   event
   * @param {Function} handler
   */
  function on(event, handler) {
    if (!listeners.has(event)) {
      listeners.set(event, new Set());
    }
    listeners.get(event).add(handler);
  }

  /**
   * Unsubscribe a specific handler from an event.
   * @param {string}   event
   * @param {Function} handler
   */
  function off(event, handler) {
    listeners.get(event)?.delete(handler);
  }

  /**
   * Publish an event with optional payload.
   * All registered handlers are called synchronously.
   * @param {string} event
   * @param {*}      [payload]
   */
  function emit(event, payload) {
    listeners.get(event)?.forEach((handler) => {
      handler(payload);
    });
  }

  return { on, off, emit };
})();

export default eventBus;