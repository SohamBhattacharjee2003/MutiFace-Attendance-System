import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Register from "./pages/Register";
import Attendance from "./pages/Attendance";
import Records from "./pages/Records";

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <div className="container mx-auto mt-6 px-4">
        <Routes>
          <Route path="/" element={<Attendance />} />
          <Route path="/register" element={<Register />} />
          <Route path="/records" element={<Records />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
