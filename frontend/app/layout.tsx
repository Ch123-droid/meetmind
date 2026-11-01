import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MeetMind — comptes rendus de réunion par IA",
  description: "Transformez la transcription d'une réunion en décisions et en actions, chaque élément relié à sa source.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
