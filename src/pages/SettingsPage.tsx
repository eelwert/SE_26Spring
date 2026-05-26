import { useState } from 'react';
import { Lock, PlugZap, Save, ShieldCheck, SlidersHorizontal, ToggleLeft, ToggleRight } from 'lucide-react';
import { useWorkspace } from '../context/WorkspaceContext';
import type { RuntimeSetting } from '../types/domain';
import { Button, Field, Panel, SectionHeader, StatusBadge } from '../components/ui';

const categoryLabels: Record<RuntimeSetting['category'], string> = {
  rbac: '权限',
  plugin: '插件',
  llm: 'LLM',
  simulation: '仿真',
  audit: '审计',
};

export function SettingsPage() {
  const {
    settings,
    functions,
    health,
    updateSetting,
    togglePluginFunction,
  } = useWorkspace();
  const [editingValues, setEditingValues] = useState<Record<string, RuntimeSetting['value']>>({});
  const [busyKey, setBusyKey] = useState<string | null>(null);

  const getValue = (setting: RuntimeSetting) => editingValues[setting.id] ?? setting.value;

  const handleSave = async (setting: RuntimeSetting) => {
    setBusyKey(setting.id);
    try {
      await updateSetting(setting.id, getValue(setting));
    } finally {
      setBusyKey(null);
    }
  };

  const handleToggleFunction = async (name: string, enabled: boolean) => {
    setBusyKey(name);
    try {
      await togglePluginFunction(name, enabled);
    } finally {
      setBusyKey(null);
    }
  };

  return (
    <div className="page-stack">
      <SectionHeader title="系统设置" description="RBAC、插件白名单、LLM 阈值、仿真刷新与审计策略。" />

      <div className="settings-grid">
        <Panel>
          <SectionHeader title="运行参数" />
          <div className="settings-list">
            {settings.map((setting) => (
              <div key={setting.id} className="setting-row">
                <div>
                  <strong>{setting.title}</strong>
                  <span>{setting.description}</span>
                  <StatusBadge status={categoryLabels[setting.category]} />
                </div>
                <Field label="值">
                  {typeof setting.value === 'boolean' ? (
                    <button
                      type="button"
                      className={`toggle-button ${getValue(setting) ? 'active' : ''}`}
                      disabled={setting.locked}
                      onClick={() => setEditingValues((current) => ({ ...current, [setting.id]: !getValue(setting) }))}
                    >
                      {getValue(setting) ? <ToggleRight size={20} /> : <ToggleLeft size={20} />}
                      {getValue(setting) ? '开启' : '关闭'}
                    </button>
                  ) : (
                    <input
                      value={String(getValue(setting))}
                      disabled={setting.locked}
                      onChange={(event) => {
                        const next = typeof setting.value === 'number' ? Number(event.target.value) : event.target.value;
                        setEditingValues((current) => ({ ...current, [setting.id]: next }));
                      }}
                    />
                  )}
                </Field>
                <Button size="sm" variant="secondary" disabled={setting.locked} isLoading={busyKey === setting.id} onClick={() => void handleSave(setting)}>
                  {setting.locked ? <Lock size={14} /> : <Save size={14} />}
                  保存
                </Button>
              </div>
            ))}
          </div>
        </Panel>

        <Panel>
          <SectionHeader title="服务健康" />
          <div className="service-list">
            {health.map((item) => (
              <div key={item.id} className="service-row">
                <div>
                  <strong>{item.name}</strong>
                  <span>{item.description}</span>
                </div>
                <StatusBadge status={item.status} />
                <small>{item.latencyMs}ms</small>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <Panel>
        <SectionHeader title="插件函数白名单" />
        <div className="plugin-grid">
          {functions.map((func) => (
            <div key={func.name} className="plugin-card">
              <div className="plugin-card-head">
                <PlugZap size={18} />
                <div>
                  <strong>{func.title}</strong>
                  <span>{func.name}</span>
                </div>
                <StatusBadge status={func.enabled ? 'healthy' : 'offline'} />
              </div>
              <p>{func.description}</p>
              <div className="plugin-meta">
                <span>{func.category}</span>
                <StatusBadge status={func.risk === 'high' ? 'critical' : func.risk === 'medium' ? 'warning' : 'info'} />
                <span>{func.averageMs}ms</span>
              </div>
              <Button
                size="sm"
                variant={func.enabled ? 'secondary' : 'primary'}
                isLoading={busyKey === func.name}
                onClick={() => void handleToggleFunction(func.name, !func.enabled)}
              >
                <SlidersHorizontal size={14} />
                {func.enabled ? '停用' : '启用'}
              </Button>
            </div>
          ))}
        </div>
      </Panel>

      <Panel>
        <SectionHeader title="权限策略摘要" />
        <div className="policy-grid">
          <div>
            <ShieldCheck size={20} />
            <strong>RBAC 主模型</strong>
            <span>菜单、按钮和高危操作按角色权限过滤。</span>
          </div>
          <div>
            <Lock size={20} />
            <strong>高危二次确认</strong>
            <span>回滚、白名单、批量替换等操作均写入审计。</span>
          </div>
          <div>
            <PlugZap size={20} />
            <strong>函数注册表</strong>
            <span>多模态计划只允许调用已启用白名单函数。</span>
          </div>
        </div>
      </Panel>
    </div>
  );
}
