export default function IndustriesPage() {
  return (
    <>
      {/* Hero Section */}
      <section className="bg-primary text-white py-5">
        <div className="container">
          <div className="row">
            <div className="col-lg-8 mx-auto text-center">
              <h1 className="display-4 fw-bold mb-4">Industries We Serve</h1>
              <p className="lead">Delivering specialized automation solutions across diverse sectors</p>
            </div>
          </div>
        </div>
      </section>

      {/* Industries Grid */}
      <section className="py-5">
        <div className="container">
          <div className="row g-4">
            {/* Finance & Accounting */}
            <div className="col-lg-4 col-md-6">
              <div className="card border-0 shadow-lg h-100">
                <div className="card-body p-4 text-center">
                  <div className="text-primary mb-4" style={{ fontSize: "3.5rem" }}>
                    🏦
                  </div>
                  <h4 className="text-primary mb-3">Finance & Accounting</h4>
                  <p className="mb-4">
                    Streamline financial processes, automate reporting, and ensure compliance with intelligent
                    automation solutions.
                  </p>
                  <ul className="list-unstyled text-start">
                    <li className="mb-2">• Automated invoice processing</li>
                    <li className="mb-2">• Financial reporting automation</li>
                    <li className="mb-2">• Compliance monitoring</li>
                    <li className="mb-2">• Risk assessment tools</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Healthcare */}
            <div className="col-lg-4 col-md-6">
              <div className="card border-0 shadow-lg h-100">
                <div className="card-body p-4 text-center">
                  <div className="text-primary mb-4" style={{ fontSize: "3.5rem" }}>
                    🏥
                  </div>
                  <h4 className="text-primary mb-3">Healthcare</h4>
                  <p className="mb-4">
                    Improve patient care and operational efficiency with AI-powered healthcare automation solutions.
                  </p>
                  <ul className="list-unstyled text-start">
                    <li className="mb-2">• Patient data management</li>
                    <li className="mb-2">• Appointment scheduling</li>
                    <li className="mb-2">• Medical billing automation</li>
                    <li className="mb-2">• Compliance tracking</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Manufacturing */}
            <div className="col-lg-4 col-md-6">
              <div className="card border-0 shadow-lg h-100">
                <div className="card-body p-4 text-center">
                  <div className="text-primary mb-4" style={{ fontSize: "3.5rem" }}>
                    🏭
                  </div>
                  <h4 className="text-primary mb-3">Manufacturing</h4>
                  <p className="mb-4">
                    Optimize production processes, quality control, and supply chain management with intelligent
                    automation.
                  </p>
                  <ul className="list-unstyled text-start">
                    <li className="mb-2">• Production planning automation</li>
                    <li className="mb-2">• Quality control systems</li>
                    <li className="mb-2">• Inventory management</li>
                    <li className="mb-2">• Predictive maintenance</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Retail & eCommerce */}
            <div className="col-lg-4 col-md-6">
              <div className="card border-0 shadow-lg h-100">
                <div className="card-body p-4 text-center">
                  <div className="text-primary mb-4" style={{ fontSize: "3.5rem" }}>
                    🛒
                  </div>
                  <h4 className="text-primary mb-3">Retail & eCommerce</h4>
                  <p className="mb-4">
                    Enhance customer experience and streamline operations with retail-focused automation solutions.
                  </p>
                  <ul className="list-unstyled text-start">
                    <li className="mb-2">• Customer service automation</li>
                    <li className="mb-2">• Inventory optimization</li>
                    <li className="mb-2">• Price management</li>
                    <li className="mb-2">• Order processing automation</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Education */}
            <div className="col-lg-4 col-md-6">
              <div className="card border-0 shadow-lg h-100">
                <div className="card-body p-4 text-center">
                  <div className="text-primary mb-4" style={{ fontSize: "3.5rem" }}>
                    🎓
                  </div>
                  <h4 className="text-primary mb-3">Education</h4>
                  <p className="mb-4">
                    Transform educational administration and enhance learning experiences with AI-powered solutions.
                  </p>
                  <ul className="list-unstyled text-start">
                    <li className="mb-2">• Student information systems</li>
                    <li className="mb-2">• Automated grading systems</li>
                    <li className="mb-2">• Enrollment management</li>
                    <li className="mb-2">• Learning analytics</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Logistics & Supply Chain */}
            <div className="col-lg-4 col-md-6">
              <div className="card border-0 shadow-lg h-100">
                <div className="card-body p-4 text-center">
                  <div className="text-primary mb-4" style={{ fontSize: "3.5rem" }}>
                    🚚
                  </div>
                  <h4 className="text-primary mb-3">Logistics & Supply Chain</h4>
                  <p className="mb-4">
                    Optimize logistics operations and supply chain management with intelligent automation and tracking
                    systems.
                  </p>
                  <ul className="list-unstyled text-start">
                    <li className="mb-2">• Route optimization</li>
                    <li className="mb-2">• Warehouse automation</li>
                    <li className="mb-2">• Shipment tracking</li>
                    <li className="mb-2">• Demand forecasting</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Industry Benefits */}
      <section className="py-5 bg-light">
        <div className="container">
          <div className="row">
            <div className="col-lg-8 mx-auto text-center mb-5">
              <h2 className="text-primary mb-4">Industry-Specific Benefits</h2>
              <p className="lead">
                Our solutions are tailored to address the unique challenges and opportunities in each industry
              </p>
            </div>
          </div>

          <div className="row g-4">
            <div className="col-md-3">
              <div className="text-center">
                <div className="text-secondary mb-3" style={{ fontSize: "2.5rem" }}>
                  ⚡
                </div>
                <h5>Increased Efficiency</h5>
                <p className="text-muted">Reduce manual work and accelerate processes across all departments.</p>
              </div>
            </div>

            <div className="col-md-3">
              <div className="text-center">
                <div className="text-secondary mb-3" style={{ fontSize: "2.5rem" }}>
                  💰
                </div>
                <h5>Cost Reduction</h5>
                <p className="text-muted">Lower operational costs through intelligent automation and optimization.</p>
              </div>
            </div>

            <div className="col-md-3">
              <div className="text-center">
                <div className="text-secondary mb-3" style={{ fontSize: "2.5rem" }}>
                  🎯
                </div>
                <h5>Improved Accuracy</h5>
                <p className="text-muted">Eliminate human errors and ensure consistent, reliable results.</p>
              </div>
            </div>

            <div className="col-md-3">
              <div className="text-center">
                <div className="text-secondary mb-3" style={{ fontSize: "2.5rem" }}>
                  📈
                </div>
                <h5>Scalable Growth</h5>
                <p className="text-muted">Build systems that grow with your business and adapt to changing needs.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-5 bg-secondary text-white">
        <div className="container text-center">
          <h2 className="mb-4">Ready to Transform Your Industry?</h2>
          <p className="lead mb-4">Let's discuss how our industry-specific solutions can benefit your organization</p>
          <a href="/contact" className="btn btn-light btn-lg">
            Get Industry-Specific Consultation
          </a>
        </div>
      </section>
    </>
  )
}
