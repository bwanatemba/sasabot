export default function SolutionsPage() {
  return (
    <>
      {/* Hero Section */}
      <section className="bg-primary text-white py-5">
        <div className="container">
          <div className="row">
            <div className="col-lg-8 mx-auto text-center">
              <h1 className="display-4 fw-bold mb-4">Our Solutions</h1>
              <p className="lead">Comprehensive automation solutions tailored to your business needs</p>
            </div>
          </div>
        </div>
      </section>

      {/* Solutions Overview */}
      <section className="py-5">
        <div className="container">
          <div className="row g-5">
            <div className="col-lg-6">
              <h2 className="text-primary mb-4">Enterprise Solutions</h2>
              <p className="lead mb-4">
                Scalable automation platforms designed for large organizations with complex workflows and multiple
                departments.
              </p>
              <ul className="list-unstyled">
                <li className="mb-3">
                  🏢 <strong>Multi-department Integration</strong> - Seamless workflow automation across all business
                  units
                </li>
                <li className="mb-3">
                  📊 <strong>Advanced Analytics Dashboard</strong> - Real-time insights and performance monitoring
                </li>
                <li className="mb-3">
                  🔒 <strong>Enterprise Security</strong> - Bank-level security with compliance management
                </li>
                <li className="mb-3">
                  ⚡ <strong>High-volume Processing</strong> - Handle thousands of transactions per minute
                </li>
              </ul>
            </div>
            <div className="col-lg-6">
              <img
                src="/placeholder.svg?height=400&width=500"
                alt="Enterprise Solutions"
                className="img-fluid rounded shadow"
              />
            </div>
          </div>
        </div>
      </section>

      {/* SMB Solutions */}
      <section className="py-5 bg-light">
        <div className="container">
          <div className="row g-5">
            <div className="col-lg-6">
              <img
                src="/placeholder.svg?height=400&width=500"
                alt="SMB Solutions"
                className="img-fluid rounded shadow"
              />
            </div>
            <div className="col-lg-6">
              <h2 className="text-primary mb-4">Small & Medium Business Solutions</h2>
              <p className="lead mb-4">
                Cost-effective automation tools that grow with your business, perfect for startups and growing
                companies.
              </p>
              <ul className="list-unstyled">
                <li className="mb-3">
                  💰 <strong>Affordable Pricing</strong> - Flexible plans that fit your budget
                </li>
                <li className="mb-3">
                  🚀 <strong>Quick Implementation</strong> - Get started in days, not months
                </li>
                <li className="mb-3">
                  📈 <strong>Scalable Architecture</strong> - Easily upgrade as your business grows
                </li>
                <li className="mb-3">
                  🎯 <strong>Focused Features</strong> - Essential automation without complexity
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Industry-Specific Solutions */}
      <section className="py-5">
        <div className="container">
          <h2 className="text-center text-primary mb-5">Industry-Specific Solutions</h2>
          <div className="row g-4">
            <div className="col-md-4">
              <div className="card border-0 shadow-sm h-100">
                <div className="card-body text-center p-4">
                  <div className="text-primary mb-3" style={{ fontSize: "3rem" }}>
                    🏥
                  </div>
                  <h5 className="text-primary">Healthcare Suite</h5>
                  <p>HIPAA-compliant automation for patient management, billing, and compliance.</p>
                </div>
              </div>
            </div>
            <div className="col-md-4">
              <div className="card border-0 shadow-sm h-100">
                <div className="card-body text-center p-4">
                  <div className="text-primary mb-3" style={{ fontSize: "3rem" }}>
                    🏦
                  </div>
                  <h5 className="text-primary">Financial Services</h5>
                  <p>Secure automation for banking, insurance, and financial compliance.</p>
                </div>
              </div>
            </div>
            <div className="col-md-4">
              <div className="card border-0 shadow-sm h-100">
                <div className="card-body text-center p-4">
                  <div className="text-primary mb-3" style={{ fontSize: "3rem" }}>
                    🏭
                  </div>
                  <h5 className="text-primary">Manufacturing</h5>
                  <p>Production optimization, quality control, and supply chain automation.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
