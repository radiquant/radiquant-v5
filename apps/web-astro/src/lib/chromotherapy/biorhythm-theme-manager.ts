export const CIRCADIAN_PHASES = {
  dawn: { hours: [5, 6, 7], theme: "warm-light" },
  morning: { hours: [8, 9, 10, 11], theme: "bright-focus" },
  afternoon: { hours: [12, 13, 14, 15, 16], theme: "neutral" },
  evening: { hours: [17, 18, 19, 20], theme: "warm-soft" },
  night: { hours: [21, 22, 23, 0, 1, 2, 3, 4], theme: "dark-calm" },
} as const;

export function getCurrentCircadianPhase(): string {
  const currentHour = new Date().getHours();

  for (const [phase, config] of Object.entries(CIRCADIAN_PHASES)) {
    if ((config.hours as readonly number[]).includes(currentHour)) {
      return phase;
    }
  }

  return "afternoon";
}

export function applyCircadianTheme(): void {
  if (typeof document === "undefined") {
    return;
  }

  document.documentElement.style.setProperty(
    "--circadian-phase",
    getCurrentCircadianPhase(),
  );
}
