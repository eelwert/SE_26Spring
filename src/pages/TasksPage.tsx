import { FormEvent, useEffect, useMemo, useState } from 'react';
import { GitBranch, Play, RefreshCw, ShieldAlert, Workflow } from 'lucide-react';
import { useSession } from '../context/SessionContext';
import { useWorkspace } from '../context/WorkspaceContext';
import { Button, EmptyState, Field, Panel, ProgressBar, SectionHeader, StatusBadge } from '../components/ui';

type ParamFieldType = 'text' | 'textarea' | 'number' | 'integer' | 'boolean' | 'select';
type SelectOutputType = 'string' | 'number' | 'integer';

interface ParamOption {
  label: string;
  value: string | number;
}

interface ParamField {
  name: string;
  label: string;
  type: ParamFieldType;
  required?: boolean;
  defaultValue?: string | number | boolean;
  min?: number;
  max?: number;
  step?: number;
  placeholder?: string;
  hint?: string;
  options?: ParamOption[];
  valueType?: SelectOutputType;
}

const furnitureOptions: ParamOption[] = [
  { label: '木质野餐桌', value: 'wooden_picnic_table' },
  { label: '小型消防罐', value: 'small_lpg_tank' },
  { label: '小黄鸭玩具', value: 'rubber_duck_toy' },
];

const roadTextureOptions: ParamOption[] = [
  { label: 'Road 4 clean', value: 'road_4_clean' },
  { label: 'Road 8 dirty', value: 'road_8_dirty' },
  { label: 'Road 11 dirty', value: 'road_11_dirty' },
  { label: 'SpongeBob road', value: 'spongebob_fun' },
];

const pavementTextureOptions: ParamOption[] = [
  { label: 'Pavement 25', value: 'pavement_25' },
  { label: 'Tiles 038', value: 'tiles_038' },
  { label: 'Patrick pavement', value: 'patrick_fun' },
];

const sceneTemplateOptions: ParamOption[] = [
  { label: '0 - 滨水街区', value: 0 },
  { label: '1 - 商业街', value: 1 },
  { label: '2 - 交通枢纽', value: 2 },
];

const weatherOptions: ParamOption[] = [
  { label: '晴', value: '晴' },
  { label: '多云', value: '多云' },
  { label: '雨', value: '雨' },
  { label: '夜间', value: '夜间' },
];

const boolDefault = (name: string, label: string, defaultValue = true): ParamField => ({
  name,
  label,
  type: 'boolean',
  defaultValue,
});

const numberField = (
  name: string,
  label: string,
  defaultValue: number,
  extra: Partial<ParamField> = {},
): ParamField => ({
  name,
  label,
  type: extra.type ?? 'number',
  defaultValue,
  step: extra.type === 'integer' ? 1 : 0.1,
  ...extra,
});

