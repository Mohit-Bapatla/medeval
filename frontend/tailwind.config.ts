import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#172026",
        graphite: "#3a4650",
        clinical: "#0f766e",
        signal: "#b45309",
        surface: "#f7f9fb",
        line: "#d7dee5",
      },
    },
  },
  plugins: [],
};

export default config;
