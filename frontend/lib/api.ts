import type { AnalyzeResponse, ChatResponse, EmailDraft, ExportFormat, Health, Mode, Report, Segment } from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request(path: string, init?: RequestInit): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, init);
  } catch {
    throw new Error(`Impossible de joindre l'API (${API_URL}). Le serveur FastAPI est-il démarré ?`);
  }
  if (!res.ok) {
    let detail = `Erreur ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail.map((d: { msg: string }) => d.msg).join(" ; ");
    } catch {
      /* corps non JSON */
    }
    throw new Error(detail);
  }
  return res;
}

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await request(path, init);
  return res.json() as Promise<T>;
}

const post = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const getHealth = () => json<Health>("/api/health");

export const getSample = () => json<{ filename: string; text: string; meeting_date: string }>("/api/sample");

export const analyze = (p: { text: string; filename: string; mode: Mode; meeting_date: string | null }) =>
  json<AnalyzeResponse>("/api/analyze", post(p));

export async function transcribeAudio(file: File): Promise<string> {
  const form = new FormData();
  form.append("file", file);
  const res = await request("/api/transcribe", { method: "POST", body: form });
  return (await res.json()).text as string;
}

export const chat = (p: { question: string; segments: Segment[]; mode: Mode }) =>
  json<ChatResponse>("/api/chat", post(p));

export const exportEmail = (report: Report) => json<EmailDraft>("/api/export/email", post(report));

export async function downloadExport(fmt: ExportFormat, report: Report, baseName: string): Promise<void> {
  const res = await request(`/api/export/${fmt}`, post(report));
  const url = URL.createObjectURL(await res.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = `${baseName}.${fmt}`;
  a.click();
  URL.revokeObjectURL(url);
}
