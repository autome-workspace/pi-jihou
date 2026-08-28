import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Overview from "./pages/Overview";
import Schedules from "./pages/Schedules";
import Audio from "./pages/Audio";
import Voicevox from "./pages/Voicevox";
import Variables from "./pages/Variables";
import Devices from "./pages/Devices";
import Time from "./pages/Time";
import Logs from "./pages/Logs";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/overview" replace />} />
        <Route path="/overview" element={<Overview />} />
        <Route path="/schedules" element={<Schedules />} />
        <Route path="/audio" element={<Audio />} />
        <Route path="/voicevox" element={<Voicevox />} />
        <Route path="/variables" element={<Variables />} />
        <Route path="/devices" element={<Devices />} />
        <Route path="/time" element={<Time />} />
        <Route path="/logs" element={<Logs />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  );
}