const PLUGIN_PARAM_SCHEMAS: Record<string, ParamField[]> = {
  replace_asset_batch: [
    { name: 'asset_id', label: '资产 ID', type: 'text', required: true, defaultValue: 'asset-tree-ginkgo' },
    {
      name: 'target_type',
      label: '替换目标',
      type: 'select',
      required: true,
      defaultValue: 'tree',
      options: [
        { label: '树木', value: 'tree' },
        { label: '道路材质', value: 'road_material' },
        { label: '座椅', value: 'seat' },
        { label: '建筑立面', value: 'building_facade' },
        { label: '车辆', value: 'vehicle' },
      ],
    },
  ],
  apply_template_linkage: [
    {
      name: 'template_id',
      label: '模板编号',
      type: 'select',
      valueType: 'integer',
      required: true,
      defaultValue: 1,
      options: Array.from({ length: 10 }, (_, index) => ({ label: `模板 ${index}`, value: index })),
    },
    numberField('tree_density', '树木密度', 60, { type: 'integer', min: 0, max: 100, required: true, step: 1 }),
    numberField('road_width', '道路宽度(m)', 8, { min: 1, max: 60, required: true }),
  ],
  set_weather_lighting: [
    { name: 'weather', label: '天气', type: 'select', required: true, defaultValue: '多云', options: weatherOptions },
    { name: 'time_of_day', label: '时间', type: 'text', required: true, defaultValue: '16:30', placeholder: 'HH:mm' },
  ],
  dispatch_blender_job: [
    { name: 'function_plan', label: '函数计划标识', type: 'textarea', defaultValue: 'manual-plan', hint: '高级任务可填写计划名称或后端约定的计划引用。' },
    { name: 'idempotency_key', label: '幂等键', type: 'text', defaultValue: 'manual-dispatch' },
  ],
  solve_point_layout: [
    { name: 'point_set', label: '点集', type: 'textarea', required: true, defaultValue: '0,0;20,0;20,20;0,20' },
    { name: 'topology_rules', label: '拓扑规则', type: 'textarea', defaultValue: 'closed_block' },
  ],
  extract_sketch_topology: [
    { name: 'attachment_ref', label: '草图附件引用', type: 'text', required: true, defaultValue: 'road-sketch.png' },
    numberField('scale', '比例尺', 1, { min: 0.01, max: 100 }),
  ],
  run_traffic_simulation: [
    { name: 'rules_version', label: '规则版本', type: 'text', required: true, defaultValue: 'traffic-r1' },
    numberField('seed', '随机种子', 42, { type: 'integer', min: 0, step: 1 }),
  ],
  run_crowd_simulation: [
    { name: 'rules_version', label: '规则版本', type: 'text', required: true, defaultValue: 'crowd-r1' },
    numberField('agent_count', '行人数量', 80, { type: 'integer', min: 0, max: 10000, step: 1 }),
    numberField('seed', '随机种子', 42, { type: 'integer', min: 0, step: 1 }),
  ],
  rollback_scene_version: [
    { name: 'snapshot_id', label: '快照 ID', type: 'text', required: true, placeholder: 'snapshot-xxx' },
  ],
  set_street_width: [
    numberField('width', '道路宽度(m)', 8, { min: 1, max: 60, required: true }),
  ],
  set_lane_amount: [
    numberField('lanes', '车道数量', 4, { type: 'integer', min: 1, max: 12, required: true, step: 1 }),
  ],
  set_tree_density: [
    numberField('density', '树木密度', 0.5, { min: 0, max: 1, required: true, step: 0.05, hint: '插件当前使用 0 到 1 的密度值。' }),
  ],
  set_street_lights: [boolDefault('enable', '开启路灯', true)],
  toggle_traffic: [boolDefault('enable', '启用交通元素', true)],
  apply_scene_template: [
    {
      name: 'template_id',
      label: '场景模板',
      type: 'select',
      valueType: 'integer',
      required: true,
      defaultValue: 0,
      options: sceneTemplateOptions,
    },
  ],
  apply_road_texture: [
    { name: 'texture_id', label: '道路纹理', type: 'select', required: true, defaultValue: 'road_4_clean', options: roadTextureOptions },
  ],
  apply_pavement_texture: [
    { name: 'texture_id', label: '人行道纹理', type: 'select', required: true, defaultValue: 'pavement_25', options: pavementTextureOptions },
  ],
  delete_furniture: [
    { name: 'asset_id', label: '家具资产', type: 'select', required: true, defaultValue: 'wooden_picnic_table', options: furnitureOptions },
  ],
  place_furniture: [
    { name: 'asset_id', label: '家具资产', type: 'select', required: true, defaultValue: 'wooden_picnic_table', options: furnitureOptions },
    numberField('min_count', '最少数量', 5, { type: 'integer', min: 0, max: 100, step: 1 }),
    numberField('max_count', '最多数量', 10, { type: 'integer', min: 0, max: 100, step: 1 }),
    numberField('spacing', '间距(m)', 8, { min: 0, max: 100 }),
    numberField('scale', '缩放', 1, { min: 0.01, max: 20 }),
    boolDefault('randomize', '随机布局', true),
    numberField('placement_offset', '摆放偏移(m)', 0, { min: -50, max: 50 }),
    boolDefault('clear_previous', '清除旧资产', false),
  ],
  apply_layout_template: [
    { name: 'layout_id', label: '布局模板', type: 'select', required: true, defaultValue: 'linear_blocks', options: [{ label: 'Linear Blocks', value: 'linear_blocks' }] },
    numberField('rows', '行数', 2, { type: 'integer', min: 1, max: 20, step: 1 }),
    numberField('columns', '列数', 3, { type: 'integer', min: 1, max: 20, step: 1 }),
    boolDefault('clear_previous', '替换旧布局', true),
  ],
  list_buildings: [],
  place_building: [
    numberField('x', '中心 X', 0, { required: true }),
    numberField('y', '中心 Y', 0, { required: true }),
    numberField('width', '宽度(m)', 10, { min: 1, max: 500 }),
    numberField('depth', '深度(m)', 10, { min: 1, max: 500 }),
    numberField('height', '高度(m)', 20, { min: 1, max: 1000 }),
    { name: 'color', label: '颜色', type: 'text', defaultValue: '#A0A0A0', placeholder: '#A0A0A0' },
  ],
  move_building: [
    { name: 'building_id', label: '建筑 ID', type: 'text', required: true, placeholder: 'B_0001' },
    numberField('x', '目标 X', 0, { required: true }),
    numberField('y', '目标 Y', 0, { required: true }),
  ],
  delete_building: [
    { name: 'building_id', label: '建筑 ID', type: 'text', required: true, placeholder: 'B_0001' },
  ],
  query_space: [
    numberField('x', '中心 X', 0, { required: true }),
    numberField('y', '中心 Y', 0, { required: true }),
    numberField('width', '宽度(m)', 10, { min: 1, required: true }),
    numberField('depth', '深度(m)', 10, { min: 1, required: true }),
  ],
  generate_terrain: [
    numberField('x', '中心 X', 0),
    numberField('y', '中心 Y', 0),
    numberField('hill_height', '山丘高度(m)', 20, { min: 0, max: 300 }),
    numberField('noise_scale', '噪声比例', 3, { min: 0.1, max: 100 }),
    numberField('grid_size', '地形尺寸(m)', 50, { min: 1, max: 1000 }),
  ],
  generate_lake: [
    numberField('x', '中心 X', 0),
    numberField('y', '中心 Y', 0),
    numberField('block_size', '水域地块边长(m)', 30, { min: 1, max: 500 }),
    numberField('lake_size', '湖面半径(m)', 10, { min: 1, max: 250 }),
    numberField('ripple_strength', '水波强度', 0.05, { min: 0, max: 5, step: 0.01 }),
  ],
  generate_river: [
    numberField('river_width', '河流宽度(m)', 5, { min: 1, max: 100 }),
    numberField('seed', '随机种子', 0, { type: 'integer', min: 0, step: 1 }),
  ],
  add_boat: [
    numberField('boat_scale', '船只缩放', 1, { min: 0.01, max: 20 }),
    numberField('flow_speed', '流速', 1, { min: 0, max: 20 }),
  ],
  start_simulation: [
    numberField('car_density', '车辆密度', 10, { min: 0, max: 200 }),
    numberField('pedestrian_density', '行人密度', 5, { min: 0, max: 200 }),
    numberField('car_speed_min', '最低车速', 2, { min: 0, max: 200 }),
    numberField('car_speed_max', '最高车速', 8, { min: 0, max: 200 }),
  ],
  stop_simulation: [],
  apply_layout: [
    { name: 'points', label: '坐标点集', type: 'textarea', required: true, defaultValue: '0,0;20,0;20,20;0,20', hint: '格式：x,y;x,y;...' },
    { name: 'connections', label: '边连接', type: 'textarea', placeholder: '0,1;1,2;2,3;3,0' },
    { name: 'faces', label: '面定义', type: 'textarea', placeholder: '0,1,2,3' },
  ],
  sketch_layout: [
    { name: 'image_path', label: '草图路径', type: 'text', required: true, placeholder: 'D:/path/to/sketch.png' },
    numberField('threshold', '识别阈值', 50, { type: 'integer', min: 0, max: 255, step: 1 }),
  ],
};

