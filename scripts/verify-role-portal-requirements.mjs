import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const read = (path) => readFileSync(path, 'utf8');

const app = read('src/App.tsx');
const login = read('src/pages/LoginPage.tsx');
const layout = read('src/components/AppLayout.tsx');
const modeler = read('src/pages/ModelerPortalPage.tsx');
const analyst = read('src/pages/AnalystPortalPage.tsx');
const admin = read('src/pages/AdminPortalPage.tsx');

assert.match(app, /function RoleRoute/, 'App.tsx should define a role-aware route guard.');
assert.match(app, /path="\/modeler"/, 'App.tsx should expose /modeler.');
assert.match(app, /path="\/analyst"/, 'App.tsx should expose /analyst.');
assert.match(app, /path="\/admin"/, 'App.tsx should expose /admin.');
assert.match(app, /allowedRole=\{"modeler"\}/, '/modeler should be guarded for modeler.');
assert.match(app, /allowedRole=\{"analyst"\}/, '/analyst should be guarded for analyst.');
assert.match(app, /allowedRole=\{"admin"\}/, '/admin should be guarded for admin.');

assert.match(login, /getLandingPathForRole/, 'Login should redirect by role after authentication.');
assert.match(layout, /roleNavItems/, 'Navigation should be role-specific.');

assert.match(modeler, /进入 Blender 插件系统/, 'Modeler page should include Blender plugin entry.');
assert.match(modeler, /道路纹理贴图/, 'Modeler page should include road texture controls.');
assert.match(modeler, /3D 资产实例化/, 'Modeler page should include 3D asset instancing controls.');
assert.match(modeler, /模板编号/, 'Modeler page should include template number input.');
assert.match(modeler, /\(0,0\),\(10,0\),\(10,10\)/, 'Modeler page should include coordinate-set layout input.');
assert.match(modeler, /手绘草图/, 'Modeler page should include sketch upload workflow.');

assert.match(analyst, /自然语言指令/, 'Analyst page should include natural language command controls.');
assert.match(analyst, /结构化 JSON/, 'Analyst page should preview structured JSON.');
assert.match(analyst, /交通灯/, 'Analyst page should include traffic light simulation display.');
assert.match(analyst, /自然景观/, 'Analyst page should include natural landscape controls.');

assert.match(admin, /删除用户/, 'Admin page should include admin-only delete user action.');
assert.match(admin, /审核插件/, 'Admin page should include admin-only plugin review action.');

console.log('Role portal frontend requirements verified.');
