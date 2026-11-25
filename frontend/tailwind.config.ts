import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      colors: {
        canvas: "var(--bg-canvas)",
        surface: "var(--bg-surface)",
        subtle: "var(--bg-subtle)",
        hairline: "var(--border-hairline)",
        strong: "var(--border-strong)",
        ink: {
          primary: "var(--ink-primary)",
          secondary: "var(--ink-secondary)",
          muted: "var(--ink-muted)",
          inverse: "var(--ink-inverse)",
        },
        accent: {
          DEFAULT: "var(--accent-primary)",
          hover: "var(--accent-primary-hover)",
          subtle: "var(--accent-subtle)",
          border: "var(--accent-border)",
        },
        status: {
          critical: {
            ink: "var(--status-critical-ink)",
            bg: "var(--status-critical-bg)",
            border: "var(--status-critical-border)",
          },
          warning: {
            ink: "var(--status-warning-ink)",
            bg: "var(--status-warning-bg)",
            border: "var(--status-warning-border)",
          },
          healthy: {
            ink: "var(--status-healthy-ink)",
            bg: "var(--status-healthy-bg)",
            border: "var(--status-healthy-border)",
          },
        },
      },
      borderRadius: {
        panel: "var(--radius-panel)",
        control: "var(--radius-control)",
        badge: "var(--radius-badge)",
      },
      boxShadow: {
        overlay: "var(--shadow-overlay)",
      },
    },
  },
  plugins: [],
};

export default config;
