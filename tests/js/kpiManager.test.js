// tests/js/kpiManager.test.js
import { describe, it, expect } from 'vitest';

describe('kpiManager module', () => {
    it('should load without syntax errors', async () => {
        let error = null;
        try {
            await import('../../src/static/js/managers/kpiManager.js');
        } catch (e) {
            error = e;
        }
        expect(error).toBe(null);
    });
}); 