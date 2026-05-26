import { FormEvent, useMemo, useState } from 'react';
import { GitCompareArrows, RotateCcw, Save, Search } from 'lucide-react';
import { useSession } from '../context/SessionContext';
import { useWorkspace } from '../context/WorkspaceContext';
import { Button, EmptyState, Field, Panel, SectionHeader, StatusBadge } from '../components/ui';

export function AuditPage() {
  const { hasPermission } = useSession();
  const {
    selectedProjectId,
    selectedSceneId,
    auditLogs,
    versions,
    createSnapshot,
    rollbackVersion,
  } = useWorkspace();
  const [query, setQuery] = useState('');
  const [summary, setSummary] = useState('人工保存：完成当前场景审计快照');
  const [isSaving, setIsSaving] = useState(false);
  const [rollingBack, setRollingBack] = useState<string | null>(null);

  const filteredLogs = useMemo(
    () =>
      auditLogs.filter((log) => {
        const haystack = `${log.actor} ${log.eventType} ${log.target} ${log.traceId}`.toLowerCase();
        return haystack.includes(query.toLowerCase());
      }),
    [auditLogs, query],
  );

  const sceneVersions = versions.filter((version) => !selectedSceneId || version.sceneId === selectedSceneId);

  const handleSnapshot = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedProjectId || !selectedSceneId) return;
    setIsSaving(true);
    try {
      await createSnapshot({ projectId: selectedProjectId, sceneId: selectedSceneId, summary });
    } finally {
      setIsSaving(false);
    }
  };

  const handleRollback = async (snapshotId: string) => {
    setRollingBack(snapshotId);
    try {
      await rollbackVersion(snapshotId);
    } finally {
      setRollingBack(null);
    }
  };

  return (
    <div className="page-stack">
      <SectionHeader title="审计与版本" description="追加式日志、证据哈希、版本快照、差异对比与回滚。" />

      <div className="audit-layout">
        <Panel>
          <SectionHeader title="版本快照" />
          <form className="snapshot-form" onSubmit={(event) => void handleSnapshot(event)}>
            <Field label="快照说明">
              <input value={summary} onChange={(event) => setSummary(event.target.value)} />
            </Field>
            <Button type="submit" isLoading={isSaving}>
              <Save size={16} />
              保存快照
            </Button>
          </form>
          <div className="version-timeline">
            {sceneVersions.map((version) => (
              <div key={version.id} className="version-item">
                <div className="timeline-dot" />
                <div>
                  <strong>{version.version}</strong>
                  <span>{version.summary}</span>
                  <small>
                    {version.author} / {new Date(version.createdAt).toLocaleString('zh-CN')} / {version.changeCount} changes
                  </small>
                </div>
                <div className="version-actions">
                  <Button size="sm" variant="secondary">
                    <GitCompareArrows size={14} />
                    差异
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    disabled={!hasPermission('version:rollback') || !version.rollbackable}
                    isLoading={rollingBack === version.id}
                    onClick={() => void handleRollback(version.id)}
                  >
                    <RotateCcw size={14} />
                    回滚
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel>
          <SectionHeader title="差异预览" />
          {sceneVersions.length >= 2 ? (
            <div className="diff-preview">
              <div>
                <span>对象新增</span>
                <strong>+{sceneVersions[0].changeCount}</strong>
              </div>
              <div>
                <span>材质替换</span>
                <strong>12</strong>
              </div>
              <div>
                <span>布局调整</span>
                <strong>8</strong>
              </div>
              <div>
                <span>规则版本</span>
                <strong>{sceneVersions[0].version}</strong>
              </div>
            </div>
          ) : (
            <EmptyState title="快照不足" description="至少两个快照后可比较差异。" />
          )}
        </Panel>
      </div>

      <Panel>
        <SectionHeader
          title="审计日志"
          action={
            <div className="search-box">
              <Search size={16} />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索 trace、事件、人员" />
            </div>
          }
        />
        {filteredLogs.length ? (
          <div className="audit-table">
            {filteredLogs.map((log) => (
              <div key={log.id} className="audit-row">
                <div>
                  <strong>{log.eventType}</strong>
                  <span>{log.traceId}</span>
                </div>
                <span>{log.actor}</span>
                <StatusBadge status={log.severity} />
                <StatusBadge status={log.result} />
                <code>{log.evidenceHash}</code>
                <small>{new Date(log.createdAt).toLocaleString('zh-CN')}</small>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="无匹配记录" description="调整搜索词后重试。" />
        )}
      </Panel>
    </div>
  );
}
