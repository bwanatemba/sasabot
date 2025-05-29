"use client"

import type React from "react"

import { useState } from "react"

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    company: "",
    phone: "",
    service: "",
    message: "",
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Handle form submission here
    console.log("Form submitted:", formData)
    alert("Thank you for your message! We will get back to you soon.")
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  return (
    <>
      {/* Hero Section */}
      <section className="bg-primary text-white py-5">
        <div className="container">
          <div className="row">
            <div className="col-lg-8 mx-auto text-center">
              <h1 className="display-4 fw-bold mb-4">Contact Us</h1>
              <p className="lead">Ready to transform your business? Let's start the conversation.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Contact Form & Info */}
      <section className="py-5">
        <div className="container">
          <div className="row g-5">
            {/* Contact Form */}
            <div className="col-lg-8">
              <div className="card border-0 shadow-lg">
                <div className="card-body p-5">
                  <h2 className="text-primary mb-4">Get in Touch</h2>
                  <p className="mb-4">
                    Fill out the form below and we'll get back to you within 24 hours to discuss how SasaBot can help
                    automate your business processes.
                  </p>

                  <form onSubmit={handleSubmit}>
                    <div className="row g-3">
                      <div className="col-md-6">
                        <label htmlFor="name" className="form-label">
                          Full Name *
                        </label>
                        <input
                          type="text"
                          className="form-control"
                          id="name"
                          name="name"
                          value={formData.name}
                          onChange={handleChange}
                          required
                        />
                      </div>

                      <div className="col-md-6">
                        <label htmlFor="email" className="form-label">
                          Email Address *
                        </label>
                        <input
                          type="email"
                          className="form-control"
                          id="email"
                          name="email"
                          value={formData.email}
                          onChange={handleChange}
                          required
                        />
                      </div>

                      <div className="col-md-6">
                        <label htmlFor="company" className="form-label">
                          Company Name
                        </label>
                        <input
                          type="text"
                          className="form-control"
                          id="company"
                          name="company"
                          value={formData.company}
                          onChange={handleChange}
                        />
                      </div>

                      <div className="col-md-6">
                        <label htmlFor="phone" className="form-label">
                          Phone Number
                        </label>
                        <input
                          type="tel"
                          className="form-control"
                          id="phone"
                          name="phone"
                          value={formData.phone}
                          onChange={handleChange}
                        />
                      </div>

                      <div className="col-12">
                        <label htmlFor="service" className="form-label">
                          Service of Interest
                        </label>
                        <select
                          className="form-select"
                          id="service"
                          name="service"
                          value={formData.service}
                          onChange={handleChange}
                        >
                          <option value="">Select a service...</option>
                          <option value="business-intelligence">Business Intelligence</option>
                          <option value="hr-automation">HR Automation</option>
                          <option value="payroll-processing">Payroll Processing</option>
                          <option value="process-automation">Process Automation</option>
                          <option value="consultation">General Consultation</option>
                        </select>
                      </div>

                      <div className="col-12">
                        <label htmlFor="message" className="form-label">
                          Message *
                        </label>
                        <textarea
                          className="form-control"
                          id="message"
                          name="message"
                          rows={5}
                          value={formData.message}
                          onChange={handleChange}
                          placeholder="Tell us about your automation needs and challenges..."
                          required
                        ></textarea>
                      </div>

                      <div className="col-12">
                        <button type="submit" className="btn btn-primary btn-lg">
                          Send Message
                        </button>
                      </div>
                    </div>
                  </form>
                </div>
              </div>
            </div>

            {/* Contact Information */}
            <div className="col-lg-4">
              <div className="card border-0 shadow-lg h-100">
                <div className="card-body p-5">
                  <h3 className="text-primary mb-4">Contact Information</h3>

                  <div className="mb-4">
                    <h6 className="text-secondary mb-2">📍 Address</h6>
                    <p className="mb-0">Nairobi, Kenya</p>
                  </div>

                  <div className="mb-4">
                    <h6 className="text-secondary mb-2">📞 Phone</h6>
                    <p className="mb-0">+254 762222000</p>
                  </div>

                  <div className="mb-4">
                    <h6 className="text-secondary mb-2">📧 Email</h6>
                    <p className="mb-0">info@sasabot.tech</p>
                  </div>

                  <div className="mb-4">
                    <h6 className="text-secondary mb-2">🌐 Website</h6>
                    <p className="mb-0">https://sasabot.tech</p>
                  </div>

                  <hr className="my-4" />

                  <h6 className="text-secondary mb-3">Business Hours</h6>
                  <p className="mb-1">
                    <strong>Monday - Friday:</strong> 8:00 AM - 6:00 PM
                  </p>
                  <p className="mb-1">
                    <strong>Saturday:</strong> 9:00 AM - 2:00 PM
                  </p>
                  <p className="mb-0">
                    <strong>Sunday:</strong> Closed
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-5 bg-light">
        <div className="container">
          <div className="row">
            <div className="col-lg-8 mx-auto text-center">
              <h2 className="text-primary mb-4">Ready to Get Started?</h2>
              <p className="lead mb-4">
                Schedule a free consultation to discuss your automation needs and see how SasaBot can transform your
                business operations.
              </p>
              <div className="d-flex flex-wrap justify-content-center gap-3">
                <button className="btn btn-primary btn-lg">Book a Demo</button>
                <button className="btn btn-outline-primary btn-lg">Download Brochure</button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
