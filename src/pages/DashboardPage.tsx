import { Activity, AlertTriangle, CheckCircle2, Clock3, ServerCog } from 'lucide-react';
import { useMemo } from 'react';
import { useSession } from '../context/SessionContext';
import { useWorkspace } from '../context/WorkspaceContext';
import { roleLabels } from '../types/domain';
import { EmptyState, MetricCard, Panel, ProgressBar, SectionHeader, StatusBadge } from '../components/ui';

const roleFocus = {
  modeler: ['资产替换任务', '模板联动配置', '草图/点集布局'],
  analyst: ['仿真指标回放', '多模态方案推演', '冲突热力分析'],
  admin: ['权限策略审计', '插件白名单', '版本快照回滚'],
};

export function DashboardPage() {
  const { session } = useSession();
  const { summary, selectedProject, selectedScene, tasks, simulations, auditLogs, health, projects } = useWorkspace();
  const role = session?.user.role ?? 'modeler';
  const recentTasks = tasks.slice(0, 5);
  const projectTasks = useMemo(
    () => tasks.filter((task) => task.projectId === selectedProject?.id),
    [selectedProject?.id, tasks],
  );
  const riskLogs = auditLogs.filter((log) => log.severity !== 'info').slice(0, 4);

  return (
    <div className="page-stack">
      <SectionHeader
        title={`${roleLabels[role]}工作台`}
        description={selectedProject && selectedScene ? `${selectedProject.name} / ${selectedScene.name}` : '等待选择项目场景'}
      />

      <div className="metrics-grid">
        <MetricCard label="项目总数" value={summary?.projectTotal ?? projects.length} meta="项目上下文" />
        <MetricCard label="运行任务" value={summary?.runningTasks ?? 0} meta="队列与插件" tone="warn" />
        <MetricCard label="失败任务" value={summary?.failedTasks ?? 0} meta="可重试/回滚" tone={(summary?.failedTasks ?? 0) > 0 ? 'bad' : 'good'} />
        <MetricCard label="仿真成功率" value={`${summary?.simulationSuccessRate ?? 0}%`} meta="车辆/人群" tone="good" />
        <MetricCard label="插件健康度" value={`${summary?.pluginHealthRate ?? 0}%`} meta="控制与执行平面" tone="good" />
      </div>

      <div className="dashboard-grid">
        <Panel className="wide-panel">
          <SectionHeader title="当前场景状态" />
          {selectedScene ? (
            <div className="scene-state">
              <div className="scene-preview">
                <div className="mini-map">
                  <span className="map-water" />
                  <span className="map-road r1" />
                  <span className="map-road r2" />
                  <span className="map-road r3" />
                  <span className="map-block m1" />
                  <span className="map-block m2" />
                  <span className="map-block m3" />
                  <span className="map-agent p1" />
                  <span className="map-agent p2" />
                </div>
              </div>
              <div className="scene-details">
                <div>
                  <span>模板</span>
                  <strong>{selectedScene.templateId}</strong>
                </div>
                <div>
                  <span>对象数量</span>
                  <strong>{selectedScene.objectCount.toLocaleString()}</strong>
                </div>
                <div>
                  <span>树木密度</span>
                  <strong>{selectedScene.treeDensity}%</strong>
                </div>
                <div>
                  <span>道路宽度</span>
                  <strong>{selectedScene.roadWidth}m</strong>
                </div>
                <div>
                  <span>天气/时间</span>
                  <strong>
                    {selectedScene.weather} {selectedScene.timeOfDay}
                  </strong>
                </div>
                <div>
                  <span>问题数</span>
                  <strong>{selectedScene.issueCount}</strong>
                </div>
              </div>
            </div>
          ) : (
            <EmptyState title="暂无场景" description="创建项目后会生成默认场景。" />
          )}
        </Panel>

        <Panel>
          <SectionHeader title="角色任务焦点" />
          <div className="focus-list">
            {roleFocus[role].map((item, index) => (
              <div key={item}>
                <span>{index + 1}</span>
                <strong>{item}</strong>
              </div>
            ))}
          </div>
        </Panel>

        <Panel>
          <SectionHeader title="项目任务负载" />
          {projectTasks.length ? (
            <div className="task-load">
              {projectTasks.slice(0, 4).map((task) => (
                <div key={task.id} className="compact-row">
                  <div>
                    <strong>{task.title}</strong>
                    <span>{task.functionName}</span>
                  </div>
                  <StatusBadge status={task.status} />
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="无项目任务" description="当前项目还没有调度记录。" />
          )}
        </Panel>

        <Panel className="wide-panel">
          <SectionHeader title="任务队列" />
          <div className="table-list">
            {recentTasks.map((task) => (
              <div key={task.id} className="table-row task-row">
                <div>
                  <strong>{task.title}</strong>
                  <span>{task.traceId}</span>
                </div>
                <StatusBadge status={task.status} />
                <div className="progress-cell">
                  <ProgressBar value={task.progress} />
                  <small>{task.progress}%</small>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel>
          <SectionHeader title="仿真回放" />
          {simulations.slice(0, 3).map((simulation) => (
            <div key={simulation.id} className="compact-row">
              <div>
                <strong>{simulation.type === 'combined' ? '综合仿真' : simulation.type === 'traffic' ? '车辆仿真' : '人群仿真'}</strong>
                <span>{simulation.rulesVersion}</span>
              </div>
              <StatusBadge status={simulation.status} />
            </div>
          ))}
        </Panel>

        <Panel>
          <SectionHeader title="审计告警" />
          {riskLogs.length ? (
            <div className="audit-mini">
              {riskLogs.map((log) => (
                <div key={log.id}>
                  {log.severity === 'critical' ? <AlertTriangle size={16} /> : <Clock3 size={16} />}
                  <span>{log.eventType}</span>
                  <StatusBadge status={log.severity} />
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="无告警" description="关键操作审计正常。" />
          )}
        </Panel>

        <Panel className="wide-panel">
          <SectionHeader title="运行健康" />
          <div className="health-grid">
            {health.map((item) => (
              <div key={item.id} className="health-item">
                <div>
                  {item.status === 'healthy' ? <CheckCircle2 size={18} /> : item.status === 'degraded' ? <Activity size={18} /> : <ServerCog size={18} />}
                  <strong>{item.name}</strong>
                </div>
                <StatusBadge status={item.status} />
                <ProgressBar value={item.successRate} />
                <span>
                  {item.latencyMs}ms / {item.successRate}%
                </span>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}
