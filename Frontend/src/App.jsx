import { BrowserRouter, Routes, Route } from "react-router-dom";

// Pages
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import RegisterStudent from "./pages/RegisterStudent";
import LiveAttendance from "./pages/LiveAttendance";
import Attendance from "./pages/Attendance";
import StudentList from "./pages/StudentList";
import Settings from "./pages/Settings";

// Navbar
import Navbar from "./components/Navbar";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* ---- LOGIN PAGE (NO NAVBAR) ---- */}
        <Route path="/" element={<Login />} />

        {/* ---- PAGES WITH NAVBAR ---- */}
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
          path="/register"
          element={
            <>
              <Navbar />
              <RegisterStudent />
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

        <Route
          path="/attendance"
          element={
            <>
              <Navbar />
              <Attendance />
            </>
          }
        />

        <Route
          path="/students"
          element={
            <>
              <Navbar />
              <StudentList />
            </>
          }
        />

        <Route
          path="/settings"
          element={
            <>
              <Navbar />
              <Settings />
            </>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
