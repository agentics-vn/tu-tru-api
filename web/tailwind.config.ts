import type { Config } from "tailwindcss";

/**
 * Design tokens lifted from LuangiaiBatTuDesignSystem ("Direction C").
 * The API is presentation-agnostic; this theme is the frontend's choice.
 */
const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        forest: { DEFAULT: "#1d3129", deep: "#0e1c14" },
        paper: { DEFAULT: "#f0ece2", warm: "#ede7d3" },
        cream: "#ede7d3",
        ink: "#18150e",
        muted: "#7a7050",
        gold: { DEFAULT: "#c5a55a", light: "#c9a84c", deep: "#9a7c22" },
        vermilion: "#a3201f",
        jade: { DEFAULT: "#5e7d5e", mute: "#7a9a80" },
        // Ngũ hành (data colors, kept distinct for readability on parchment)
        hanh: {
          moc: "#2f6f4f",
          hoa: "#a3201f",
          tho: "#9a7c22",
          kim: "#6f6a52",
          thuy: "#274b6d",
        },
      },
      borderColor: {
        hairline: "rgba(154,124,34,0.30)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Open Sans", "system-ui", "sans-serif"],
        serif: ["var(--font-sans)", "Open Sans", "system-ui", "sans-serif"],
        display: ["var(--font-sans)", "Open Sans", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "IBM Plex Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
