/* eslint-disable jsx-a11y/anchor-is-valid */
import React from 'react';
// import { Link } from 'react-router-dom';
import './Footer.css';

function Footer() {
  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-left">
          <p>
            SkinNet Analyzer is not intended to perform diagnosis, but rather to provide users the ability to image, track, and better understand their skin conditions.
          </p>
          <p>SkinNet Analyzer | All Rights Reserved.</p>
          <p>Copyright © 2025</p>
        </div>

        <div className="footer-links">
          <div className="footer-column">
            <a href="#">Main</a>
            <a href="#">Early Detection</a>
            <a href="#">How it works</a>
            {/* <a href="#">Artificial Intelligence</a> */}
          </div>
          <div className="footer-column">
            <a href="#">Features</a>
            <a href="#">FAQ</a>
            <a href="#">Privacy Policy</a>
            <a href="#">Terms of Use</a>
          </div>
        </div>
        <div className="footer-right">
          <p>If you have any questions about our website - contact us through email:</p>
          <p className="email">support@net.com</p>
          <div className="social-icons">
            <a href="#"><i className="fab fa-facebook"></i></a>
            <a href="#"><i className="fab fa-linkedin"></i></a>
            <a href="#"><i className="fab fa-twitter"></i></a>
            <a href="#"><i className="fab fa-instagram"></i></a>
            <a href="#"><i className="fab fa-telegram"></i></a>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
