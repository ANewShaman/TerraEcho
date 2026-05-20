/**
 * TerraEcho — tabs.js
 * Responsibility: Tab switching UI state only.
 * Direct DOM manipulation. No EventBus. No external dependencies.
 *
 * Reads: [role="tab"][data-tab], [role="tabpanel"][data-tab]
 * Writes: aria-selected, aria-hidden
 */

/**
 * Activates a tab by its data-tab value.
 * All other tabs and panels are deactivated.
 *
 * @param {string} targetTab - The data-tab value to activate.
 * @param {NodeList} buttons  - All tab button elements.
 * @param {NodeList} panels   - All tab panel elements.
 */
function activateTab(targetTab, buttons, panels) {
  buttons.forEach((btn) => {
    const isTarget = btn.dataset.tab === targetTab;
    btn.setAttribute('aria-selected', isTarget ? 'true' : 'false');
    btn.tabIndex = isTarget ? 0 : -1;
  });

  panels.forEach((panel) => {
    const isTarget = panel.dataset.tab === targetTab;
    panel.setAttribute('aria-hidden', isTarget ? 'false' : 'true');
  });
}

/**
 * Initialises the tab system.
 * - Reads initial state from aria-selected attributes in HTML.
 * - Attaches click listeners.
 * - Supports keyboard navigation (ArrowLeft / ArrowRight).
 *
 * Called once from main.js after DOMContentLoaded.
 */
export function initTabs() {
  const buttons = document.querySelectorAll('[role="tab"][data-tab]');
  const panels  = document.querySelectorAll('[role="tabpanel"][data-tab]');

  if (buttons.length === 0 || panels.length === 0) {
    console.warn('[tabs] No tab buttons or panels found.');
    return;
  }

  // Click handler
  buttons.forEach((btn) => {
    btn.addEventListener('click', () => {
      activateTab(btn.dataset.tab, buttons, panels);
    });
  });

  // Keyboard navigation — left/right arrow keys within tab bar
  buttons.forEach((btn, index) => {
    btn.addEventListener('keydown', (e) => {
      let targetIndex = null;

      if (e.key === 'ArrowRight') {
        targetIndex = (index + 1) % buttons.length;
      } else if (e.key === 'ArrowLeft') {
        targetIndex = (index - 1 + buttons.length) % buttons.length;
      } else if (e.key === 'Home') {
        targetIndex = 0;
      } else if (e.key === 'End') {
        targetIndex = buttons.length - 1;
      }

      if (targetIndex !== null) {
        /**
 * TerraEcho — tabs.js
 * Responsibility: Tab switching UI state only.
 * Direct DOM manipulation. No EventBus. No external dependencies.
 *
 * Reads: [role="tab"][data-tab], [role="tabpanel"][data-tab]
 * Writes: aria-selected, aria-hidden
 */

/**
 * Activates a tab by its data-tab value.
 * All other tabs and panels are deactivated.
 *
 * @param {string} targetTab - The data-tab value to activate.
 * @param {NodeList} buttons  - All tab button elements.
 * @param {NodeList} panels   - All tab panel elements.
 */
function activateTab(targetTab, buttons, panels) {
  buttons.forEach((btn) => {
    const isTarget = btn.dataset.tab === targetTab;
    btn.setAttribute('aria-selected', isTarget ? 'true' : 'false');
    btn.tabIndex = isTarget ? 0 : -1;
  });

  panels.forEach((panel) => {
    const isTarget = panel.dataset.tab === targetTab;
    panel.setAttribute('aria-hidden', isTarget ? 'false' : 'true');
  });
}

/**
 * Initialises the tab system.
 * - Reads initial state from aria-selected attributes in HTML.
 * - Attaches click listeners.
 * - Supports keyboard navigation (ArrowLeft / ArrowRight).
 *
 * Called once from main.js after DOMContentLoaded.
 */
export function initTabs() {
  const buttons = document.querySelectorAll('[role="tab"][data-tab]');
  const panels  = document.querySelectorAll('[role="tabpanel"][data-tab]');

  if (buttons.length === 0 || panels.length === 0) {
    console.warn('[tabs] No tab buttons or panels found.');
    return;
  }

  // Click handler
  buttons.forEach((btn) => {
    btn.addEventListener('click', () => {
      activateTab(btn.dataset.tab, buttons, panels);
    });
  });

  // Keyboard navigation — left/right arrow keys within tab bar
  buttons.forEach((btn, index) => {
    btn.addEventListener('keydown', (e) => {
      let targetIndex = null;

      if (e.key === 'ArrowRight') {
        targetIndex = (index + 1) % buttons.length;
      } else if (e.key === 'ArrowLeft') {
        targetIndex = (index - 1 + buttons.length) % buttons.length;
      } else if (e.key === 'Home') {
        targetIndex = 0;
      } else if (e.key === 'End') {
        targetIndex = buttons.length - 1;
      }

      if (targetIndex !== null) {
        e.preventDefault();
        buttons[targetIndex].focus();
        activateTab(buttons[targetIndex].dataset.tab, buttons, panels);
      }
    });
  });

  // Ensure initial state is consistent with HTML aria-selected
  const initialActive = Array.from(buttons).find(
    (btn) => btn.getAttribute('aria-selected') === 'true'
  );

  if (initialActive) {
    activateTab(initialActive.dataset.tab, buttons, panels);
  } else {
    // Default to first tab if none is pre-selected
    activateTab(buttons[0].dataset.tab, buttons, panels);
  }
}e.preventDefault();
        buttons[targetIndex].focus();
        activateTab(buttons[targetIndex].dataset.tab, buttons, panels);
      }
    });
  });

  // Ensure initial state is consistent with HTML aria-selected
  const initialActive = Array.from(buttons).find(
    (btn) => btn.getAttribute('aria-selected') === 'true'
  );

  if (initialActive) {
    activateTab(initialActive.dataset.tab, buttons, panels);
  } else {
    // Default to first tab if none is pre-selected
    activateTab(buttons[0].dataset.tab, buttons, panels);
  }
}