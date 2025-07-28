import React from "react";
import { FaChevronDown } from "react-icons/fa6";
import "../App.css";
const Navbar = () => (
  <div className="navbar" >
    <div className="nav-logo">
      <img
        src="/logo.png"
        alt="Logo"
        style={{
          width: "200px",
          marginLeft: "-10%",
        }}
      />
    </div>
    <h2>Sentiment Analysis</h2>
    <div className="user-profile">
      <img src="/profileImage.png" alt="User" className="profile-img" />
      <span>User</span>
      <FaChevronDown />
    </div>
  </div>
);
export default Navbar;
