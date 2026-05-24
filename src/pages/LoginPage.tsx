import { FormEvent, useMemo, useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { ArrowRight, Building2, Eye, EyeOff, ShieldCheck, UsersRound, WandSparkles } from 'lucide-react';
import { useSession } from '../context/SessionContext';
import { roleDescriptions, roleLabels, type RoleCode } from '../types/domain';
import { Button, Field, InlineError, StatusBadge } from '../components/ui';

const demoAccounts: Array<{ role: RoleCode; email: string; icon: React.ElementType }> = [
  { role: 'modeler', email: 'modeler@nku.city', icon: Building2 },
  { role: 'analyst', email: 'analyst@nku.city', icon: WandSparkles },
  { role: 'admin', email: 'admin@nku.city', icon: ShieldCheck },
];

export function LoginPage() {
  const { isAuthenticated, login } = useSession();
  const navigate = useNavigate();
  const [email, setEmail] = useState('modeler@nku.city');
  const [password, setPassword] = useState('demo1234');
  const [selectedRole, setSelectedRole] = useState<RoleCode>('modeler');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentAccount = useMemo(
    () => demoAccounts.find((account) => account.role === selectedRole) ?? demoAccounts[0],
    [selectedRole],
  );

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      await login({ email, password, role: selectedRole });
      navigate('/', { replace: true });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '登录失败。');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="login-page">
      <section className="login-visual" aria-label="系统状态概览">
        <div className="login-brand">
          <div className="brand-mark">SC</div>
          <div>
            <strong>智能城市生成系统</strong>
            <span>主系统控制平面</span>
          </div>
        </div>
        <div className="city-board">
          <div className="city-grid">
            {Array.from({ length: 36 }, (_, index) => (
              <span key={index} className={index % 5 === 0 ? 'grid-node hot' : index % 7 === 0 ? 'grid-node active' : 'grid-node'} />
            ))}
          </div>
          <div className="city-road road-a" />
          <div className="city-road road-b" />
          <div className="city-water" />
          <div className="city-building b1" />
          <div className="city-building b2" />
          <div className="city-building b3" />
          <div className="city-agent a1" />
          <div className="city-agent a2" />
          <div className="city-agent a3" />
        </div>
        <div className="login-status-grid">
          <div>
            <span>插件回执</span>
            <strong>97.6%</strong>
          </div>
          <div>
            <span>函数白名单</span>
            <strong>9</strong>
          </div>
          <div>
            <span>仿真刷新</span>
            <strong>10Hz</strong>
          </div>
        </div>
      </section>

      <section className="login-panel">
        <div className="login-heading">
          <StatusBadge status="healthy" />
          <h1>登录工作台</h1>
          <p>选择角色后进入对应的项目、编排、仿真或治理工作流。</p>
        </div>

        <div className="role-switcher">
          {demoAccounts.map((account) => {
            const Icon = account.icon;
            const isSelected = selectedRole === account.role;
            return (
              <button
                key={account.role}
                className={`role-card ${isSelected ? 'active' : ''}`}
                type="button"
                onClick={() => {
                  setSelectedRole(account.role);
                  setEmail(account.email);
                }}
              >
                <Icon size={20} />
                <strong>{roleLabels[account.role]}</strong>
                <span>{account.email}</span>
              </button>
            );
          })}
        </div>

        <form className="login-form" onSubmit={(event) => void handleSubmit(event)}>
          {error ? <InlineError message={error} onDismiss={() => setError(null)} /> : null}
          <Field label="账号">
            <input value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="username" />
          </Field>
          <Field label="密码">
            <div className="password-field">
              <input
                value={password}
                type={showPassword ? 'text' : 'password'}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
              />
              <button type="button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? '隐藏密码' : '显示密码'}>
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </Field>
          <div className="selected-role-summary">
            <UsersRound size={18} />
            <span>{roleDescriptions[currentAccount.role]}</span>
          </div>
          <Button type="submit" isLoading={isSubmitting}>
            进入系统
            <ArrowRight size={16} />
          </Button>
        </form>
      </section>
    </main>
  );
}
