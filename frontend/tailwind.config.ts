import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#14213d",
        signal: "#2a9d8f",
        warning: "#e9c46a",
        danger: "#e76f51",
        panel: "#f8fafc",
      },
    },
  },
  plugins: [],
};

export default config;
