export default function ServicesPage() {
  return (
    <>
      {/* Hero Section */}
      <section className="bg-primary text-white py-5">
        <div className="container">
          <div className="row">
            <div className="col-lg-8 mx-auto text-center">
              <h1 className="display-4 fw-bold mb-4">Our Services</h1>
              <p className="lead">Comprehensive AI-powered automation solutions for modern enterprises</p>
            </div>
          </div>
        </div>
      </section>

      {/* Services Grid */}
      <section className="py-5">
        <div className="container">
          <div className="row g-5">
            {/* Business Intelligence */}
            <div className="col-lg-6">
              <div className="card border-0 shadow-lg h-100">
                <div className="card-body p-5">
                  <div className="text-primary mb-4" style={{ fontSize: "4rem" }}>
                    🔍
                  </div>
                  <h3 className="text-primary mb-4">Business Intelligence</h3>
                  <p className="lead mb-4">
                    Turn data into actionable insights. Our AI tools analyze your data in real time, helping you
                    identify trends, forecast outcomes, and make smarter decisions.
                  </p>
                  <ul className="list-unstyled">
                    <li className="mb-2">📊 Real-time data analysis and visualization</li>
                    <li className="mb-2">📈 Predictive analytics and forecasting</li>
                    <li className="mb-2">🎯 Custom dashboards and reporting</li>
                    <li className="mb-2">🔄 Automated data integration</li>
                    <li className="mb-2">📱 Mobile-friendly analytics platforms</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* HR Automation */}
            <div className="col-lg-6">
              <div className="card border-0 shadow-lg h-100">
                <div className="card-body p-5">
                  <div className="text-primary mb-4" style={{ fontSize: "4rem" }}>
                    👥
                  </div>
                  <h3 className="text-primary mb-4">HR Automation</h3>
                  <p className="lead mb-4">
                    Recruit faster, onboard smoother, and manage employees more efficiently. From CV screening to
                    performance tracking — we take care of the routine so your HR team can focus on people.
                  </p>
                  <ul className="list-unstyled">
                    <li className="mb-2">🎯 Automated CV screening and candidate matching</li>
                    <li className="mb-2">📋 Digital onboarding workflows</li>
                    <li className="mb-2">📊 Performance tracking and analytics</li>
                    <li className="mb-2">📅 Leave management automation</li>
                    <li className="mb-2">🎓 Training and development tracking</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Payroll Processing */}
            <div className="col-lg-6">
              <div className="card border-0 shadow-lg h-100">
                <div className="card-body p-5">
                  <div className="text-primary mb-4" style={{ fontSize: "4rem" }}>
                    💰
                  </div>
                  <h3 className="text-primary mb-4">Payroll Processing</h3>
                  <p className="lead mb-4">
                    Accurate, timely, and compliant payroll solutions powered by automation. We ensure your staff gets
                    paid right — every time, on time.
                  </p>
                  <ul className="list-unstyled">
                    <li className="mb-2">⚡ Automated payroll calculations</li>
                    <li className="mb-2">📋 Tax compliance and reporting</li>
                    <li className="mb-2">🏦 Direct deposit and payment processing</li>
                    <li className="mb-2">📊 Payroll analytics and insights</li>
                    <li className="mb-2">🔒 Secure and compliant data handling</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Process Automation */}
            <div className="col-lg-6">
              <div className="card border-0 shadow-lg h-100">
                <div className="card-body p-5">
                  <div className="text-primary mb-4" style={{ fontSize: "4rem" }}>
                    🔄
                  </div>
                  <h3 className="text-primary mb-4">Process Automation</h3>
                  <p className="lead mb-4">
                    We identify bottlenecks and automate repetitive tasks across departments — from finance to customer
                    service — improving overall productivity and cost-efficiency.
                  </p>
                  <ul className="list-unstyled">
                    <li className="mb-2">🔍 Process analysis and optimization</li>
                    <li className="mb-2">🤖 Robotic Process Automation (RPA)</li>
                    <li className="mb-2">📧 Automated workflows and notifications</li>
                    <li className="mb-2">📋 Document processing and management</li>
                    <li className="mb-2">🔗 System integration and API development</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Additional Services */}
      <section className="py-5 bg-light">
        <div className="container">
          <div className="row">
            <div className="col-lg-8 mx-auto text-center mb-5">
              <h2 className="text-primary mb-4">Additional Services</h2>
              <p className="lead">
                Beyond our core offerings, we provide comprehensive support for your automation journey
              </p>
            </div>
          </div>

          <div className="row g-4">
            <div className="col-md-4">
              <div className="card border-0 shadow-sm h-100">
                <div className="card-body text-center p-4">
                  <div className="text-secondary mb-3" style={{ fontSize: "2.5rem" }}>
                    🔧
                  </div>
                  <h5 className="text-primary">Implementation & Integration</h5>
                  <p className="text-muted">
                    Seamless integration with your existing systems and smooth implementation processes.
                  </p>
                </div>
              </div>
            </div>

            <div className="col-md-4">
              <div className="card border-0 shadow-sm h-100">
                <div className="card-body text-center p-4">
                  <div className="text-secondary mb-3" style={{ fontSize: "2.5rem" }}>
                    🎓
                  </div>
                  <h5 className="text-primary">Training & Support</h5>
                  <p className="text-muted">
                    Comprehensive training programs and ongoing support to maximize your ROI.
                  </p>
                </div>
              </div>
            </div>

            <div className="col-md-4">
              <div className="card border-0 shadow-sm h-100">
                <div className="card-body text-center p-4">
                  <div className="text-secondary mb-3" style={{ fontSize: "2.5rem" }}>
                    📈
                  </div>
                  <h5 className="text-primary">Consulting & Strategy</h5>
                  <p className="text-muted">
                    Strategic consulting to identify automation opportunities and develop roadmaps.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-5 bg-secondary text-white">
        <div className="container text-center">
          <h2 className="mb-4">Ready to Get Started?</h2>
          <p className="lead mb-4">Let's discuss how our services can transform your business operations</p>
          <a href="/contact" className="btn btn-light btn-lg">
            Schedule a Consultation
          </a>
        </div>
      </section>
    </>
  )
}
