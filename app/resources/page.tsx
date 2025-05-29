export default function ResourcesPage() {
  return (
    <>
      {/* Hero Section */}
      <section className="bg-primary text-white py-5">
        <div className="container">
          <div className="row">
            <div className="col-lg-8 mx-auto text-center">
              <h1 className="display-4 fw-bold mb-4">Resources</h1>
              <p className="lead">Guides, whitepapers, and insights to help you understand business automation</p>
            </div>
          </div>
        </div>
      </section>

      {/* Resource Categories */}
      <section className="py-5">
        <div className="container">
          <div className="row g-4">
            {/* Whitepapers */}
            <div className="col-lg-4">
              <div className="card border-0 shadow-sm h-100">
                <div className="card-body p-4">
                  <div className="text-primary mb-3" style={{ fontSize: "3rem" }}>
                    📄
                  </div>
                  <h4 className="text-primary mb-3">Whitepapers</h4>
                  <div className="list-group list-group-flush">
                    <div className="list-group-item border-0 px-0">
                      <h6>The ROI of Business Automation</h6>
                      <small className="text-muted">Learn how to calculate and maximize your automation ROI</small>
                    </div>
                    <div className="list-group-item border-0 px-0">
                      <h6>AI in Modern Business</h6>
                      <small className="text-muted">Understanding AI applications in business processes</small>
                    </div>
                    <div className="list-group-item border-0 px-0">
                      <h6>Digital Transformation Guide</h6>
                      <small className="text-muted">Step-by-step guide to digital transformation</small>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Guides */}
            <div className="col-lg-4">
              <div className="card border-0 shadow-sm h-100">
                <div className="card-body p-4">
                  <div className="text-primary mb-3" style={{ fontSize: "3rem" }}>
                    📚
                  </div>
                  <h4 className="text-primary mb-3">Implementation Guides</h4>
                  <div className="list-group list-group-flush">
                    <div className="list-group-item border-0 px-0">
                      <h6>Getting Started with Automation</h6>
                      <small className="text-muted">A beginner's guide to business automation</small>
                    </div>
                    <div className="list-group-item border-0 px-0">
                      <h6>HR Automation Checklist</h6>
                      <small className="text-muted">Essential steps for HR process automation</small>
                    </div>
                    <div className="list-group-item border-0 px-0">
                      <h6>Payroll Automation Best Practices</h6>
                      <small className="text-muted">Optimize your payroll processes</small>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Tools & Templates */}
            <div className="col-lg-4">
              <div className="card border-0 shadow-sm h-100">
                <div className="card-body p-4">
                  <div className="text-primary mb-3" style={{ fontSize: "3rem" }}>
                    🛠️
                  </div>
                  <h4 className="text-primary mb-3">Tools & Templates</h4>
                  <div className="list-group list-group-flush">
                    <div className="list-group-item border-0 px-0">
                      <h6>ROI Calculator</h6>
                      <small className="text-muted">Calculate potential savings from automation</small>
                    </div>
                    <div className="list-group-item border-0 px-0">
                      <h6>Process Mapping Template</h6>
                      <small className="text-muted">Map your current business processes</small>
                    </div>
                    <div className="list-group-item border-0 px-0">
                      <h6>Automation Readiness Assessment</h6>
                      <small className="text-muted">Evaluate your automation readiness</small>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Resources */}
      <section className="py-5 bg-light">
        <div className="container">
          <h2 className="text-center text-primary mb-5">Featured Resources</h2>
          <div className="row g-4">
            <div className="col-md-6">
              <div className="card border-0 shadow-lg">
                <img src="/placeholder.svg?height=200&width=400" alt="Automation Guide" className="card-img-top" />
                <div className="card-body p-4">
                  <span className="badge bg-secondary mb-2">New</span>
                  <h5 className="card-title">Complete Guide to Business Process Automation</h5>
                  <p className="card-text">
                    A comprehensive 50-page guide covering everything you need to know about implementing automation in
                    your business.
                  </p>
                  <button className="btn btn-primary">Download Free</button>
                </div>
              </div>
            </div>
            <div className="col-md-6">
              <div className="card border-0 shadow-lg">
                <img src="/placeholder.svg?height=200&width=400" alt="AI Webinar" className="card-img-top" />
                <div className="card-body p-4">
                  <span className="badge bg-primary mb-2">Webinar</span>
                  <h5 className="card-title">AI-Powered Automation: What's Next?</h5>
                  <p className="card-text">
                    Join our experts for a live discussion on the future of AI in business automation and emerging
                    trends.
                  </p>
                  <button className="btn btn-outline-primary">Register Now</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
