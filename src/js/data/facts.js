/**
 * TerraEcho — data/facts.js
 * Responsibility: Narrative fact strings keyed to milestone years.
 * Snap logic: returns the fact for the most recent milestone year
 * that is less than or equal to the current year.
 * No DOM. No events. No side effects.
 */

/**
 * Each entry contains:
 *   text   — the displayed narrative (literary, first-person Earth voice)
 *   source — attribution shown below the fact card
 */
export const FACTS = {
  1900: {
    text: `At the turn of the twentieth century, vast forests still blanketed
           the continents. The atmosphere held just 295 parts per million of CO₂ —
           a world before the great acceleration, before the skies filled with the
           exhaust of ambition.`,
    source: 'NOAA / FAO Global Forest Resources Assessment',
  },
  1950: {
    text: `Post-war prosperity arrived with a cost written in smoke. Factory
           output doubled, automobiles multiplied, and for the first time scientists
           began measuring something quietly alarming: the air itself was changing.
           The Arctic, still vast, did not yet know what was coming.`,
    source: 'Scripps Institution of Oceanography — Keeling Curve origins',
  },
  1970: {
    text: `On April 22nd, 1970, twenty million Americans took to the streets
           for the first Earth Day. The Cuyahoga River had caught fire. Smog
           choked Los Angeles. Something had shifted — the planet had found
           a voice, and people had begun to listen.`,
    source: 'EPA founding record / Earth Day Network historical archive',
  },
  1990: {
    text: `The word "sustainability" entered the global vocabulary. Scientists
           at the IPCC published their first assessment: warming was unequivocal,
           human-caused, and already underway. The Arctic ice, though still
           expansive, had quietly begun its long retreat.`,
    source: 'IPCC First Assessment Report, 1990',
  },
  2010: {
    text: `The decade opened with record heat. Arctic sea ice reached its
           second-lowest September extent ever measured. CO₂ crossed 390 ppm —
           a concentration the Earth had not seen in three million years.
           Tipping points were no longer theoretical.`,
    source: 'NSIDC Arctic Sea Ice News / NOAA Annual Greenhouse Gas Index',
  },
  2024: {
    text: `For the first time in recorded history, the global average temperature
           exceeded 1.5°C above pre-industrial levels for a full calendar year.
           The window for action has not closed — but it is narrowing with
           every season that passes without change.`,
    source: 'NASA GISS / Copernicus Climate Change Service, 2024',
  },
};

/** Ordered milestone years matching timelineData.js */
const FACT_YEARS = [1900, 1950, 1970, 1990, 2010, 2024];

/**
 * Returns the milestone year whose fact should display for a given year.
 * Snaps to the most recent milestone year ≤ current year.
 * The previous fact always persists — there is no empty state.
 *
 * Examples:
 *   getFactYearFor(1900) → 1900
 *   getFactYearFor(1963) → 1950
 *   getFactYearFor(1970) → 1970
 *   getFactYearFor(2024) → 2024
 *
 * @param {number} year
 * @returns {number} Milestone year key for FACTS object
 */
export function getFactYearFor(year) {
  let result = FACT_YEARS[0];
  for (const milestoneYear of FACT_YEARS) {
    if (year >= milestoneYear) {
      result = milestoneYear;
    } else {
      break;
    }
  }
  return result;
}