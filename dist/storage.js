import { emptyState, validateState } from './model.js';
export const STORAGE_KEY = 'achievement-journal:v1';
export function readJournal(storage) {
  try {
    const raw = storage.getItem(STORAGE_KEY);
    return { state: raw ? validateState(JSON.parse(raw)) : emptyState(), blocked: false };
  } catch {
    return { state: emptyState(), blocked: true };
  }
}
export function writeJournal(storage, state) {
  try {
    storage.setItem(STORAGE_KEY, JSON.stringify(validateState(state)));
    return true;
  } catch {
    return false;
  }
}
