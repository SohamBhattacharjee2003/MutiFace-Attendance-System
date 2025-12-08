import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="bg-blue-600 text-white py-4 shadow-md">
      <div className="container mx-auto flex space-x-6 text-lg font-semibold">
        <Link to="/" className="hover:text-yellow-300">Attendance</Link>
        <Link to="/register" className="hover:text-yellow-300">Register Student</Link>
        <Link to="/records" className="hover:text-yellow-300">Records</Link>
      </div>
    </nav>
  );
}
