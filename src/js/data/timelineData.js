/**
 * TerraEcho — data/timelineData.js
 * Responsibility: Environmental metric values at milestone years.
 * Exposes an interpolation utility for smooth bar transitions.
 * No DOM. No events. No side effects.
 *
 * Data sources (approximate, for narrative accuracy):
 *   Forest cover  — Global Forest Watch, FAO Global Forest Resources Assessment
 *   Arctic sea ice — NSIDC (National Snow and Ice Data Center)
 *   CO2           — NOAA, Scripps Institution of Oceanography (Keeling Curve)
 *   Species       — IUCN Red List (cumulative threatened species estimates)
 *   Temp anomaly  — NASA GISS Surface Temperature Analysis
 *   Sea level     — CSIRO / Church & White sea level reconstruction
 */

/**
 * Metric values at each of the six milestone years.
 * Each entry defines the state of the planet at that point in time.
 *
 * Forest cover:  percentage of global land area covered by forest
 * Arctic ice:    September minimum extent in million km²
 * CO2:           atmospheric concentration in parts per million
 * Species:       cumulative IUCN threatened species (thousands)
 * tempAnomaly:   °C above pre-industrial baseline (1850–1900 average)
 * seaLevel:      mm above 1900 baseline
 */
export const MILESTONE_DATA = {
  1900: {
    forestCover: 35.0,   // ~35% of land forested pre-industrial expansion
    arcticIce:   13.5,   // million km² — relatively stable pre-warming
    co2:         295,    // ppm — just above pre-industrial ~280ppm
    species:     0.5,    // thousands — very few formally assessed
    tempAnomaly: -0.1,   // slight negative anomaly vs baseline
    seaLevel:    0,      // baseline
  },
  1950: {
    forestCover: 33.2,
    arcticIce:   13.2,
    co2:         311,
    species:     1.2,
    tempAnomaly:  0.1,
    seaLevel:    60,     // ~6cm rise by mid-century
  },
  1970: {
    forestCover: 31.5,
    arcticIce:   12.8,
    co2:         325,
    species:     2.8,
    tempAnomaly:  0.2,
    seaLevel:    90,
  },
  1990: {
    forestCover: 29.6,
    arcticIce:   12.0,
    co2:         354,
    species:     5.5,
    tempAnomaly:  0.45,
    seaLevel:    130,
  },
  2010: {
    forestCover: 27.8,
    arcticIce:    9.8,   // accelerating decline
    co2:         389,
    species:     9.0,
    tempAnomaly:  0.72,
    seaLevel:    180,
  },
  2024: {
    forestCover: 26.1,
    arcticIce:    7.2,   // record lows observed
    co2:         422,
    species:    11.5,
    tempAnomaly:  1.3,
    seaLevel:    220,
  },
};

/** Ordered milestone years — used for interpolation boundary lookup */
export const MILESTONE_YEARS = [1900, 1950, 1970, 1990, 2010, 2024];

/**
 * Bar display ranges — used to convert raw values to 0–100% fill.
 * min: value at which bar reads 0%
 * max: value at which bar reads 100%
 *
 * For forest and ice, 100% = best historical state (1900).
 * For CO2, 100% = worst state (2024). Bar fills as conditions worsen.
 */
export const BAR_RANGES = {
  forestCover: { min: 20,  max: 38,  invert: false }, // more = better = fuller bar
  arcticIce:   { min: 4,   max: 15,  invert: false }, // more = better = fuller bar
  co2:         { min: 270, max: 440, invert: true  }, // less CO2 = fuller bar (healthier)
};

/**
 * Linear interpolation between two values.
 * @param {number} a - Start value
 * @param {number} b - End value
 * @param {number} t - Progress 0.0 → 1.0
 * @returns {number}
 */
function lerp(a, b, t) {
  return a + (b - a) * t;
}

/**
 * Returns interpolated metric values for any year between 1900–2024.
 * Finds the two nearest milestone years and linearly interpolates all metrics.
 *
 * @param {number} year - Target year (will be clamped to 1900–2024)
 * @returns {object} Interpolated values for all six metrics
 */
export function getValuesForYear(year) {
  const clampedYear = Math.max(1900, Math.min(2024, year));

  // Exact milestone match — return directly, no interpolation needed
  if (MILESTONE_DATA[clampedYear]) {
    return { ...MILESTONE_DATA[clampedYear] };
  }

  // Find bounding milestone years
  let lowerYear = MILESTONE_YEARS[0];
  let upperYear = MILESTONE_YEARS[MILESTONE_YEARS.length - 1];

  for (let i = 0; i < MILESTONE_YEARS.length - 1; i++) {
    if (clampedYear >= MILESTONE_YEARS[i] && clampedYear < MILESTONE_YEARS[i + 1]) {
      lowerYear = MILESTONE_YEARS[i];
      upperYear = MILESTONE_YEARS[i + 1];
      break;
    }
  }

  const lower = MILESTONE_DATA[lowerYear];
  const upper = MILESTONE_DATA[upperYear];
  const t     = (clampedYear - lowerYear) / (upperYear - lowerYear);

  return {
    forestCover: lerp(lower.forestCover, upper.forestCover, t),
    arcticIce:   lerp(lower.arcticIce,   upper.arcticIce,   t),
    co2:         lerp(lower.co2,         upper.co2,         t),
    species:     lerp(lower.species,     upper.species,     t),
    tempAnomaly: lerp(lower.tempAnomaly, upper.tempAnomaly, t),
    seaLevel:    lerp(lower.seaLevel,    upper.seaLevel,    t),
  };
}

/**
 * Converts a raw metric value to a 0–100 bar fill percentage.
 * Respects inversion for CO2 (less CO2 = healthier = fuller bar).
 *
 * @param {'forestCover'|'arcticIce'|'co2'} metric
 * @param {number} value
 * @returns {number} Percentage 0–100
 */
export function toBarPercent(metric, value) {
  const range  = BAR_RANGES[metric];
  const ratio  = (value - range.min) / (range.max - range.min);
  const clamped = Math.max(0, Math.min(1, ratio));
  return range.invert
    ? (1 - clamped) * 100
    : clamped * 100;
}