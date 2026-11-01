export type Priority = "haute" | "moyenne" | "basse";
export type Mode = "offline" | "claude";

export interface Action {
  description: string;
  responsable: string | null;
  echeance_texte: string | null;
  echeance: string | null;
  priorite: Priority;
  source_citation: string;
  horodatage: string | null;
  segment_index: number | null;
  verifie: boolean;
}

export interface Decision {
  decision: string;
  contexte: string;
  source_citation: string;
  horodatage: string | null;
  segment_index: number | null;
  verifie: boolean;
}

export interface Report {
  titre: string;
  date_reunion: string | null;
  resume_executif: string;
  participants: string[];
  points_cles: string[];
  decisions: Decision[];
  actions: Action[];
  questions_ouvertes: string[];
}

export interface Segment {
  text: string;
  speaker: string | null;
  start: number | null;
  timestamp: string | null;
}

export interface AnalyzeResponse {
  report: Report;
  segments: Segment[];
  mode: Mode;
  elapsed_seconds: number;
}

export interface Health {
  status: string;
  claude_available: boolean;
  model: string;
  audio_available: boolean;
  version: string;
}

export interface ChatResponse {
  answer: string;
  excerpts: Segment[];
}

export interface EmailDraft {
  subject: string;
  body: string;
}

export type ExportFormat = "docx" | "md" | "json" | "ics";
