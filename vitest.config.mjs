import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // Ya no usamos el environment global de jsdom
    // environment: 'jsdom', 
    include: ['**/*.{test,spec}.js'],
  },
}); 