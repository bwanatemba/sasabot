"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

export default function Navigation() {
  const pathname = usePathname()

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-primary sticky-top">
      <div className="container">
        <Link className="navbar-brand d-flex align-items-center" href="/">
          <img
            src="https://res.cloudinary.com/digitaliquids-cloud-technologies/image/upload/sasabot-logo_dnd7wx.jpg"
            alt="SasaBot Technologies Logo"
            className="me-2"
            width="40"
            height="40"
          />
          
        </Link>

        <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span className="navbar-toggler-icon"></span>
        </button>

        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav ms-auto">
            <li className="nav-item">
              <Link className={`nav-link ${pathname === "/" ? "active" : ""}`} href="/">
                Home
              </Link>
            </li>
            <li className="nav-item">
              <Link className={`nav-link ${pathname === "/about" ? "active" : ""}`} href="/about">
                About
              </Link>
            </li>
            <li className="nav-item">
              <Link className={`nav-link ${pathname === "/services" ? "active" : ""}`} href="/services">
                Services
              </Link>
            </li>
            <li className="nav-item">
              <Link className={`nav-link ${pathname === "/industries" ? "active" : ""}`} href="/industries">
                Industries
              </Link>
            </li>
            <li className="nav-item">
              <Link className={`nav-link ${pathname === "/contact" ? "active" : ""}`} href="/contact">
                Contact
              </Link>
            </li>
            <li className="nav-item">
              <Link className={`nav-link ${pathname === "/solutions" ? "active" : ""}`} href="/solutions">
                Solutions
              </Link>
            </li>
            <li className="nav-item">
              <Link className={`nav-link ${pathname === "/case-studies" ? "active" : ""}`} href="/case-studies">
                Case Studies
              </Link>
            </li>
            <li className="nav-item">
              <Link className={`nav-link ${pathname === "/resources" ? "active" : ""}`} href="/resources">
                Resources
              </Link>
            </li>
            <li className="nav-item">
              <Link className={`nav-link ${pathname === "/pricing" ? "active" : ""}`} href="/pricing">
                Pricing
              </Link>
            </li>
            <li className="nav-item ms-2">
              <Link className="btn btn-secondary btn-sm" href="/contact">
                Get Started
              </Link>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  )
}
