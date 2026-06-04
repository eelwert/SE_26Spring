import type { PermissionCode, RoleCode } from '../types/domain';

export const roleLandingPaths: Record<RoleCode, string> = {
  modeler: '/modeler',
  analyst: '/analyst',
  admin: '/admin',
};

export const getLandingPathForRole = (role: RoleCode) => roleLandingPaths[role];

export const roleDefaultPermissions: Record<RoleCode, PermissionCode[]> = {
  modeler: ['project:read', 'project:write', 'asset:replace', 'layout:edit', 'task:dispatch'],
  analyst: ['project:read', 'multimodal:execute', 'simulation:run', 'task:dispatch'],
  admin: ['audit:read', 'version:rollback', 'settings:write'],
};