function buildInitialValues(fields: ParamField[]) {
  return fields.reduce<Record<string, string | boolean>>((acc, field) => {
    acc[field.name] = field.type === 'boolean'
      ? Boolean(field.defaultValue)
      : String(field.defaultValue ?? '');
    return acc;
  }, {});
}

function inferFieldFromName(name: string): ParamField {
  const normalized = name.trim();
  const integerNames = ['seed', 'count', 'amount', 'lanes', 'rows', 'columns', 'threshold', 'template_id'];
  const numberNames = ['width', 'height', 'depth', 'density', 'scale', 'spacing', 'speed', 'size', 'x', 'y'];
  const booleanNames = ['enable', 'enabled', 'randomize', 'clear_previous', 'dry_run'];
  const lower = normalized.toLowerCase();

  if (booleanNames.some((item) => lower.includes(item))) {
    return boolDefault(normalized, normalized, false);
  }
  if (integerNames.some((item) => lower.includes(item))) {
    return numberField(normalized, normalized, 0, { type: 'integer', step: 1 });
  }
  if (numberNames.some((item) => lower.includes(item))) {
    return numberField(normalized, normalized, 0);
  }
  return { name: normalized, label: normalized, type: 'text' };
}

function getParamFields(functionName: string, schemaSummary?: string) {
  if (PLUGIN_PARAM_SCHEMAS[functionName]) {
    return PLUGIN_PARAM_SCHEMAS[functionName];
  }
  if (!schemaSummary || schemaSummary.trim().toLowerCase() === 'none') {
    return [];
  }
  return schemaSummary.split(',').map((item) => inferFieldFromName(item));
}

