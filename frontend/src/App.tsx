import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Discovery from './pages/Discovery';
import Jobs from './pages/Jobs';
import Leads from './pages/Leads';
import LeadDetail from './pages/LeadDetail';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="discovery" element={<Discovery />} />
          <Route path="jobs" element={<Jobs />} />
          <Route path="leads" element={<Leads />} />
          <Route path="leads/:id" element={<LeadDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
