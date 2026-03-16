/**
 * Normalizes a team name to match the kpOvrStats format (the site's source of truth).
 * Strips periods and apostrophes so names like "Mount St. Mary's" -> "Mount St Marys".
 */
export function normalizeTeamName(name) {
  return String(name).replace(/\./g, '').replace(/'/g, '');
}
