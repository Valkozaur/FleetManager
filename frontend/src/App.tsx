import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { OrdersPage } from './pages/OrdersPage';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/" element={<Navigate to="/orders" replace />} />
          <Route path="/orders" element={<OrdersPage />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
