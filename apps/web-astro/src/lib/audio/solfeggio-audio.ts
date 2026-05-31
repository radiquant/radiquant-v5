export const FEATURE_ADAPTIVE_UX = import.meta.env.PUBLIC_FEATURE_ADAPTIVE_UX === "true";

export const SOLFEGGIO_FREQUENCIES = {
  ut: 396,
  re: 417,
  mi: 528,
  fa: 639,
  sol: 741,
  la: 852,
} as const;

type SolfeggioKey = keyof typeof SOLFEGGIO_FREQUENCIES;

type WindowWithWebkitAudio = Window &
  typeof globalThis & {
    webkitAudioContext?: typeof AudioContext;
  };

export async function playSolfeggioTone(
  freq: SolfeggioKey,
  durationMs: number = 1000,
): Promise<void> {
  if (!FEATURE_ADAPTIVE_UX) {
    return;
  }

  if (typeof window === "undefined") {
    return;
  }

  if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) {
    return;
  }

  const audioWindow = window as WindowWithWebkitAudio;
  const AudioContextConstructor = audioWindow.AudioContext ?? audioWindow.webkitAudioContext;
  if (!AudioContextConstructor) {
    return;
  }

  const audioContext = new AudioContextConstructor();
  const oscillator = audioContext.createOscillator();
  const gain = audioContext.createGain();
  const durationSeconds = Math.max(durationMs, 0) / 1000;

  oscillator.type = "sine";
  oscillator.frequency.value = SOLFEGGIO_FREQUENCIES[freq];
  gain.gain.setValueAtTime(0.05, audioContext.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.0001, audioContext.currentTime + durationSeconds);
  oscillator.connect(gain);
  gain.connect(audioContext.destination);
  oscillator.start();

  await new Promise<void>((resolve) => {
    window.setTimeout(() => {
      oscillator.stop();
      void audioContext.close().finally(resolve);
    }, durationMs);
  });
}
