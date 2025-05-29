import Link from "next/link"

export default function Footer() {
  return (
    <footer className="bg-secondary text-white py-5 mt-5">
      <div className="container">
        <div className="row">
          <div className="col-lg-4 col-md-6 mb-4">
            <div className="d-flex align-items-center mb-3">
              <img
                src="https://res.cloudinary.com/digitaliquids-cloud-technologies/image/upload/sasabot-logo_dnd7wx.jpg"
                alt="SasaBot Technologies Logo"
                className="me-2"
                width="40"
                height="40"
              />
              
            </div>
            <p className="text-muted">
              Empowering businesses with AI-powered automation solutions. Smarter business starts here.
            </p>
          </div>

          <div className="col-lg-2 col-md-6 mb-4">
            <h6 className="text-primary mb-3">Quick Links</h6>
            <ul className="list-unstyled">
              <li>
                <Link href="/" className="text-muted text-decoration-none">
                  Home
                </Link>
              </li>
              <li>
                <Link href="/about" className="text-muted text-decoration-none">
                  About
                </Link>
              </li>
              <li>
                <Link href="/services" className="text-muted text-decoration-none">
                  Services
                </Link>
              </li>
              <li>
                <Link href="/industries" className="text-muted text-decoration-none">
                  Industries
                </Link>
              </li>
            </ul>
          </div>

          <div className="col-lg-3 col-md-6 mb-4">
            <h6 className="text-primary mb-3">Services</h6>
            <ul className="list-unstyled">
              <li>
                <span className="text-muted">Business Intelligence</span>
              </li>
              <li>
                <span className="text-muted">HR Automation</span>
              </li>
              <li>
                <span className="text-muted">Payroll Processing</span>
              </li>
              <li>
                <span className="text-muted">Process Automation</span>
              </li>
            </ul>
          </div>

          <div className="col-lg-3 col-md-6 mb-4">
            <h6 className="text-primary mb-3">Contact Info</h6>
            <ul className="list-unstyled">
              <li className="text-muted mb-2">📍 Nairobi, Kenya</li>
              <li className="text-muted mb-2">📞 +254 762222000</li>
              <li className="text-muted mb-2">📧 info@sasabot.tech</li>
              <li className="text-muted">🌐 https://sasabot.tech</li>
            </ul>
          </div>
        </div>

        <hr className="my-4" />

        <div className="row align-items-center">
          <div className="col-md-6">
            <p className="text-muted mb-0">
              © 2025 SasaBot Technologies. All rights reserved. by Digitaliquids Cloud Technologies
            </p>
            <div className="mt-2">
              <Link href="/terms" className="text-muted text-decoration-none me-3">
                Terms of Service
              </Link>
              <Link href="/privacy" className="text-muted text-decoration-none">
                Privacy Policy
              </Link>
            </div>
          </div>
          <div className="col-md-6 text-md-end">
            <Link href="/contact" className="btn btn-primary btn-sm">
              Book a Demo
            </Link>
          </div>
        </div>
      </div>
    </footer>
  )
}
