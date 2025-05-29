export default function AboutPage() {
  return (
    <>
      {/* Hero Section */}
      <section className="bg-primary text-white py-5">
        <div className="container">
          <div className="row">
            <div className="col-lg-8 mx-auto text-center">
              <h1 className="display-4 fw-bold mb-4">About SasaBot Technologies</h1>
              <p className="lead">Founded with the vision to bring intelligent automation to every business</p>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section className="py-5">
        <div className="container">
          <div className="row">
            <div className="col-lg-8 mx-auto">
              <div className="mb-5">
                <h2 className="text-primary mb-4">Our Mission</h2>
                <p className="lead">
                  SasaBot Technologies combines AI innovation with a passion for problem-solving. We're on a mission to
                  help businesses operate smarter, scale faster, and lead in a digital-first world.
                </p>
                <p>
                  We believe that every business, regardless of size, should have access to cutting-edge automation
                  technology. Our team of experts works tirelessly to create solutions that not only solve today's
                  challenges but also prepare organizations for tomorrow's opportunities.
                </p>
              </div>

              <div className="mb-5">
                <h2 className="text-primary mb-4">Our Vision</h2>
                <p>
                  To be the leading provider of AI-powered business automation solutions, empowering organizations
                  worldwide to achieve unprecedented levels of efficiency, accuracy, and growth through intelligent
                  technology.
                </p>
              </div>

              <div className="mb-5">
                <h2 className="text-primary mb-4">Our Values</h2>
                <div className="row g-4">
                  <div className="col-md-6">
                    <div className="card border-0 shadow-sm h-100">
                      <div className="card-body">
                        <h5 className="text-secondary">Innovation</h5>
                        <p>We continuously push the boundaries of what's possible with AI and automation.</p>
                      </div>
                    </div>
                  </div>

                  <div className="col-md-6">
                    <div className="card border-0 shadow-sm h-100">
                      <div className="card-body">
                        <h5 className="text-secondary">Excellence</h5>
                        <p>We deliver solutions that exceed expectations and drive measurable results.</p>
                      </div>
                    </div>
                  </div>

                  <div className="col-md-6">
                    <div className="card border-0 shadow-sm h-100">
                      <div className="card-body">
                        <h5 className="text-secondary">Partnership</h5>
                        <p>We work closely with our clients as trusted partners in their digital transformation.</p>
                      </div>
                    </div>
                  </div>

                  <div className="col-md-6">
                    <div className="card border-0 shadow-sm h-100">
                      <div className="card-body">
                        <h5 className="text-secondary">Integrity</h5>
                        <p>We maintain the highest standards of ethics and transparency in all our dealings.</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mb-5">
                <h2 className="text-primary mb-4">Our Approach</h2>
                <p>
                  At SasaBot Technologies, we understand that every business is unique. That's why we take a
                  consultative approach to automation, working closely with our clients to:
                </p>
                <ul className="list-unstyled">
                  <li className="mb-2">
                    🔍 <strong>Analyze</strong> your current processes and identify automation opportunities
                  </li>
                  <li className="mb-2">
                    🎯 <strong>Design</strong> custom solutions tailored to your specific needs
                  </li>
                  <li className="mb-2">
                    🚀 <strong>Implement</strong> solutions with minimal disruption to your operations
                  </li>
                  <li className="mb-2">
                    📈 <strong>Optimize</strong> and scale your automation as your business grows
                  </li>
                  <li className="mb-2">
                    🛠️ <strong>Support</strong> you with ongoing maintenance and improvements
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section className="py-5 bg-light">
        <div className="container">
          <div className="row">
            <div className="col-lg-8 mx-auto text-center">
              <h2 className="text-primary mb-4">Our Expertise</h2>
              <p className="lead mb-5">
                Our team brings together decades of experience in AI, automation, and business process optimization.
              </p>

              <div className="row g-4">
                <div className="col-md-4">
                  <div className="text-center">
                    <div className="text-primary mb-3" style={{ fontSize: "3rem" }}>
                      🤖
                    </div>
                    <h5>AI & Machine Learning</h5>
                    <p className="text-muted">
                      Deep expertise in artificial intelligence and machine learning technologies.
                    </p>
                  </div>
                </div>

                <div className="col-md-4">
                  <div className="text-center">
                    <div className="text-primary mb-3" style={{ fontSize: "3rem" }}>
                      ⚙️
                    </div>
                    <h5>Process Automation</h5>
                    <p className="text-muted">Proven track record in automating complex business processes.</p>
                  </div>
                </div>

                <div className="col-md-4">
                  <div className="text-center">
                    <div className="text-primary mb-3" style={{ fontSize: "3rem" }}>
                      💼
                    </div>
                    <h5>Business Strategy</h5>
                    <p className="text-muted">Strategic thinking to align technology solutions with business goals.</p>
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
