export const PHASE_COLORS = {
  diagnose: { primary: "#0D9488", label: "Teal" },
  analyse: { primary: "#7C3AED", label: "Violet" },
  harmonize: { primary: "#059669", label: "Emerald" },
  report: { primary: "#D97706", label: "Gold" },
} as const;

export type WorkflowPhase = keyof typeof PHASE_COLORS;

export function getPhaseColor(phase: WorkflowPhase): string {
  return PHASE_COLORS[phase].primary;
}

export function applyPhaseTheme(phase: WorkflowPhase): void {
  if (typeof document === "undefined") {
    return;
  }

  const phaseColor = PHASE_COLORS[phase];
  document.documentElement.style.setProperty("--phase-primary", phaseColor.primary);
  document.documentElement.style.setProperty("--phase-label", phaseColor.label);
}