function parseFieldValue(field: ParamField, value: string | boolean | undefined) {
  if (field.type === 'boolean') {
    return Boolean(value);
  }

  const rawValue = String(value ?? '').trim();
  if (!rawValue) {
    if (field.required) {
      throw new Error(`请填写「${field.label}」`);
    }
    return undefined;
  }

  const shouldParseNumber = field.type === 'number' || field.type === 'integer' || field.valueType === 'number' || field.valueType === 'integer';
  if (!shouldParseNumber) {
    return rawValue;
  }

  const parsed = Number(rawValue);
  if (!Number.isFinite(parsed)) {
    throw new Error(`「${field.label}」必须是合法数字`);
  }
  if ((field.type === 'integer' || field.valueType === 'integer') && !Number.isInteger(parsed)) {
    throw new Error(`「${field.label}」必须是整数`);
  }
  if (field.min !== undefined && parsed < field.min) {
    throw new Error(`「${field.label}」不能小于 ${field.min}`);
  }
  if (field.max !== undefined && parsed > field.max) {
    throw new Error(`「${field.label}」不能大于 ${field.max}`);
  }
  return field.type === 'integer' || field.valueType === 'integer' ? Math.trunc(parsed) : parsed;
}

function buildTaskParams(fields: ParamField[], values: Record<string, string | boolean>) {
  return fields.reduce<Record<string, unknown>>((acc, field) => {
    const parsed = parseFieldValue(field, values[field.name]);
    if (parsed !== undefined) {
      acc[field.name] = parsed;
    }
    return acc;
  }, {});
}

