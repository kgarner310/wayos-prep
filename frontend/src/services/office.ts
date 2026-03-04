/**
 * Office.js integration helpers for Outlook Add-in.
 *
 * These functions interact with the Outlook mailbox context:
 * - Read calendar appointment subject to auto-suggest industry
 * - Insert text into a new email compose window
 * - Set email subject line
 */

declare const Office: any;

let _initialized = false;
let _resolveReady: () => void;
const _ready = new Promise<void>((resolve) => {
  _resolveReady = resolve;
});

/** Initialize Office.js — call once at app startup. */
export function initOffice(): Promise<void> {
  if (_initialized) return _ready;
  _initialized = true;

  if (typeof Office !== 'undefined' && Office.onReady) {
    Office.onReady(() => _resolveReady());
  } else {
    // Running outside Outlook (standalone browser dev) — resolve immediately
    _resolveReady();
  }
  return _ready;
}

/** Check if we're actually running inside Outlook. */
export function isOutlookContext(): boolean {
  try {
    return (
      typeof Office !== 'undefined' &&
      Office.context &&
      Office.context.mailbox !== undefined
    );
  } catch {
    return false;
  }
}

/**
 * Try to read the current appointment subject (e.g. "Meeting with ABC Roofing").
 * Returns null if not in an appointment context.
 */
export function getAppointmentSubject(): Promise<string | null> {
  return new Promise((resolve) => {
    if (!isOutlookContext()) {
      resolve(null);
      return;
    }
    try {
      const item = Office.context.mailbox.item;
      if (!item) {
        resolve(null);
        return;
      }
      // Appointment read mode — subject is a string
      if (typeof item.subject === 'string') {
        resolve(item.subject);
        return;
      }
      // Appointment compose mode — subject is async
      if (item.subject && typeof item.subject.getAsync === 'function') {
        item.subject.getAsync((result: any) => {
          resolve(result.status === 'succeeded' ? result.value : null);
        });
        return;
      }
      resolve(null);
    } catch {
      resolve(null);
    }
  });
}

/**
 * Open a new email compose window and insert the given body text.
 * Works from message read, compose, or appointment contexts.
 */
export function composeEmailWithBody(
  subject: string,
  body: string
): Promise<boolean> {
  return new Promise((resolve) => {
    if (!isOutlookContext()) {
      // Fallback: copy to clipboard and alert
      navigator.clipboard.writeText(body).then(
        () => resolve(true),
        () => resolve(false)
      );
      return;
    }

    try {
      const mailbox = Office.context.mailbox;

      // Use displayNewMessageForm to open a compose window
      mailbox.displayNewMessageForm({
        subject: subject,
        htmlBody: body.replace(/\n/g, '<br/>'),
      });
      resolve(true);
    } catch {
      resolve(false);
    }
  });
}

/**
 * Insert text into the currently open compose email body.
 * Only works when the add-in is opened from a compose context.
 */
export function insertIntoCurrentEmail(body: string): Promise<boolean> {
  return new Promise((resolve) => {
    if (!isOutlookContext()) {
      resolve(false);
      return;
    }
    try {
      const item = Office.context.mailbox.item;
      if (item && item.body && typeof item.body.setAsync === 'function') {
        item.body.setAsync(body, { coercionType: 'text' }, (result: any) => {
          resolve(result.status === 'succeeded');
        });
      } else {
        resolve(false);
      }
    } catch {
      resolve(false);
    }
  });
}
