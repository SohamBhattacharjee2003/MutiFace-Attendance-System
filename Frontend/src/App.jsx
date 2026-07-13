import { BrowserRouter, Routes, Route } from "react-router-dom";

// Pages
import Home from "./pages/Home";
import Login from "./pages/Login";
import Research from "./pages/Research";
import Enroll from "./pages/Enroll";
import Classes from "./pages/Classes";
import ClassDetail from "./pages/ClassDetail";
import Dashboard from "./pages/Dashboard";
import LiveAttendance from "./pages/LiveAttendance";
import Capture from "./pages/Capture";

// Navbar
import Navbar from "./components/Navbar";

export default function App() {
  return (
    <BrowserRouter basename="/">
      <Routes>
        {/* ---- PUBLIC PAGES (NO NAVBAR) ---- */}
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/research" element={<Research />} />
        {/* the link a teacher shares — public on purpose, but gated by the roster */}
        <Route path="/enroll/:code" element={<Enroll />} />

        {/* ---- PAGES WITH NAVBAR ---- */}
        <Route
          path="/classes"
          element={
            <>
              <Navbar />
              <Classes />
            </>
          }
        />

        <Route
          path="/classes/:id"
          element={
            <>
              <Navbar />
              <ClassDetail />
            </>
          }
        />

        <Route
          path="/dashboard"
          element={
            <>
              <Navbar />
              <Dashboard />
            </>
          }
        />

        <Route
          path="/capture"
          element={
            <>
              <Navbar />
              <Capture />
            </>
          }
        />

        <Route
          path="/live"
          element={
            <>
              <Navbar />
              <LiveAttendance />
            </>
          }
        />

      </Routes>
    </BrowserRouter>
  );
}
