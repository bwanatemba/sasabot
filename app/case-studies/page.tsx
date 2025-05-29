export default function CaseStudiesPage() {
  return (
    <>
      {/* Hero Section */}
      <section className="bg-primary text-white py-5">
        <div className="container">
          <div className="row">
            <div className="col-lg-8 mx-auto text-center">
              <h1 className="display-4 fw-bold mb-4">Case Studies</h1>
              <p className="lead">Real results from real businesses using SasaBot automation solutions</p>
            </div>
          </div>
        </div>
      </section>

      {/* Case Studies */}
      <section className="py-5">
        <div className="container">
          <div className="row g-5">
            {/* Case Study 1 */}
            <div className="col-lg-12">
              <div className="card border-0 shadow-lg">
                <div className="row g-0">
                  <div className="col-md-4">
                    <img
                      src="/placeholder.svg?height=300&width=400"
                      alt="Manufacturing Company"
                      className="img-fluid rounded-start h-100 object-cover"
                    />
                  </div>
                  <div className="col-md-8">
                    <div className="card-body p-5">
                      <span className="badge bg-secondary mb-3">Manufacturing</span>
                      <h3 className="text-primary mb-3">TechManufacturing Ltd: 60% Reduction in Processing Time</h3>
                      <p className="lead mb-3">
                        How we helped a mid-size manufacturing company automate their inventory management and reduce
                        order processing time by 60%.
                      </p>
                      <div className="row g-3 mb-4">
                        <div className="col-sm-4">
                          <div className="text-center">
                            <h4 className="text-secondary mb-1">60%</h4>
                            <small className="text-muted">Time Reduction</small>
                          </div>
                        </div>
                        <div className="col-sm-4">
                          <div className="text-center">
                            <h4 className="text-secondary mb-1">$200K</h4>
                            <small className="text-muted">Annual Savings</small>
                          </div>
                        </div>
                        <div className="col-sm-4">
                          <div className="text-center">
                            <h4 className="text-secondary mb-1">95%</h4>
                            <small className="text-muted">Accuracy Rate</small>
                          </div>
                        </div>
                      </div>
                      <button className="btn btn-outline-primary">Read Full Case Study</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Case Study 2 */}
            <div className="col-lg-12">
              <div className="card border-0 shadow-lg">
                <div className="row g-0">
                  <div className="col-md-8">
                    <div className="card-body p-5">
                      <span className="badge bg-secondary mb-3">Healthcare</span>
                      <h3 className="text-primary mb-3">MediCare Clinic: Streamlined Patient Management</h3>
                      <p className="lead mb-3">
                        Automated patient scheduling, billing, and record management for a growing healthcare practice.
                      </p>
                      <div className="row g-3 mb-4">
                        <div className="col-sm-4">
                          <div className="text-center">
                            <h4 className="text-secondary mb-1">40%</h4>
                            <small className="text-muted">More Patients</small>
                          </div>
                        </div>
                        <div className="col-sm-4">
                          <div className="text-center">
                            <h4 className="text-secondary mb-1">80%</h4>
                            <small className="text-muted">Less Admin Time</small>
                          </div>
                        </div>
                        <div className="col-sm-4">
                          <div className="text-center">
                            <h4 className="text-secondary mb-1">99%</h4>
                            <small className="text-muted">Compliance Rate</small>
                          </div>
                        </div>
                      </div>
                      <button className="btn btn-outline-primary">Read Full Case Study</button>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <img
                      src="/placeholder.svg?height=300&width=400"
                      alt="Healthcare Clinic"
                      className="img-fluid rounded-end h-100 object-cover"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Case Study 3 */}
            <div className="col-lg-12">
              <div className="card border-0 shadow-lg">
                <div className="row g-0">
                  <div className="col-md-4">
                    <img
                      src="/placeholder.svg?height=300&width=400"
                      alt="Retail Company"
                      className="img-fluid rounded-start h-100 object-cover"
                    />
                  </div>
                  <div className="col-md-8">
                    <div className="card-body p-5">
                      <span className="badge bg-secondary mb-3">Retail</span>
                      <h3 className="text-primary mb-3">RetailPlus: Automated Inventory & Customer Service</h3>
                      <p className="lead mb-3">
                        Complete automation of inventory management and customer service for a growing retail chain.
                      </p>
                      <div className="row g-3 mb-4">
                        <div className="col-sm-4">
                          <div className="text-center">
                            <h4 className="text-secondary mb-1">50%</h4>
                            <small className="text-muted">Cost Reduction</small>
                          </div>
                        </div>
                        <div className="col-sm-4">
                          <div className="text-center">
                            <h4 className="text-secondary mb-1">24/7</h4>
                            <small className="text-muted">Customer Support</small>
                          </div>
                        </div>
                        <div className="col-sm-4">
                          <div className="text-center">
                            <h4 className="text-secondary mb-1">98%</h4>
                            <small className="text-muted">Stock Accuracy</small>
                          </div>
                        </div>
                      </div>
                      <button className="btn btn-outline-primary">Read Full Case Study</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-5 bg-secondary text-white">
        <div className="container text-center">
          <h2 className="mb-4">Ready to Be Our Next Success Story?</h2>
          <p className="lead mb-4">Let's discuss how we can help you achieve similar results</p>
          <a href="/contact" className="btn btn-light btn-lg">
            Start Your Success Story
          </a>
        </div>
      </section>
    </>
  )
}