export function TasksPage() {
  const { hasPermission } = useSession();
  const {
    selectedProjectId,
    selectedSceneId,
    functions,
    tasks,
    dispatchTask,
    retryTask,
  } = useWorkspace();
  const [functionName, setFunctionName] = useState(functions[0]?.name ?? 'replace_asset_batch');
  const [title, setTitle] = useState('手动下发插件任务');
  const [priority, setPriority] = useState(3);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const functionItem = functions.find((item) => item.name === functionName);
  const parameterFields = useMemo(
    () => getParamFields(functionName, functionItem?.schemaSummary),
    [functionName, functionItem?.schemaSummary],
  );
  const [paramValues, setParamValues] = useState<Record<string, string | boolean>>(() => buildInitialValues(parameterFields));

  useEffect(() => {
    if (functions.length && !functions.some((item) => item.name === functionName)) {
      setFunctionName(functions[0].name);
    }
  }, [functionName, functions]);

  useEffect(() => {
    setParamValues(buildInitialValues(parameterFields));
    setLocalError(null);
  }, [parameterFields]);

  const generatedParamsPreview = useMemo(() => {
    try {
      return JSON.stringify(buildTaskParams(parameterFields, paramValues), null, 2);
    } catch {
      return '请补全合法参数后生成预览';
    }
  }, [parameterFields, paramValues]);

  const taskStats = useMemo(
    () => ({
      running: tasks.filter((task) => task.status === 'running').length,
      queued: tasks.filter((task) => task.status === 'queued').length,
      failed: tasks.filter((task) => task.status === 'failed').length,
      success: tasks.filter((task) => task.status === 'success').length,
    }),
    [tasks],
  );

  const handleFunctionChange = (nextName: string) => {
    setFunctionName(nextName);
    const nextFunction = functions.find((item) => item.name === nextName);
    if (nextFunction?.title) {
      setTitle(nextFunction.title);
    }
  };

  const updateParamValue = (fieldName: string, value: string | boolean) => {
    setParamValues((current) => ({ ...current, [fieldName]: value }));
  };

  const handleDispatch = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedProjectId || !selectedSceneId) return;
    setIsSubmitting(true);
    setLocalError(null);
    try {
      const parsedParams = buildTaskParams(parameterFields, paramValues);
      await dispatchTask({
        projectId: selectedProjectId,
        sceneId: selectedSceneId,
        functionName,
        title,
        priority,
        params: parsedParams,
        dependsOn: [],
      });
    } catch (caught) {
      setLocalError(caught instanceof Error ? caught.message : '任务下发失败。');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page-stack">
      <SectionHeader title="任务编排与插件调度" description="白名单函数、DAG 依赖、Blender 插件任务下发与回执状态机。" />

      <div className="metrics-grid">
        <MetricInline label="排队" value={taskStats.queued} />
        <MetricInline label="运行" value={taskStats.running} />
        <MetricInline label="成功" value={taskStats.success} />
        <MetricInline label="失败" value={taskStats.failed} />
      </div>

      <div className="two-column uneven">
        <Panel>
          <SectionHeader title="函数注册表" />
          <div className="function-list">
            {functions.map((item) => (
              <button key={item.name} className={`function-item ${item.name === functionName ? 'active' : ''}`} type="button" onClick={() => handleFunctionChange(item.name)}>
                <div>
                  <strong>{item.title}</strong>
                  <span>{item.name}</span>
                </div>
                <StatusBadge status={item.enabled ? 'healthy' : 'offline'} />
                <small>
                  {item.risk} / {item.averageMs}ms
                </small>
              </button>
            ))}
          </div>
        </Panel>

        <Panel>
          <SectionHeader title="任务下发" action={functionItem ? <StatusBadge status={functionItem.risk === 'high' ? 'critical' : 'info'} /> : null} />
          <form className="dispatch-form" onSubmit={(event) => void handleDispatch(event)}>
            {localError ? <div className="form-error">{localError}</div> : null}
            <Field label="任务标题">
              <input value={title} onChange={(event) => setTitle(event.target.value)} />
            </Field>
            <div className="form-grid">
              <Field label="函数">
                <select value={functionName} onChange={(event) => handleFunctionChange(event.target.value)}>
                  {functions.map((item) => (
                    <option key={item.name} value={item.name}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="优先级">
                <input type="number" min={1} max={5} value={priority} onChange={(event) => setPriority(Number(event.target.value))} />
              </Field>
            </div>

            <div className="parameter-form">
              <div className="parameter-form-head">
                <strong>函数参数</strong>
                <span>{functionItem?.schemaSummary ?? 'none'}</span>
              </div>
              {parameterFields.length ? (
                <div className="form-grid">
                  {parameterFields.map((field) => (
                    <ParameterInput key={field.name} field={field} value={paramValues[field.name]} onChange={(value) => updateParamValue(field.name, value)} />
                  ))}
                </div>
              ) : (
                <EmptyState title="该函数无需参数" description="系统会自动构造空参数对象并提交给后端。" />
              )}
            </div>

            <div className="function-schema">
              <ShieldAlert size={16} />
              <span>{functionItem?.description ?? '请选择要下发的插件函数。'}</span>
            </div>

            <div className="generated-params-preview">
              <span>自动生成的 params</span>
              <pre>{generatedParamsPreview}</pre>
            </div>

            <div className="form-actions">
              <Button type="submit" isLoading={isSubmitting} disabled={!hasPermission('task:dispatch') || !selectedProjectId || !selectedSceneId}>
                <Play size={16} />
                生成任务
              </Button>
            </div>
          </form>
        </Panel>
      </div>

      <Panel>
        <SectionHeader title="DAG 调度视图" />
        <div className="dag-view">
          <DagNode title="参数校验" status="success" />
          <DagEdge />
          <DagNode title="函数白名单" status="success" />
          <DagEdge />
          <DagNode title="队列调度" status={taskStats.queued > 0 ? 'queued' : 'success'} />
          <DagEdge />
          <DagNode title="Blender 执行" status={taskStats.running > 0 ? 'running' : 'queued'} />
          <DagEdge />
          <DagNode title="回执归档" status={taskStats.failed > 0 ? 'failed' : 'success'} />
        </div>
      </Panel>

      <Panel>
        <SectionHeader title="任务状态机" />
        {tasks.length ? (
          <div className="task-table">
            {tasks.map((task) => (
              <div key={task.id} className="task-card-row">
                <div>
                  <strong>{task.title}</strong>
                  <span>
                    {task.functionName} / {task.traceId}
                  </span>
                </div>
                <StatusBadge status={task.status} />
                <div className="progress-cell">
                  <ProgressBar value={task.progress} />
                  <small>{task.progress}%</small>
                </div>
                <div className="task-log">
                  {task.logs.slice(-2).map((log) => (
                    <span key={log}>{log}</span>
                  ))}
                </div>
                <Button variant="secondary" size="sm" disabled={!task.retryable} onClick={() => void retryTask(task.id)}>
                  <RefreshCw size={14} />
                  重试
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="暂无任务" description="函数计划和手动调度会进入任务状态机。" />
        )}
      </Panel>
    </div>
  );
}

function ParameterInput({
  field,
  value,
  onChange,
}: {
  field: ParamField;
  value: string | boolean | undefined;
  onChange: (value: string | boolean) => void;
}) {
  if (field.type === 'boolean') {
    return (
      <Field label={field.label} hint={field.hint}>
        <label className="param-toggle">
          <input type="checkbox" checked={Boolean(value)} onChange={(event) => onChange(event.target.checked)} />
          <span>{Boolean(value) ? '开启' : '关闭'}</span>
        </label>
      </Field>
    );
  }

  if (field.type === 'select') {
    return (
      <Field label={`${field.label}${field.required ? ' *' : ''}`} hint={field.hint}>
        <select value={String(value ?? '')} onChange={(event) => onChange(event.target.value)}>
          {(field.options ?? []).map((option) => (
            <option key={String(option.value)} value={String(option.value)}>
              {option.label}
            </option>
          ))}
        </select>
      </Field>
    );
  }

  if (field.type === 'textarea') {
    return (
      <Field label={`${field.label}${field.required ? ' *' : ''}`} hint={field.hint}>
        <textarea rows={3} value={String(value ?? '')} placeholder={field.placeholder} onChange={(event) => onChange(event.target.value)} />
      </Field>
    );
  }

  return (
    <Field label={`${field.label}${field.required ? ' *' : ''}`} hint={field.hint}>
      <input
        type={field.type === 'text' ? 'text' : 'number'}
        min={field.min}
        max={field.max}
        step={field.step}
        value={String(value ?? '')}
        placeholder={field.placeholder}
        onChange={(event) => onChange(event.target.value)}
      />
    </Field>
  );
}

function MetricInline({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric metric-default">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>任务</small>
    </div>
  );
}

function DagNode({ title, status }: { title: string; status: string }) {
  return (
    <div className={`dag-node dag-${status}`}>
      <Workflow size={18} />
      <strong>{title}</strong>
      <StatusBadge status={status} />
    </div>
  );
}

function DagEdge() {
  return (
    <div className="dag-edge">
      <GitBranch size={18} />
    </div>
  );
}
