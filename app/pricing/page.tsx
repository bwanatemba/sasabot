export default function PricingPage() {
  return (
    <>
      {/* Hero Section */}
      <section className="bg-primary text-white py-5">
        <div className="container">
          <div className="row">
            <div className="col-lg-8 mx-auto text-center">
              <h1 className="display-4 fw-bold mb-4">Pricing Plans</h1>
              <p className="lead">Flexible pricing options to fit businesses of all sizes</p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="py-5">
        <div className="container">
          <div className="row g-4">
            {/* Starter Plan */}
            <div className="col-lg-4">
              <div className="card border-0 shadow-lg h-100">
                <div className="card-body p-5 text-center">
                  <h3 className="text-primary mb-3">Starter</h3>
                  <div className="mb-4">
                    <span className="display-4 fw-bold">$299</span>
                    <span className="text-muted">/month</span>
                  </div>
                  <p className="lead mb-4">Perfect for small businesses getting started with automation</p>
                  <ul className="list-unstyled text-start mb-4">
                    <li className="mb-2">✅ Up to 5 automated workflows</li>
                    <li className="mb-2">✅ Basic HR automation</li>
                    <li className="mb-2">✅ Simple payroll processing</li>
                    <li className="mb-2">✅ Email support</li>
                    <li className="mb-2">✅ Basic reporting</li>
                  </ul>
                  <button className="btn btn-outline-primary btn-lg w-100">Get Started</button>
                </div>
              </div>
            </div>

            {/* Professional Plan */}
            <div className="col-lg-4">
              <div className="card border-0 shadow-lg h-100 position-relative">
                <div className="position-absolute top-0 start-50 translate-middle">
                  <span className="badge bg-secondary px-3 py-2">Most Popular</span>
                </div>
                <div className="card-body p-5 text-center">
                  <h3 className="text-primary mb-3">Professional</h3>
                  <div className="mb-4">
                    <span className="display-4 fw-bold">$799</span>
                    <span className="text-muted">/month</span>
                  </div>
                  <p className="lead mb-4">Ideal for growing businesses with complex needs</p>
                  <ul className="list-unstyled text-start mb-4">
                    <li className="mb-2">✅ Up to 25 automated workflows</li>
                    <li className="mb-2">✅ Advanced HR automation</li>
                    <li className="mb-2">✅ Full payroll processing</li>
                    <li className="mb-2">✅ Business intelligence dashboard</li>
                    <li className="mb-2">✅ Priority support</li>
                    <li className="mb-2">✅ Custom integrations</li>
                  </ul>
                  <button className="btn btn-primary btn-lg w-100">Get Started</button>
                </div>
              </div>
            </div>

            {/* Enterprise Plan */}
            <div className="col-lg-4">
              <div className="card border-0 shadow-lg h-100">
                <div className="card-body p-5 text-center">
                  <h3 className="text-primary mb-3">Enterprise</h3>
                  <div className="mb-4">
                    <span className="display-4 fw-bold">Custom</span>
                  </div>
                  <p className="lead mb-4">Tailored solutions for large organizations</p>
                  <ul className="list-unstyled text-start mb-4">
                    <li className="mb-2">✅ Unlimited workflows</li>
                    <li className="mb-2">✅ Full automation suite</li>
                    <li className="mb-2">✅ Advanced analytics</li>
                    <li className="mb-2">✅ Dedicated account manager</li>
                    <li className="mb-2">✅ 24/7 phone support</li>
                    <li className="mb-2">✅ Custom development</li>
                    <li className="mb-2">✅ On-premise deployment</li>
                  </ul>
                  <button className="btn btn-outline-primary btn-lg w-100">Contact Sales</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-5 bg-light">
        <div className="container">
          <div className="row">
            <div className="col-lg-8 mx-auto">
              <h2 className="text-center text-primary mb-5">Frequently Asked Questions</h2>
              <div className="accordion" id="pricingFAQ">
                <div className="accordion-item">
                  <h2 className="accordion-header">
                    <button className="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#faq1">
                      What's included in the setup?
                    </button>
                  </h2>
                  <div id="faq1" className="accordion-collapse collapse show" data-bs-parent="#pricingFAQ">
                    <div className="accordion-body">
                      All plans include initial setup, data migration, training, and ongoing support. We handle the
                      technical implementation so you can focus on your business.
                    </div>
                  </div>
                </div>
                <div className="accordion-item">
                  <h2 className="accordion-header">
                    <button
                      className="accordion-button collapsed"
                      type="button"
                      data-bs-toggle="collapse"
                      data-bs-target="#faq2"
                    >
                      Can I upgrade or downgrade my plan?
                    </button>
                  </h2>
                  <div id="faq2" className="accordion-collapse collapse" data-bs-parent="#pricingFAQ">
                    <div className="accordion-body">
                      Yes, you can change your plan at any time. Upgrades take effect immediately, while downgrades take
                      effect at your next billing cycle.
                    </div>
                  </div>
                </div>
                <div className="accordion-item">
                  <h2 className="accordion-header">
                    <button
                      className="accordion-button collapsed"
                      type="button"
                      data-bs-toggle="collapse"
                      data-bs-target="#faq3"
                    >
                      Is there a free trial available?
                    </button>
                  </h2>
                  <div id="faq3" className="accordion-collapse collapse" data-bs-parent="#pricingFAQ">
                    <div className="accordion-body">
                      We offer a 30-day free trial for all plans. No credit card required to get started.
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
