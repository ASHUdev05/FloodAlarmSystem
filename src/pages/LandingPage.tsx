import Footer from "../components/Footer";
import { Link } from "react-router-dom";

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">      <main
        className="flex-grow bg-cover bg-center text-white flex flex-col items-center justify-center"
        style={{
          backgroundImage:
            "url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1470&q=80')",
        }}
      >
        <div className="bg-black bg-opacity-50 p-8 rounded-2xl text-center max-w-2xl">
          <h2 className="text-4xl font-bold mb-4">Real-Time Flood Alert System</h2>
          <p className="text-lg mb-6">
            Our flood alarm system uses IoT sensors and data analysis to warn residents
            about potential flooding in their area. Stay safe and informed with
            real-time alerts.
          </p>
          <div className="space-x-4">
            <Link
              to="/login"
              className="bg-blue-500 px-6 py-2 rounded-xl hover:bg-blue-600"
            >
              Login
            </Link>
            <Link
              to="/signup"
              className="bg-green-500 px-6 py-2 rounded-xl hover:bg-green-600"
            >
              Sign Up
            </Link>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
