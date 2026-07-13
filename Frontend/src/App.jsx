import { BrowserRouter, Routes, Route } from "react-router-dom";

// Pages
import Home from "./pages/Home";
import Login from "./pages/Login";
import Research from "./pages/Research";
import Enroll from "./pages/Enroll";
import Classes from "./pages/Classes";
import ClassDetail from "./pages/ClassDetail";
import Dashboard from "./pages/Dashboard";
import RegisterStudent from "./pages/RegisterStudent";
import LiveAttendance from "./pages/LiveAttendance";
import Attendance from "./pages/Attendance";
import StudentList from "./pages/StudentList";
import AttendanceRecords from "./pages/Attendance_Records";

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
          path="/attendance-records"
          element={
            <>
              <Navbar />
              <AttendanceRecords />
            </>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
