import { afterEach, describe, expect, it, vi } from "vitest";

import {
  CIRCADIAN_PHASES,
  applyCircadianTheme,
  getCurrentCircadianPhase,
} from "../../lib/chromotherapy/biorhythm-theme-manager";
import {
  PHASE_COLORS,
  applyPhaseTheme,
  getPhaseColor,
} from "../../lib/chromotherapy/workflow-chromotherapy";
import {
  SOLFEGGIO_FREQUENCIES,
  playSolfeggioTone,
} from "../../lib/audio/solfeggio-audio";

describe("chromotherapy helpers", () => {
  afterEach(() => {
    document.documentElement.style.removeProperty("--phase-primary");
    document.documentElement.style.removeProperty("--phase-label");
    document.documentElement.style.removeProperty("--circadian-phase");
    vi.unstubAllGlobals();
  });

  it("getPhaseColor returns correct color for each phase", () => {
    expect(getPhaseColor("diagnose")).toBe("#0D9488");
    expect(getPhaseColor("analyse")).toBe("#7C3AED");
    expect(getPhaseColor("harmonize")).toBe("#059669");
    expect(getPhaseColor("report")).toBe("#D97706");
  });

  it("applyPhaseTheme sets CSS custom property", () => {
    applyPhaseTheme("diagnose");

    expect(document.documentElement.style.getPropertyValue("--phase-primary")).toBe("#0D9488");
    expect(document.documentElement.style.getPropertyValue("--phase-label")).toBe("Teal");
  });

  it("getCurrentCircadianPhase returns valid phase", () => {
    expect(Object.keys(CIRCADIAN_PHASES)).toContain(getCurrentCircadianPhase());
  });

  it("applyCircadianTheme sets circadian custom property", () => {
    applyCircadianTheme();

    expect(Object.keys(CIRCADIAN_PHASES)).toContain(
      document.documentElement.style.getPropertyValue("--circadian-phase"),
    );
  });

  it("SOLFEGGIO_FREQUENCIES contains all 6 frequencies", () => {
    expect(SOLFEGGIO_FREQUENCIES).toEqual({
      ut: 396,
      re: 417,
      mi: 528,
      fa: 639,
      sol: 741,
      la: 852,
    });
  });

  it("playSolfeggioTone respects prefers-reduced-motion", async () => {
    const audioContext = vi.fn();
    vi.stubGlobal("AudioContext", audioContext);
    vi.stubGlobal(
      "matchMedia",
      vi.fn().mockReturnValue({
        matches: true,
        media: "(prefers-reduced-motion: reduce)",
        onchange: null,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }),
    );

    await playSolfeggioTone("mi", 10);

    expect(audioContext).not.toHaveBeenCalled();
  });

  it("PHASE_COLORS covers all 4 workflow phases", () => {
    expect(Object.keys(PHASE_COLORS).sort()).toEqual([
      "analyse",
      "diagnose",
      "harmonize",
      "report",
    ]);
  });
});
