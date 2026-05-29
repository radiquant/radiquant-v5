import type { RoleName } from '../api/types';

export interface RoleProjectionCopy {
  role: RoleName;
  title: string;
  description: string;
  allowedNextStep: string;
}

export const ROLE_PROJECTIONS: RoleProjectionCopy[] = [
  {
    role: 'client',
    title: 'Klientenansicht',
    description: 'Ruhige Zusammenfassung für Wohlbefinden und Orientierung.',
    allowedNextStep: 'Klientenfunktionen folgen nach Contract-Freigabe.',
  },
  {
    role: 'therapist',
    title: 'Therapeutische Arbeitsansicht',
    description: 'Professionelle Übersicht mit klaren Freigabegrenzen.',
    allowedNextStep: 'Praxisdaten folgen nach Tenant- und Consent-Gates.',
  },
  {
    role: 'assistant',
    title: 'Assistenzansicht',
    description: 'Begrenzte Praxisunterstützung ohne administrative Bereiche.',
    allowedNextStep: 'Unterstützende Abläufe folgen nach API-Contract.',
  },
  {
    role: 'admin',
    title: 'Administrationsansicht',
    description: 'Betriebs- und Compliance-orientierte Shell.',
    allowedNextStep: 'Admin-Funktionen folgen nach Admin-Route-Gate.',
  },
  {
    role: 'researcher',
    title: 'Forschungsansicht',
    description: 'Anonymisierte Labs-Perspektive als spätere Option.',
    allowedNextStep: 'Labs bleiben feature-flagged und geschlossen.',
  },
  {
    role: 'system',
    title: 'Systemrolle',
    description: 'Interne Service-Rolle ohne UI-Arbeitsfläche.',
    allowedNextStep: 'Interne Routen bleiben nicht öffentlich exponiert.',
  },
];
