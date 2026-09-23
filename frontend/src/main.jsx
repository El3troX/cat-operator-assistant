import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router/dom';
import { Toaster } from 'sonner';
import SessionProvider from './app/SessionProvider';
import { router } from './app/router';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 10_000, retry: 1 },
  },
});

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <SessionProvider>
        <RouterProvider router={router} />
        <Toaster theme="dark" richColors position="top-right" closeButton />
      </SessionProvider>
    </QueryClientProvider>
  </StrictMode>,
);
