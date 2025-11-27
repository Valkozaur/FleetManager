import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { OrdersPage } from './pages/OrdersPage';
import { OrderDetailsPage } from './pages/OrderDetailsPage';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import FleetPage from "./pages/FleetPage"; // Added import for FleetPage
import { Layout } from './components/Layout'; // Added import for Layout

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/" element={<Layout />}> {/* Changed root route to use Layout */}
            <Route index element={<Navigate to="/orders" replace />} /> {/* Changed path to index */}
            <Route path="orders" element={<OrdersPage />} /> {/* Changed path to relative "orders" */}
            <Route path="orders/:id" element={<OrderDetailsPage />} /> {/* Changed path to relative "orders/:id" */}
            <Route path="fleet" element={<FleetPage />} /> {/* Added FleetPage route */}
          </Route>
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
