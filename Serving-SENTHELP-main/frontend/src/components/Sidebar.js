// Sidebar.js
import React from "react";
import "../App.css";

const Sidebar = ({ selectedView, onViewChange }) => {
  return (
    <div className="sidebar h-screen w-64 bg-gray-100 p-6 shadow-md">
      {/* Logo + Titre */}
      <div className="flex items-center mb-8">
        <img
          src="/logo.png" // <- à adapter selon ton chemin ou remplace par un autre logo
          alt="Logo"
          style = {{ width: "200px", height: "100px" }}
          className="w-10 h-10 mr-3 rounded-full"
        />
        <h2 className="text-2xl font-bold text-gray-800">Dashboard</h2>
      </div>

      {/* Boutons */}
      <button
        className={`w-full text-left px-4 py-3 mb-3 rounded-lg font-medium transition-all duration-300 
          ${
            selectedView === "stats"
              ? "bg-blue-600 text-white shadow-md"
              : "bg-white text-gray-700 hover:bg-blue-100"
          }`}
        onClick={() => onViewChange("stats")}
        style={{ height: "80px" }}
      >
        <p style={{ fontSize: `${15}px` }}> 📈 Statistique Générale </p>
      </button>

      <button
        className={`w-full text-left px-4 py-3 rounded-lg font-medium transition-all duration-300 
          ${
            selectedView === "sentiment"
              ? "bg-blue-600 text-white shadow-md"
              : "bg-white text-gray-700 hover:bg-blue-100"
          }`}
        onClick={() => onViewChange("sentiment")}
        style={{ height: "80px" }}
      >
        <p style={{ fontSize: `${15}px` }}>💬 Analyse de Sentiment</p>
      </button>
    </div>
  );
};

export default Sidebar;

