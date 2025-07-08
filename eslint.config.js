// eslint.config.js
import globals from "globals";

export default [
  {
    files: ["src/static/js/**/*.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        ...globals.browser,
        "io": "readonly",
        "$": "readonly",
        "jQuery": "readonly",
        "bootstrap": "readonly",
        "Chart": "readonly"
      }
    },
    rules: {
      "no-unused-vars": "warn",
      "no-console": "off",
      "no-undef": "warn"
    }
  }
]; 