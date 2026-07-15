import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Heatmap from './pages/Heatmap';
import Incidents from './pages/Incidents';
import Permits from './pages/Permits';
import Emergency from './pages/Emergency';
import Audit from './pages/Audit';
import CCTV from './pages/CCTV';
import IoT from './pages/IoT';
import KnowledgeGraph from './pages/KnowledgeGraph';
import Orchestrator from './pages/Orchestrator';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/heatmap" element={<Heatmap />} />
          <Route path="/incidents" element={<Incidents />} />
          <Route path="/permits" element={<Permits />} />
          <Route path="/emergency" element={<Emergency />} />
          <Route path="/audit" element={<Audit />} />
          <Route path="/cctv" element={<CCTV />} />
          <Route path="/iot" element={<IoT />} />
          <Route path="/knowledge-graph" element={<KnowledgeGraph />} />
          <Route path="/orchestrator" element={<Orchestrator />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
