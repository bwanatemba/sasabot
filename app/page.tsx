import Link from "next/link"

export default function HomePage() {
  return (
    <>
      {/* Hero Section */}
      <section className="bg-primary text-white py-5">
        <div className="container">
          <div className="row align-items-center min-vh-75">
            <div className="col-lg-6">
              <h1 className="display-4 fw-bold mb-4">Smarter Business Starts Here</h1>
              <p className="lead mb-4">
                At SasaBot Technologies, we help companies unlock their full potential by automating business processes
                with cutting-edge AI. From business intelligence to HR, payroll, and beyond — we streamline your
                operations so you can focus on what matters most: growth.
              </p>
              <div className="d-flex flex-wrap gap-3">
                <Link href="/contact" className="btn btn-secondary btn-lg">
                  Book a Demo
                </Link>
                <Link href="/services" className="btn btn-outline-light btn-lg">
                  Our Services
                </Link>
              </div>
            </div>
            <div className="col-lg-6 text-center">
              <img
                src="https://res.cloudinary.com/digitaliquids-cloud-technologies/image/upload/sasabot-logo_dnd7wx.jpg"
                alt="AI Automation Illustration"
                className="img-fluid rounded"
              />
            </div>
          </div>
        </div>
      </section>

      {/* What We Do Section */}
      <section className="py-5">
        <div className="container">
          <div className="row">
            <div className="col-lg-8 mx-auto text-center mb-5">
              <h2 className="display-5 fw-bold text-primary mb-4">What We Do</h2>
              <p className="lead text-muted">AI-Powered Automation for the Modern Enterprise</p>
              <p>
                We design and deploy intelligent automation systems that reduce manual work, eliminate errors, and
                improve decision-making. Whether you're a startup or a large enterprise, SasaBot empowers your teams
                with solutions that are fast, scalable, and efficient.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Services Preview */}
      <section className="py-5 bg-light">
        <div className="container">
          <h2 className="text-center text-primary mb-5">Our Solutions</h2>
          <div className="row g-4">
            <div className="col-lg-3 col-md-6">
              <div className="card h-100 border-0 shadow-sm">
                <div className="card-body text-center">
                  <div className="text-primary mb-3" style={{ fontSize: "3rem" }}>
                    🔍
                  </div>
                  <h5 className="card-title text-primary">Business Intelligence</h5>
                  <p className="card-text">
                    Turn data into actionable insights with real-time analysis and forecasting.
                  </p>
                </div>
              </div>
            </div>

            <div className="col-lg-3 col-md-6">
              <div className="card h-100 border-0 shadow-sm">
                <div className="card-body text-center">
                  <div className="text-primary mb-3" style={{ fontSize: "3rem" }}>
                    👥
                  </div>
                  <h5 className="card-title text-primary">HR Automation</h5>
                  <p className="card-text">Streamline recruitment, onboarding, and employee management processes.</p>
                </div>
              </div>
            </div>

            <div className="col-lg-3 col-md-6">
              <div className="card h-100 border-0 shadow-sm">
                <div className="card-body text-center">
                  <div className="text-primary mb-3" style={{ fontSize: "3rem" }}>
                    💰
                  </div>
                  <h5 className="card-title text-primary">Payroll Processing</h5>
                  <p className="card-text">Accurate, timely, and compliant payroll solutions powered by automation.</p>
                </div>
              </div>
            </div>

            <div className="col-lg-3 col-md-6">
              <div className="card h-100 border-0 shadow-sm">
                <div className="card-body text-center">
                  <div className="text-primary mb-3" style={{ fontSize: "3rem" }}>
                    🔄
                  </div>
                  <h5 className="card-title text-primary">Process Automation</h5>
                  <p className="card-text">Identify bottlenecks and automate repetitive tasks across departments.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="text-center mt-5">
            <Link href="/services" className="btn btn-primary btn-lg">
              View All Services
            </Link>
          </div>
        </div>
      </section>

      {/* Why Choose Us */}
      <section className="py-5">
        <div className="container">
          <div className="row">
            <div className="col-lg-6">
              <h2 className="text-primary mb-4">Why Choose SasaBot?</h2>
              <div className="row g-4">
                <div className="col-12">
                  <div className="d-flex">
                    <div className="text-secondary me-3">✅</div>
                    <div>
                      <h6>Tailored Solutions</h6>
                      <p className="text-muted">
                        We don't do one-size-fits-all. Every tool we build is customized to your business needs.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="col-12">
                  <div className="d-flex">
                    <div className="text-secondary me-3">✅</div>
                    <div>
                      <h6>AI Expertise</h6>
                      <p className="text-muted">
                        Our team blends deep tech knowledge with real-world business experience.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="col-12">
                  <div className="d-flex">
                    <div className="text-secondary me-3">✅</div>
                    <div>
                      <h6>Seamless Integration</h6>
                      <p className="text-muted">
                        We integrate with your existing tools and platforms, making transition smooth.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="col-12">
                  <div className="d-flex">
                    <div className="text-secondary me-3">✅</div>
                    <div>
                      <h6>Scalable & Secure</h6>
                      <p className="text-muted">Built to grow with you, with security and compliance baked in.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="col-lg-6">
              <img src="https://res.cloudinary.com/digitaliquids-cloud-technologies/image/upload/sasabot-logo_dnd7wx.jpg" alt="Why Choose SasaBot" className="img-fluid rounded" />
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-5 bg-secondary text-white">
        <div className="container text-center">
          <h2 className="mb-4">Ready to Automate?</h2>
          <p className="lead mb-4">
            Let's transform your business together. Schedule a free consultation and discover how SasaBot can automate
            your workflows, boost efficiency, and drive real ROI.
          </p>
          <Link href="/contact" className="btn btn-light btn-lg">
            Book a Demo
          </Link>
        </div>
      </section>
    </>
  )
}
