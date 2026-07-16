import { describe, it, expect } from 'vitest';
import { homeRouteForRole } from '@/routes/roleHome';

describe('homeRouteForRole', () => {
  it('routes a student to the root path', () => {
    expect(homeRouteForRole('student')).toBe('/');
  });

  it('routes a teacher to /teacher', () => {
    expect(homeRouteForRole('teacher')).toBe('/teacher');
  });

  it('routes a parent to /parent', () => {
    expect(homeRouteForRole('parent')).toBe('/parent');
  });

  it('routes an admin to /admin', () => {
    expect(homeRouteForRole('admin')).toBe('/admin');
  });

  it('returns a distinct route for every role (no accidental collisions)', () => {
    const roles = ['student', 'teacher', 'parent', 'admin'] as const;
    const routes = roles.map(homeRouteForRole);
    expect(new Set(routes).size).toBe(roles.length);
  });
});
