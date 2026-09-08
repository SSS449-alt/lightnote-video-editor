import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      colors: {
        accent: "#6366f1",
        "accent-light": "#818cf8",
        surface: "#12121a",
        "surface-2": "#1a1a26",
        "text-primary": "#f1f1f5",
        "text-secondary": "#8888aa",
      },
    },
  },
  plugins: [],
};

export default config;