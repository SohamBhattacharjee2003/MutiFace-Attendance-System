export default function MainLayout({ children }) {
  return (
    <div className="min-h-screen bg-[#070c24] text-white relative overflow-hidden">

      {/* SAME GLOW EFFECT AS DASHBOARD */}
      <div className="absolute w-[700px] h-[700px] bg-blue-900/30 blur-[200px] -top-10 left-10 rounded-full"></div>
      <div className="absolute w-[500px] h-[500px] bg-purple-700/20 blur-[200px] bottom-0 right-10 rounded-full"></div>

      <Navbar />

      <div className="pt-24 px-8 relative z-10">
        {children}
      </div>
    </div>
  );
}
