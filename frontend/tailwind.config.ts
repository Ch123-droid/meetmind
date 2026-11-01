import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  darkMode: "media",
  theme: {
    extend: {
      colors: {
        navy: { DEFAULT: "#1F3A5F", 700: "#2E5C8A", 50: "#EAF3F7" },
        teal: { DEFAULT: "#0E9AA7", 600: "#0B7F8A" },
        accent: "#E8833A",
      },
      boxShadow: { card: "0 1px 2px rgba(31,58,95,.08), 0 8px 24px rgba(31,58,95,.08)" },
    },
  },
  plugins: [],
};
export default config;
