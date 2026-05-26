import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import App from '../../src/App';
import { SessionProvider } from '../../src/context/SessionContext';
import { WorkspaceProvider } from '../../src/context/WorkspaceContext';

function renderApp(initialPath = '/login') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <SessionProvider>
        <WorkspaceProvider>
          <App />
        </WorkspaceProvider>
      </SessionProvider>
    </MemoryRouter>,
  );
}

describe('App', () => {
  it('renders the login page for unauthenticated users', async () => {
    renderApp('/login');

    expect(await screen.findByRole('heading', { name: '登录工作台' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /进入系统/ })).toBeInTheDocument();
  });
});
