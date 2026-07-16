# aa_transportation_system.py
# COMPLETE WORKING AA TRANSPORTATION MANAGEMENT SYSTEM
# Run: python aa_transportation_system.py
# Login: admin / admin

import sqlite3
from flask import Flask, request, redirect, session, render_template_string, jsonify
from datetime import date, datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'aa-transportation-secret-2025'
DB = 'aa_transportation.db'

LOGIN_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AA Transportation - Secure Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
        :root {
            --primary-color: #0f172a;
            --accent-color: #3b82f6;
            --text-gray: #64748b;
        }

        body {
            background: linear-gradient(rgba(15, 23, 42, 0.8), rgba(15, 23, 42, 0.8)), 
                        url('https://images.unsplash.com/photo-1503376780353-7e6692767b70?q=80&w=2070&auto=format&fit=crop');
            background-size: cover;
            background-position: center;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            margin: 0;
            overflow: hidden;
        }

        .login-card {
            background: rgba(255, 255, 255, 0.98);
            border-radius: 24px;
            padding: 40px;
            width: 100%;
            max-width: 450px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            position: relative;
            z-index: 1;
        }

        /* Branding Section */
        .brand-logo {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            box-shadow: 0 10px 20px rgba(59, 130, 246, 0.3);
        }

        .brand-logo i {
            font-size: 2.5rem;
            color: white;
        }

        .login-header h2 {
            color: var(--primary-color);
            font-weight: 800;
            letter-spacing: -0.5px;
            margin-bottom: 8px;
            text-align: center;
        }

        .login-header p {
            color: var(--text-gray);
            text-align: center;
            margin-bottom: 30px;
            font-size: 0.95rem;
        }

        /* Input Styling */
        .form-label {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--primary-color);
            margin-left: 4px;
        }

        .input-group-text {
            background-color: transparent;
            border-right: none;
            color: var(--text-gray);
            padding-left: 15px;
        }

        .form-control {
            border-left: none;
            padding: 12px 15px;
            font-size: 1rem;
            border-radius: 0 10px 10px 0;
            border: 1px solid #e2e8f0;
        }

        .form-control:focus {
            box-shadow: none;
            border-color: #e2e8f0;
            background-color: #f8fafc;
        }

        .input-group:focus-within {
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
            border-radius: 10px;
        }

        /* Button Styling */
        .btn-login {
            background: var(--primary-color);
            border: none;
            color: white;
            padding: 14px;
            border-radius: 12px;
            font-weight: 600;
            width: 100%;
            margin-top: 10px;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }

        .btn-login:hover {
            background: #1e293b;
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }

        /* Footer Section */
        .company-footer {
            margin-top: 35px;
            padding-top: 25px;
            border-top: 1px solid #f1f5f9;
            text-align: center;
        }

        .dev-tag {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-gray);
            margin-bottom: 5px;
        }

        .dev-name {
            color: var(--primary-color);
            font-weight: 700;
            text-decoration: none;
            font-size: 0.9rem;
        }

        .contact-pill {
            display: inline-block;
            background: #f1f5f9;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            color: var(--accent-color);
            margin-top: 8px;
            font-weight: 600;
        }

        /* Alert styling */
        .alert {
            border-radius: 12px;
            font-size: 0.9rem;
            border: none;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="brand-logo">
            <i class="bi bi-shield-lock"></i>
        </div>
        
        <div class="login-header">
            <h2>AA Transportation</h2>
            <p>Vehicle Management System v2.0</p>
        </div>
        
        {% if error %}
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="bi bi-exclamation-triangle-fill me-2"></i> {{ error }}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
        {% endif %}
        
        <form method="POST">
            <div class="mb-3">
                <label class="form-label">Username</label>
                <div class="input-group">
                    <span class="input-group-text"><i class="bi bi-person"></i></span>
                    <input type="text" name="username" class="form-control" placeholder="Enter username" required autofocus>
                </div>
            </div>
            
            <div class="mb-4">
                <label class="form-label">Password</label>
                <div class="input-group">
                    <span class="input-group-text"><i class="bi bi-key"></i></span>
                    <input type="password" name="password" class="form-control" placeholder="••••••••" required>
                </div>
            </div>
            
            <button type="submit" class="btn-login">
                Sign In to Dashboard <i class="bi bi-arrow-right"></i>
            </button>
        </form>

        <div class="company-footer">
            <div class="dev-tag">System Developed By</div>
            <div class="dev-name">Muhammad Ahtesham Ul Haq</div>
            <div class="contact-pill">
                <i class="bi bi-whatsapp me-1"></i> +92 345 9880990
            </div>
            <div class="mt-2 text-muted" style="font-size: 0.7rem;">
                &copy; 2025 Teccea Solutions. All Rights Reserved.
            </div>
        </div>
    </div>
</body>
</html>
'''
BASE_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AA Transportation - {{ title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
        :root {
            --primary: #1e3c72;
            --primary-light: #e0e7ff;
            --secondary: #2a5298;
            --success: #28a745;
            --warning: #ffc107;
            --danger: #dc3545;
            --info: #17a2b8;
        }
        
        body {
            background-color: #f8f9fa;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            color: #333;
        }
        
        .navbar {
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 1rem 0;
        }
        
        .navbar-brand {
            font-weight: 700;
            color: var(--primary) !important;
            font-size: 1.5rem;
        }
        
        .sidebar {
            background: white;
            min-height: calc(100vh - 70px);
            border-right: 1px solid #dee2e6;
            padding-top: 20px;
            position: sticky;
            top: 70px;
        }
        
        .sidebar a {
            display: block;
            padding: 12px 20px;
            color: #495057;
            text-decoration: none;
            border-left: 3px solid transparent;
            margin-bottom: 5px;
            transition: all 0.2s;
            font-weight: 500;
        }
        
        .sidebar a:hover {
            background-color: var(--primary-light);
            color: var(--primary);
            border-left-color: var(--primary);
        }
        
        .sidebar a.active {
            background-color: var(--primary-light);
            color: var(--primary);
            border-left-color: var(--primary);
        }
        
        .main-content {
            padding: 30px;
            background-color: #f8f9fa;
            min-height: calc(100vh - 70px);
        }
        
        .card {
            border: none;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            margin-bottom: 24px;
            background: white;
        }
        
        .card-header {
            background: white;
            border-bottom: 1px solid #dee2e6;
            padding: 20px;
            border-radius: 10px 10px 0 0 !important;
            font-weight: 600;
            color: var(--primary);
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: 500;
        }
        
        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(30, 60, 114, 0.2);
        }
        
        .table {
            background: white;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #dee2e6;
        }
        
        .table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
            padding: 15px;
        }
        
        .table td {
            padding: 15px;
            vertical-align: middle;
            border-color: #e9ecef;
        }
        
        .modal-header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
        }
        
        .form-control, .form-select {
            border-radius: 6px;
            border: 2px solid #e9ecef;
            padding: 10px;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-light">
        <div class="container-fluid">
            <a class="navbar-brand" href="/dashboard">
                <i class="bi bi-car-front-fill me-2"></i>AA Transportation
            </a>
            <div class="d-flex align-items-center">
                <span class="me-3 text-muted">
                    <i class="bi bi-person-circle me-1"></i>{{ session.user }}
                </span>
                <a href="/logout" class="btn btn-outline-primary btn-sm">
                    <i class="bi bi-box-arrow-right me-1"></i>Logout
                </a>
            </div>
        </div>
    </nav>

    <div class="container-fluid">
        <div class="row">
            <div class="col-lg-2 col-xl-2 sidebar text-dark">
                <h6 class="text-uppercase text-muted mb-3 px-3 fw-bold">MAIN MENU</h6>
                <div class="nav flex-column">
                    <a href="/dashboard" class="{{ 'active' if request.path == '/dashboard' else '' }}">
                        <i class="bi bi-speedometer2 me-2"></i>Dashboard
                    </a>
                    <a href="/investors" class="{{ 'active' if request.path == '/investors' else '' }}">
                        <i class="bi bi-people me-2"></i>Investors/Owners
                    </a>
                    <a href="/companies" class="{{ 'active' if request.path == '/companies' else '' }}">
                        <i class="bi bi-building me-2"></i>Companies
                    </a>
                    <a href="/vehicles" class="{{ 'active' if request.path == '/vehicles' else '' }}">
                        <i class="bi bi-truck me-2"></i>Vehicles
                    </a>
                    <a href="/short-term-rentals" class="{{ 'active' if request.path == '/short-term-rentals' else '' }}">
                        <i class="bi bi-calendar-week me-2"></i>Short-term Rentals
                    </a>
                    <a href="/agents" class="{{ 'active' if request.path == '/agents' else '' }}">
                        <i class="bi bi-person-badge me-2"></i>Agents
                    </a>
                    <a href="/maintenance" class="{{ 'active' if request.path == '/maintenance' else '' }}">
                        <i class="bi bi-wrench-adjustable me-2"></i>Maintenance
                    </a>
                </div>

                <hr class="my-3 mx-3">
                <h6 class="text-uppercase text-muted mb-3 px-3 fw-bold">CONTRACTS</h6>
                <div class="nav flex-column">
                    <a href="/contracts" class="{{ 'active' if request.path == '/contracts' else '' }}">
                        <i class="bi bi-file-text me-2"></i>Contract Management
                    </a>
                </div>
                
                <hr class="my-3 mx-3">
                <h6 class="text-uppercase text-muted mb-3 px-3 fw-bold">FINANCIAL</h6>
                <div class="nav flex-column">
                    <a href="/investor-payments" class="{{ 'active' if request.path == '/investor-payments' else '' }}">
                        <i class="bi bi-cash-coin me-2"></i>Investor Payments
                    </a>
                    <a href="/agent-commissions" class="{{ 'active' if request.path == '/agent-commissions' else '' }}">
                        <i class="bi bi-percent me-2"></i>Agent Commissions
                    </a>
                </div>
                
                <hr class="my-3 mx-3">
                <h6 class="text-uppercase text-muted mb-3 px-3 fw-bold">REPORTS</h6>
                <div class="nav flex-column">
                    <a href="/reports/profit-loss" class="{{ 'active' if request.path == '/reports/profit-loss' else '' }}">
                        <i class="bi bi-graph-up me-2"></i>Profit & Loss
                    </a>
                </div>
            </div>
            
            <div class="col-lg-10 col-xl-10 main-content">
                {{ content|safe }}
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''
CONTRACTS_PAGE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AA Transportation - Contracts</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
        :root {
            --primary: #1e3c72;
            --primary-light: #e0e7ff;
            --secondary: #2a5298;
        }

        body {
            background-color: #f8f9fa;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        .navbar {
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 1rem 0;
        }

        .navbar-brand {
            font-weight: 700;
            color: var(--primary) !important;
            font-size: 1.5rem;
        }

        .sidebar {
            background: white;
            min-height: calc(100vh - 70px);
            border-right: 1px solid #dee2e6;
            padding-top: 20px;
            position: sticky;
            top: 70px;
        }

        .sidebar a {
            display: block;
            padding: 12px 20px;
            color: #495057;
            text-decoration: none;
            border-left: 3px solid transparent;
            margin-bottom: 5px;
            transition: all 0.2s;
            font-weight: 500;
        }

        .sidebar a:hover, .sidebar a.active {
            background-color: var(--primary-light);
            color: var(--primary);
            border-left-color: var(--primary);
        }

        .main-content {
            padding: 30px;
            background-color: #f8f9fa;
            min-height: calc(100vh - 70px);
        }

        .card {
            border: none;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            margin-bottom: 24px;
            background: white;
        }

        .card-header {
            background: white;
            border-bottom: 1px solid #dee2e6;
            padding: 20px;
            border-radius: 10px 10px 0 0 !important;
            font-weight: 600;
            color: var(--primary);
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: 500;
        }

        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(30, 60, 114, 0.2);
        }

        .nav-tabs .nav-link {
            color: #6c757d;
            border: none;
            border-bottom: 3px solid transparent;
            padding: 12px 24px;
        }

        .nav-tabs .nav-link:hover {
            border-bottom-color: var(--primary-light);
            color: var(--primary);
        }

        .nav-tabs .nav-link.active {
            color: var(--primary);
            border-bottom-color: var(--primary);
            background: transparent;
        }

        .info-box {
            background: #f8f9fa;
            border-left: 4px solid var(--primary);
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }

        .form-select, .form-control {
            border-radius: 6px;
            border: 2px solid #e9ecef;
            padding: 10px;
        }

        .form-select:focus, .form-control:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(30, 60, 114, 0.1);
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-light">
        <div class="container-fluid">
            <a class="navbar-brand" href="/dashboard">
                <i class="bi bi-car-front-fill me-2"></i>AA Transportation
            </a>

            <div class="d-flex align-items-center">
                <span class="me-3 text-muted">
                    <i class="bi bi-person-circle me-1"></i>{{ session.user }}
                </span>
                <a href="/logout" class="btn btn-outline-primary btn-sm">
                    <i class="bi bi-box-arrow-right me-1"></i>Logout
                </a>
            </div>
        </div>
    </nav>
    <div class="container-fluid">
        <div class="row">
            <!-- Sidebar -->
            <div class="col-lg-2 col-xl-2 sidebar">
                <h6 class="text-uppercase text-muted mb-3 px-3 fw-bold">MAIN MENU</h6>
                <div class="nav flex-column">
                    <a href="/dashboard">
                        <i class="bi bi-speedometer2 me-2"></i>Dashboard
                    </a>
                    <a href="/investors">
                        <i class="bi bi-people me-2"></i>Investors/Owners
                    </a>
                    <a href="/companies">
                        <i class="bi bi-building me-2"></i>Companies
                    </a>
                    <a href="/vehicles">
                        <i class="bi bi-truck me-2"></i>Vehicles
                    </a>
                    <a href="/short-term-rentals">
                        <i class="bi bi-calendar-week me-2"></i>Short-term Rentals
                    </a>
                    <a href="/agents">
                        <i class="bi bi-person-badge me-2"></i>Agents
                    </a>
                </div>

                <hr class="my-3 mx-3">

                <h6 class="text-uppercase text-muted mb-3 px-3 fw-bold">CONTRACTS</h6>
                <div class="nav flex-column">
                    <a href="/contracts" class="active">
                        <i class="bi bi-file-text me-2"></i>Contract Management
                    </a>
                </div>

                <hr class="my-3 mx-3">

                <h6 class="text-uppercase text-muted mb-3 px-3 fw-bold">FINANCIAL</h6>
                <div class="nav flex-column">
                    <a href="/investor-payments">
                        <i class="bi bi-cash-coin me-2"></i>Investor Payments
                    </a>
                    <a href="/agent-commissions">
                        <i class="bi bi-percent me-2"></i>Agent Commissions
                    </a>
                </div>

                <hr class="my-3 mx-3">

                <h6 class="text-uppercase text-muted mb-3 px-3 fw-bold">REPORTS</h6>
                <div class="nav flex-column">
                    <a href="/reports/profit-loss">
                        <i class="bi bi-graph-up me-2"></i>Profit & Loss
                    </a>
                </div>
            </div>

            <!-- Main Content -->
            <div class="col-lg-10 col-xl-10 main-content">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h4 class="fw-bold mb-1"><i class="bi bi-file-text me-2"></i>Contract Management</h4>
                        <p class="text-muted mb-0">Generate and download rental agreements for companies and vendors</p>
                    </div>
                </div>
                <!-- Tabs -->
                <ul class="nav nav-tabs mb-4" role="tablist">
                    <li class="nav-item">
                        <a class="nav-link active" data-bs-toggle="tab" href="#company-tab">
                            <i class="bi bi-building me-2"></i>Company Contract
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" data-bs-toggle="tab" href="#vendor-tab">
                            <i class="bi bi-person-check me-2"></i>Owner/Vendor Contract
                        </a>
                    </li>
                </ul>
                <div class="tab-content">
                    <!-- Company Contract Tab -->
                    <div class="tab-pane fade show active" id="company-tab">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0"><i class="bi bi-building me-2"></i>Company Rental Agreement</h6>
                            </div>
                            <div class="card-body">
                                <p class="text-muted">Select a company to generate their rental agreement. The agreement will be populated with company details and can be printed or downloaded as PDF.</p>

                                <form method="GET" action="/contracts/company-agreement">
                                    <div class="mb-4">
                                        <label class="form-label fw-semibold">Select Company *</label>
                                        <select name="company_id" class="form-select form-select-lg" required>
                                            <option value="">-- Choose a company --</option>
                                            {% for company in companies %}
                                            <option value="{{ company.id }}">{{ company.name }} - {{ company.contact_person }}</option>
                                            {% endfor %}
                                        </select>
                                    </div>

                                    <button type="submit" class="btn btn-primary btn-lg w-100">
                                        <i class="bi bi-file-text me-2"></i>Generate & Download Company Agreement
                                    </button>
                                </form>
                            </div>
                        </div>
                    </div>
                    <!-- Vendor Contract Tab -->
                    <div class="tab-pane fade" id="vendor-tab">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0"><i class="bi bi-person-check me-2"></i>Owner/Vendor Agreement</h6>
                            </div>
                            <div class="card-body">
                                <p class="text-muted">Select a vehicle owner/investor to generate their agreement. The agreement will include payment terms, responsibilities, and vehicle handover conditions.</p>

                                <form method="GET" action="/contracts/vendor-agreement">
                                    <div class="mb-4">
                                        <label class="form-label fw-semibold">Select Owner/Vendor *</label>
                                        <select name="investor_id" class="form-select form-select-lg" required>
                                            <option value="">-- Choose an owner/vendor --</option>
                                            {% for investor in investors %}
                                            <option value="{{ investor.id }}">{{ investor.name }} - CNIC: {{ investor.cnic }}</option>
                                            {% endfor %}
                                        </select>
                                    </div>

                                    <button type="submit" class="btn btn-primary btn-lg w-100">
                                        <i class="bi bi-file-text me-2"></i>Generate & Download Owner Agreement
                                    </button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
                <!-- Instructions Card -->
                <div class="card mt-4">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="bi bi-info-circle me-2"></i>How to Use</h6>
                    </div>
                    <div class="card-body">
                        <ol class="mb-0">
                            <li class="mb-2">Select either <strong>Company Contract</strong> or <strong>Owner/Vendor Contract</strong> tab</li>
                            <li class="mb-2">Choose the company or owner from the dropdown menu</li>
                            <li class="mb-2">Click the <strong>Generate & Download</strong> button</li>
                            <li class="mb-2">A new window will open with the complete agreement</li>
                            <li class="mb-2">Click <strong>Print / Download PDF</strong> to save or print the document</li>
                            <li>Use your browser's "Save as PDF" option in the print dialog to download</li>
                        </ol>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

COMPANY_AGREEMENT_TEMPLATE = r'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page { size: A4; margin: 0.5in; }
        body { font-family: 'Times New Roman', serif; line-height: 1.6; color: #000; padding: 10px; }
        
        /* Page 1 Header Gap (16 lines approx) */
        .header-space { height: 350px; } 

        .title { text-align: center; font-weight: bold; font-size: 18pt; text-decoration: underline; margin-bottom: 30px; text-transform: uppercase; }
        .content { text-align: justify; font-size: 12pt; margin-bottom: 15px; }
        .bold { font-weight: bold; }
        .underline-box { border-bottom: 1px solid black; display: inline-block; min-width: 80px; text-align: center; font-weight: bold; }
        
        /* Definitions Table Spacing */
        .def-table { width: 100%; border-collapse: collapse; margin-top: 10px; margin-left: 20px; }
        .def-table td { vertical-align: top; padding-bottom: 15px; font-size: 12pt; }
        
        @media print { .no-print { display: none; } }
    </style>
</head>
<body>
    <div class="no-print" style="text-align: right; padding: 10px;">
        <button onclick="window.print()" style="padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer;">Print Now</button>
    </div>

    <div class="header-space"></div>
    <div class="title">LEASE AGREEMENT</div>

    <div class="content">
        This agreement is entered into at Karachi, Pakistan on this the 
        <span class="underline-box">&nbsp;{{ day_str }}&nbsp;</span> day of 
        <span class="underline-box">&nbsp;{{ month_str }}&nbsp;</span> 
        <span class="underline-box">&nbsp;{{ year_str }}&nbsp;</span>
    </div>

    <div class="content">
        <p class="bold">By and Between</p>
        <p>
            <span class="bold">AA Transportation</span> through its Proprietor <span class="bold">Ms. Shahzreah Husain</span>, 
            holding CNIC NO. <span class="bold">42301-9857415-2</span>, having its Corporate Office Address: 
            6-C, Mezzanine 2, South Park Avenue, Phase II Extension, DHA, Karachi, 
            (hereinafter referred to as the <span class="bold">“VENDOR”</span>) 
            which expression wherever the context so permit shall mean and include his heirs, successors, 
            administrators, legal representative, executors and assigns of the <span class="bold">FIRST PART</span>;
        </p>
    </div>

    <div class="content"><p class="bold">And</p></div>

    <div class="content">
        <span class="underline-box" style="min-width: 300px;">&nbsp;{{ company['name'] }}&nbsp;</span>, 
        through its manager <span class="underline-box" style="min-width: 150px;">&nbsp;{{ company['contact_person'] }}&nbsp;</span> 
        holding CNIC NO. <span class="underline-box" style="min-width: 150px;">&nbsp;{{ company['manager_cnic'] }}&nbsp;</span> 
        a company incorporated in Pakistan and having its Corporate Office: 
        <span class="underline-box" style="min-width: 250px;">&nbsp;{{ company['address'] }}&nbsp;</span> Karachi 
        (hereinafter referred to as the <span class="bold">“COMPANY”</span>) 
        which expression wherever the context so permit shall mean and include his heirs, successors, 
        administrators, legal representative, executors and assigns of the <span class="bold">SECOND PART</span>.
    </div>

    <div class="content">
        The Vendor and the Company may be referred to individually as <span class="bold">“Party”</span> and/or collectively as <span class="bold">“Parties”</span>.
    </div>

    <div class="content">
        <span class="bold">WHEREAS</span> the Vendor is the legal custodian of the Motor Vehicle and is authorized to rent / lease the Motor Vehicle to the Company;
    </div>

    <div style="page-break-before: always; height: 30px;"></div>

    <div class="content">
        <p>AND WHEREAS the Company is desirous to lease a particular Motor Vehicle from the Vendor at such rate and conditions as specified in this Agreement;</p>
        <p>AND WHEREAS the Vendor hereby agrees to lease the said Motor Vehicle to the Company on such consideration and terms & conditions as stated herein.</p>
    </div>

    <div class="content" style="margin-top: 30px;">
        <p><span class="bold">Article 1:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Definitions</span><br>
        In this Agreement, unless the context requires otherwise, the following terms and expressions shall have the meanings assigned to them:</p>
    </div>

    <table class="def-table">
        <tr>
            <td style="width: 28%;" class="bold">“Agreement”</td>
            <td style="width: 12%;">means</td>
            <td>this Agreement for lease / rent of the Motor Vehicle by the Vendor to the Company;</td>
        </tr>
        <tr>
            <td class="bold">"Effective Date"</td>
            <td>means</td>
            <td><span class="underline-box" style="min-width: 180px;">&nbsp;{{ company['effective_date'] or '__________' }}&nbsp;</span>;</td>
        </tr>
        <tr>
            <td class="bold">“Motor Vehicle”</td>
            <td>means</td>
            <td>the motor car vehicle bearing Registration No. <span class="underline-box"><b>&nbsp;{{ vehicle['reg_no'] if vehicle else '__________' }}&nbsp;</b></span>, 
                Model <span class="underline-box"><b>&nbsp;{{ vehicle['model'] if vehicle else '__________' }}&nbsp;</b></span> having Engine/Chassis No. 
                <span class="underline-box"><b>&nbsp;{{ vehicle['engine_no'] if vehicle else '__________' }}&nbsp;</b></span>;</td>
        </tr>
        <tr>
            <td class="bold">"Period of Agreement"</td>
            <td>means</td>
            <td>the time period from the Effective Date until the Termination Date as provided under this Agreement;</td>
        </tr>
        <tr>
            <td class="bold">“Rental Amount”</td>
            <td>means</td>
            <td>the amount of <span class="bold">Rs. {{ company['payment_terms'] or '75,000/-' }} per month</span> payable by the Company to the Vendor for renting the Motor Vehicle;</td>
        </tr>
        <tr>
            <td class="bold">“Termination Date”</td>
            <td>means</td>
            <td><span class="underline-box" style="min-width: 180px;">&nbsp;{{ company['termination_date'] or '__________' }}&nbsp;</span>, the date on which this Agreement reaches its natural conclusion and the Motor Vehicle must be returned to the Vendor;</td>
        </tr>
        <tr>
            <td class="bold">“Territory”</td>
            <td>means</td>
            <td>the city of Karachi – Pakistan;</td>
        </tr>
        <tr>
            <td class="bold">“Third party”</td>
            <td>means</td>
            <td>any person/entity who is neither the Vendor nor the Company.</td>
        </tr>
    </table>

    <div class="content" style="margin-top: 40px;">
        <p><span class="bold">Article 2:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Permission to use the Motor Vehicle</span></p>
    </div>
    
    <div style="page-break-before: always; height: 50px;"></div>

    <div class="content">
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="width: 40px; vertical-align: top;">2.1</td>
                <td style="text-align: justify;">
                    Subject to the terms and conditions set forth in this Agreement, the Vendor hereby 
                    grants the Company permission along with necessary authority and rights to use the 
                    Motor Vehicle in a lawful and legal manner.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">2.2</td>
                <td style="text-align: justify;">
                    The permission granted by the Vendor to the Company is subject to the Company 
                    ensuring any person(s) driving the Motor Vehicle shall hold a valid driver’s license 
                    which is legally acceptable in the Territory.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">2.3</td>
                <td style="text-align: justify;">
                    It shall at all times be the Vendor’s sole responsibility during the Period of Agreement 
                    to ensure that all comprehensive insurance policy, tax, duty and/or any other legal 
                    requirements of the Motor Vehicle are strictly complied at all times, and where 
                    necessary at the Vendor’s expense.
                </td>
            </tr>
        </table>
    </div>

    <div class="content" style="margin-top: 30px;">
        <p><span class="bold">Article 3:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Rights and Obligations of Parties</span></p>
        
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="width: 40px; vertical-align: top;">3.1</td>
                <td style="text-align: justify;">
                    The Company shall ensure the Motor Vehicle is at all times maintained to the highest 
                    standards and that the Motor Vehicle is periodically maintained and serviced at a 
                    reputable workshop at the Vendor’s expense, so the Motor Vehicle remains in top 
                    condition and roadworthy.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">3.2</td>
                <td style="text-align: justify;">
                    The Company is not entitled to transfer or delegate any rights and/or obligations under 
                    this Agreement to any third party, and shall not be allowed to sub-lease or further rent 
                    the Motor Vehicle to any third party.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">3.3</td>
                <td style="text-align: justify;">
                    The Company shall ensure the Motor Vehicle is used in a lawful manner, and the 
                    Company shall be solely responsible for all usage of the Motor Vehicle, including but 
                    not limited to actions of all persons using the Motor Vehicle, throughout the Period of 
                    Agreement. The Company shall ensure the Motor Vehicle is not taken outside the 
                    Territory.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">3.4</td>
                <td style="text-align: justify;">
                    That if any person is misusing the Motor Vehicle in any manner whatsoever, including 
                    but not limited to carrying out any unlawful activity, being negligent or rash with the 
                    Motor Vehicle, or any other such activity, the Company shall be solely responsible for 
                    any repercussions arising from the same. The Company shall at all times keep the 
                    Vendor indemnified against any / all actions, claims, liabilities etc. arising from the 
                    Motor Vehicle, as well against the actions of any person(s) driving the Motor Vehicle 
                    including but not limited to accident, death, injury etc., for the duration of the Period 
                    of Agreement.
                </td>
            </tr>
        </table>
    </div>

    <div style="page-break-before: always; height: 50px;"></div>
    <div class="content">
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="width: 40px; vertical-align: top;">3.5</td>
                <td style="text-align: justify;">
                    The Company shall not undertake any activity or omit to undertake any activity which 
                    may be deemed by the Vendor to be detrimental or prejudicial to the Motor 
                    Vehicle; and the Company shall promptly comply with all the instructions and requests 
                    of the Vendor in that respect.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">3.6</td>
                <td style="text-align: justify;">
                    It shall be incumbent upon the Company to defend any / all legal, quasi-legal or any 
                    other proceeding(s) instituted against the Motor Vehicle for the duration of the Period 
                    of Agreement. The Company shall ensure the Motor Vehicle is properly represented 
                    and defended, and the legal counsel (where required) shall be decided with the consent 
                    of the Vendor, the costs / fees of which shall be borne by the Company.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">3.7</td>
                <td style="text-align: justify;">
                    The Company shall at all times for the Period of Agreement comply with any applicable 
                    law(s) and regulations applicable in the Territory relating to the running and operating 
                    of the Motor Vehicle and shall fully indemnify the Vendor against any and all claims, 
                    suits, liabilities, adjudications that may be incurred or arise as a result of the failure of 
                    the Company to comply with this clause or any other part of this Agreement, which 
                    indemnity shall include but not be limited to any and all losses, and/or damages 
                    sustained by the Vendor or the Motor Vehicle, whether foreseeable or not.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">3.8</td>
                <td style="text-align: justify;">
                    The Company shall be responsible for the Motor Vehicle, including all its parts and 
                    original license plates. Should any part of the Motor Vehicle be damaged, lost or stolen, 
                    the Company shall be responsible to replace the same with such brand new part, at 
                    their own cost. In the event the original license plates are lost, misplaced or stolen, the 
                    Company shall immediately carry out all necessary action as deemed prudent by the 
                    Vendor, including but not limited to filing necessary police complaints, applying for 
                    duplicate license plates etc. Moreover, the Company shall be liable to pay the Vendor 
                    the lost price difference in value of the Motor Vehicle (as may be assessed by an 
                    authorized dealer of the Motor Vehicle), due to not having original license plates, 
                    within twenty (20) days of getting the price assessment.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">3.9</td>
                <td style="text-align: justify;">
                    The Company shall upon the Vendor’s request, permit the Vendor (through any of 
                    their authorized agents) to enter and inspect the Motor Vehicle. In the event the 
                    Vendor is of the reasonable opinion the Motor Vehicle is being misused or is not being 
                    handled in accordance with proper care, the Vendor shall have the right to repossess 
                    the Motor Vehicle.
                </td>
            </tr>
        </table>
    </div>

    <div class="content" style="margin-top: 40px;">
        <p><span class="bold">Article 4:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Payments</span></p>
    </div>

    <div style="page-break-before: always; height: 50px;"></div>

    <div class="content">
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="width: 40px; vertical-align: top;">4.1</td>
                <td style="text-align: justify;">
                    The Company shall pay the Vendor a consideration of <span class="bold">Rs. {{ company['payment_terms'] or '75,000/-' }}</span> (Rupees Seventy 
                    Five Thousand Only) per month, being the Rental Amount of the Motor Vehicle.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">4.2</td>
                <td style="text-align: justify;">
                    The Company shall pay the Rental Amount on or before the 10th day of each 
                    (Gregorian) calendar month. In the event the Company does not make the Rental 
                    Amount payment by the 10th day of any given month in the Period of Agreement, the 
                    Vendor shall be entitled to immediately repossess the Motor Vehicle from the 
                    Company without giving any notice whatsoever.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">4.3</td>
                <td style="text-align: justify;">
                    Payment of the Rental Amount must be made each calendar month in full by the 
                    Company to the Vendor, irrespective of the usage or operation of the Motor Vehicle 
                    by the Company. Even if the Motor Vehicle is under repair or otherwise inoperative, 
                    the Company shall still be liable to make full and timely payment of the Rental Amount 
                    to the Vendor.
                </td>
            </tr>
        </table>
    </div>

    <div class="content" style="margin-top: 30px;">
        <p><span class="bold">Article 5:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Confidentiality</span></p>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="width: 40px; vertical-align: top;">5.1</td>
                <td style="text-align: justify;">
                    The Company shall at all times keep the terms and conditions of this Agreement 
                    confidential and shall not disclose the same to any third party.
                </td>
            </tr>
        </table>
    </div>

    <div class="content" style="margin-top: 30px;">
        <p><span class="bold">Article 6:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Term and Termination</span></p>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="width: 40px; vertical-align: top;">6.1</td>
                <td style="text-align: justify;">
                    This Agreement shall be deemed to have come into effect from the Effective Date 
                    until the Termination Date, i.e. for a period of eleven (11) months, after which, subject 
                    to fulfillment of all terms & conditions herein stated, it may be renewed by mutual 
                    consent of both Parties.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">6.2</td>
                <td style="text-align: justify;">
                    This Agreement may be terminated at any time by mutual written consent of both 
                    Parties. The Vendor may also terminate this Agreement effective immediately if the 
                    Company commits a breach of any of its obligations under this Agreement.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">6.3</td>
                <td style="text-align: justify;">
                    This Agreement may be terminated in the event of a force majeure, if such force majeure 
                    makes it impossible or highly unreasonable to continue with the terms stated in the 
                    Agreement for a continual period of fifteen (15) days, or unless the Parties agree 
                    otherwise by mutual consent. In event of a force majeure, the Party seeking the same 
                    shall inform the other Party in writing within three (3) days of the said force majeure 
                    occurring.
                </td>
            </tr>
        </table>
    </div>

    <div class="content" style="margin-top: 40px;">
        <p><span class="bold">Article 7:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Consequences of Termination</span></p>
    </div>

    <div style="page-break-before: always; height: 50px;"></div>

    <div class="content">
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="width: 40px; vertical-align: top;">7.1</td>
                <td style="text-align: justify;">
                    Upon termination of this Agreement for any reason whatsoever, the Company shall 
                    immediately stop using the Motor Vehicle and shall return the same to the Company.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">7.2</td>
                <td style="text-align: justify;">
                    Where any breach of condition or violation of this Agreement by the Company has 
                    occurred, the Company shall pay the Vendor such amount as may be stated in this 
                    Agreement. In the event such amount is not stated, the Vendor shall calculate the 
                    amount of loss / damage suffered and present the same in writing to the Company, 
                    and the Company shall immediately make such payment to the Vendor.
                </td>
            </tr>
        </table>
    </div>

    <div class="content" style="margin-top: 30px;">
        <p><span class="bold">Article 8:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Force Majeure</span></p>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="width: 40px; vertical-align: top;">8.1</td>
                <td style="text-align: justify;">
                    A "force majeure event" means an event that is beyond the reasonable control of, or 
                    unforeseeable or even if foreseeable but unavoidable by both Parties, or would 
                    unreasonably prevent, affect or delay the performance by either Party of its respective 
                    obligations hereunder.
                </td>
            </tr>
        </table>
    </div>

    <div class="content" style="margin-top: 30px;">
        <p><span class="bold">Article 9:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Indemnification</span></p>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="width: 40px; vertical-align: top;">9.1</td>
                <td style="text-align: justify;">
                    The Company agrees to defend, indemnify and hold harmless the Vendor, from any 
                    and all third party lawsuits, actions, claims, damages, liabilities, costs and expenses, 
                    including reasonable attorney’s fees, court costs and other legal expenses, through all 
                    levels of appeal arising out of or related to the Motor Vehicle.
                </td>
            </tr>
        </table>
    </div>

    <div class="content" style="margin-top: 30px;">
        <p><span class="bold">Article 10:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Representations and Warranties</span></p>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="width: 40px; vertical-align: top;">10.1</td>
                <td style="text-align: justify;">
                    Representations and Warranties. Each Party makes the following representations and 
                    warranties that:
                </td>
            </tr>
        </table>
        
        <table style="width: 100%; border-collapse: collapse; margin-top: 10px; margin-left: 40px;">
            <tr>
                <td style="width: 30px; vertical-align: top;">i)</td>
                <td style="text-align: justify; padding-right: 40px;">
                    The Party has the full legal right, title, interest, power and authority to enter into 
                    this Agreement and to perform its legal obligations hereunder, and has taken all 
                    necessary action to authorize the execution and delivery of this Agreement and 
                    the performance of its obligations hereunder. This Agreement has been duly 
                    executed and delivered on behalf of the Party, and constitutes a legal, valid, 
                    binding obligation, enforceable against the Party in accordance with its terms; 
                    and
                </td>
            </tr>
            <tr style="height: 10px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">ii)</td>
                <td style="text-align: justify; padding-right: 40px;">
                    To the best of the Party's knowledge and belief, the execution and delivery of 
                    this Agreement and the performance of the Party's obligations hereunder do 
                    not conflict with or violate any requirement of applicable laws or regulations 
                    and do not conflict with, or constitute a default under, any contractual 
                    obligation of the Party.
                </td>
            </tr>
        </table>
    </div>
    
    <div style="page-break-before: always; height: 50px;"></div>

    <div class="content">
        <p><span class="bold">Article 11:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Miscellaneous Provisions</span></p>
        
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="width: 40px; vertical-align: top;">11.1</td>
                <td style="text-align: justify;">
                    This Agreement shall be executed in (two) counterparts, one of each which shall both 
                    be deemed to be an original and all of which together shall be deemed to be one and 
                    the same agreement.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">11.2</td>
                <td style="text-align: justify;">
                    The headings to the several sections hereof are not part of this Agreement, but are 
                    included merely for convenience of reference and shall not affect its meaning or 
                    interpretation.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">11.3</td>
                <td style="text-align: justify;">
                    All notices, hereunder shall be in writing and shall be hand delivered, or sent by express 
                    delivery service with confirmation of receipt, or sent by registered or certified mail, 
                    return receipt requested, postage prepaid, in each case to the respective address as 
                    indicated at the head of this Agreement. Any such notice shall be deemed to have been 
                    given when received. Should either party change its address it shall give the other party 
                    written notice.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">11.4</td>
                <td style="text-align: justify;">
                    This Agreement shall not, and neither shall in any manner be deemed to constitute a 
                    partnership between the Parties; nor shall the Company have any right or authority to 
                    assume, create or incur any liability or obligation of any kind against, in the name of, 
                    or on behalf of, the Vendor.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">11.5</td>
                <td style="text-align: justify;">
                    All words, phrases and terms, unless explicitly defined in this Agreement shall have 
                    their ordinary meaning in common commercial usage. All singular forms as used in this 
                    Agreement shall be understood to represent the plural form with equal force and all 
                    plural forms as used in this Agreement shall be understood to represent the singular 
                    form with equal force.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">11.6</td>
                <td style="text-align: justify;">
                    Any amendments, supplements or modifications to this Agreement shall only be 
                    binding when executed in writing and duly signed by both Parties.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">11.7</td>
                <td style="text-align: justify;">
                    Any / all costs arising out of this Agreement, including but not limited to stamp duty, 
                    registration fees etc. shall be borne by the Company.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">11.8</td>
                <td style="text-align: justify;">
                    In the event that any provision of this Agreement becomes or is declared by a court of 
                    competent jurisdiction or for any other reason to be illegal, unenforceable, invalid or 
                    void, this Agreement shall continue in full force and effect to the fullest extent 
                    permitted by law without said provision, and the Parties shall amend the Agreement to 
                    the extent feasible to lawfully include the substance of the excluded term to, as fully as 
                    possible, realize the intent of the Parties and their commercial bargain.
                </td>
            </tr>
        </table>
    </div>

    <div class="content" style="margin-top: 40px;">
        <p><span class="bold">Article 12:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Governing Law and Jurisdiction</span></p>
    </div>

    <div style="page-break-before: always; height: 50px;"></div>

    <div class="content">
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="width: 50px; vertical-align: top;">12.1</td>
                <td style="text-align: justify;">
                    This Agreement shall be governed by and construed in accordance with the laws of the Islamic Republic of Pakistan.
                </td>
            </tr>
            <tr style="height: 15px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">12.2</td>
                <td style="text-align: justify;">
                    The competent Courts of law at Karachi– Pakistan shall have exclusive jurisdiction to settle any claims and/or dispute arising out of this Agreement or any acts done in pursuance thereof, regardless of the location of place of business or the place where work is to be performed.
                </td>
            </tr>
        </table>
    </div>

    <div class="content" style="margin-top: 40px;">
        <p class="bold">WITNESSES:</p>
        <p>IN WITNESS THEREOF, this Agreement is signed by duly authorized representatives of the Parties at Karachi - Pakistan on the date above written.</p>
    </div>

    <div style="margin-top: 80px;">
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="width: 50%; text-align: left;">
                    __________________________<br>
                    <span class="bold">Vendor</span>
                </td>
                <td style="width: 50%; text-align: right;">
                    __________________________<br>
                    <span class="bold">Company</span>
                </td>
            </tr>
        </table>
    </div>

    <div style="margin-top: 60px;">
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="width: 50%; text-align: left;"><span class="bold">Witnesses:</span></td>
                <td style="width: 50%; text-align: left;"><span class="bold">Witnesses:</span></td>
            </tr>
            <tr style="height: 40px;"><td></td><td></td></tr>
            <tr>
                <td style="vertical-align: top;">
                    1. __________________________<br><br>
                    Name: <span class="underline-box" style="min-width: 180px;">&nbsp;</span><br><br>
                    CNIC: <span class="underline-box" style="min-width: 180px;">&nbsp;</span><br><br>
                    Date: <span class="underline-box" style="min-width: 180px;">&nbsp;</span>
                </td>
                <td style="vertical-align: top;">
                    2. __________________________<br><br>
                    Name: <span class="underline-box" style="min-width: 180px;">&nbsp;</span><br><br>
                    CNIC: <span class="underline-box" style="min-width: 180px;">&nbsp;</span><br><br>
                    Date: <span class="underline-box" style="min-width: 180px;">&nbsp;</span>
                </td>
            </tr>
        </table>
    </div>
</body>
</html>
'''
VENDOR_AGREEMENT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <style>
        @page { 
            size: A4; 
            margin: 1.5cm; 
        }
        body { 
            font-family: 'Times New Roman', serif; 
            line-height: 1.6; 
            padding: 20px; 
            margin-top: 220px; /* Exact 10 lines gap for stamp paper */
            color: #000;
        }
        .header { text-align: center; font-weight: bold; font-size: 20pt; text-decoration: underline; margin-bottom: 30px; }
        .text { text-align: justify; font-size: 12pt; margin-bottom: 15px; }
        .clause { margin-bottom: 15px; text-align: justify; font-size: 12pt; }
        .underline { font-weight: bold; border-bottom: 1px solid #000; padding: 0 5px; }
        .page-break { page-break-before: always; padding-top: 50px; }
        
        .signature-table { width: 100%; margin-top: 50px; }
        .signature-table td { width: 50%; vertical-align: top; }
        
        @media print { .no-print { display: none; } }
    </style>
</head>
<body>
    <div class="no-print" style="text-align: center; margin-bottom: 20px;">
        <button onclick="window.print()" style="padding: 10px 20px; cursor: pointer;">Print PDF</button>
    </div>

    <div class="header">Rent Agreement</div>

    <div class="text">
        This agreement is entered into at Karachi, Pakistan on this the <span class="underline">{{ day_str }}</span> day of <span class="underline">{{ month_str }}</span> <span class="underline">{{ year_str }}</span>
    </div>

    <div style="text-align:center; font-weight:bold; margin:15px 0;">By and Between</div>

    <div class="text">
        <strong>AA Transportation</strong> through its Director <strong>Ms. Shahzreah Husain</strong>, holding CNIC NO. 42301-9857415-2, having its Corporate Office Address: Office 213, Office Wing, Park Towers, Block-5, Clifton, Karachi, (hereinafter referred to as the “LESSEE”) which expression wherever the context so permit shall mean and include his heirs, successors, administrators, legal representative, executors and assigns of the FIRST PART;
    </div>

    <div style="text-align:center; font-weight:bold; margin:15px 0;">And</div>

    <div class="text">
        <strong>{{ investor.name }}</strong>, s/o <strong>{{ investor.father_name or '________________' }}</strong> holding CNIC NO. <strong>{{ investor.cnic or '________________' }}</strong> resident of <strong>{{ investor.address or '________________' }}</strong> Karachi (hereinafter referred to as the “LESSOR”) which expression wherever the context so permit shall mean and include his heirs, successors, administrators, legal representative, executors and assigns of the SECOND PART.
    </div>

    <div class="text">The Lessor and the Lessee may be referred to individually as “Party” and/or collectively as “Parties”.</div>

    <div class="text">
        <strong>Whereas</strong> the Lessor is the lawful owner of Motor Vehicle having Model No. <span class="underline">{{ investor.car_model or '________' }}</span>; Colour <span class="underline">{{ investor.color or '________' }}</span>; Engine <span class="underline">{{ investor.engine_no or '________' }}</span> / Chassis No. <span class="underline">{{ investor.chassis_no or '________' }}</span>; Registration No. <span class="underline">{{ investor.reg_no or '________' }}</span>, Meter reading <span class="underline">{{ investor.meter_reading or '________' }}</span> KM (at the time of this Agreement) being <span class="underline">{{ investor.color or '________' }}</span> Colour, (here in after referred to as the “VEHICLE”);
    </div>

    <div class="text">And whereas the Lessor is desirous of leasing / renting the Vehicle to the Lessee;</div>
    <div class="text">And whereas the Lessee is desirous of hiring the Vehicle on lease / rent from the Lessor on such terms and conditions as stated herein.</div>

    <div class="clause">1. The Lessor hereby undertakes that he is the complete sole and lawful owner of the Vehicle.</div>
    <div class="clause">2. That the Lessor hereby undertakes the said Vehicle was lawfully purchased by him on <span class="underline">{{ investor.purchase_date or '___________' }}</span> and that he holds all requisite registration and document titles of the Vehicle.</div>
    <div class="clause">3. That the Lessor hereby undertakes no third person / party has any lien or claim on the Vehicle, nor is there any mortgage or other charge on the Vehicle.</div>
    <div class="clause">4. That the Lessor hereby undertakes that all proper comprehensive insurance has been purchased for the duration period of this Agreement, and that Trakker Security has been installed and paid-up.</div>
    <div class="clause">5. That the lease / rent amount of the Vehicle shall be <strong>Rs. {{ investor.monthly_rent or '_______' }}/-</strong> (Rupees <span class="underline">________________</span> Only) per (Gregorian) calendar month, which shall be payable by or before the 20th day of each month by the Lessee to the Lessor.</div>
    <div class="clause">6. That delivery of the Vehicle along with two (2) sets of keys have been handed over by the Lessor to the Lessee at the time of signing this Agreement.</div>
    <div class="clause">7. That the Lessee shall be permitted to use the Vehicle in any manner which is not in derogation of law. The Lessee is permitted to further rent / lease the Vehicle to any third person or persons at such rates / charges as the Lessee may deem appropriate, and the Lessor shall have no claim towards the same. The lease / rent amount stated in Clause 2 of this Agreement is full and final payment the Lessee is obligated to pay the Lessor.</div>
    <div class="clause">8. The in the event any car repair for the Vehicle for any reason whatsoever is required, the Lessee may inform the Lessor of the same, and all costs involved shall be paid by the Lessor. Payments for the repairs shall be made by the Lessor, but shall be made promptly so as to ensure the Vehicle is not restricted from being used by the Lessee or any other person permitted by the Lessee to use the Vehicle. All formalities, if any, as may be required for usage of insurance for repairs or any other work on the Vehicle shall be the sole responsibility of the Lessor, who shall ensure the same is carried out with proper diligence and in a timely manner in order not to disrupt the Lessee’s (or any third party’s) use of the Vehicle.</div>
    <div class="clause">9. That payment of all taxes / fees etc. on the Vehicle shall remain the sole responsibility and liability of the Lessor.</div>
    <div class="clause">10. That the validity of this Agreement is eleven (11) months, commencing on <span class="underline">{{ day_str }} {{ month_str }} 2022</span> and ending on <span class="underline">__________ 2023</span>. The Parties may by mutual consent in writing extend this Agreement.</div>
    <div class="clause">11. The Lessee shall keep the Vehicle in a good working condition and shall make their best endeavours to ensure it remains roadworthy.</div>

    <div class="page-break"></div>

    <div class="clause">12. That the Lessor shall not interfere with Lessee’s use of the Vehicle for the duration period of this Agreement.</div>
    <div class="clause">13. That the Lessor hereby indemnifies the Lessee against any / all claims by any third party against the Vehicle. The Lessor further agrees to defend, indemnify and hold harmless the Lessee, from any and all third party lawsuits, actions, claims, damages, liabilities, costs and expenses, including reasonable attorney’s fees, court costs and other legal expenses, through all levels of appeal arising out of or related to the Vehicle.</div>
    <div class="clause">14. That this Agreement may be terminated if:</div>
    <div style="margin-left: 40px;">
        <div class="clause">i. Either Party wishes to discontinue with their obligations under this Agreement, in which case such Party shall give the other Party thirty (30) days’ notice, after which this Agreement will automatically terminate. This will not absolve either of the Parties from their obligations under this Agreement until the thirty (30) day period is reached;</div>
        <div class="clause">ii. Either Party breaches any covenant of this Agreement, in which the case the other (non-breaching) Party shall have the option to continue or immediately terminate this Agreement;</div>
        <div class="clause">iii. If both Parties by mutual consent agree to terminate this Agreement.</div>
    </div>
    <div class="clause">15. That in the event of a force majeure (act of God beyond the control of either Party), if such force majeure makes it impossible or highly unreasonable to continue with the terms stated in the Agreement for a continual period of fifteen (15) days, or unless the Parties agree otherwise by mutual consent this Agreement may be terminated. In event of a force majeure, the Party seeking the same shall inform the other Party in writing within three (3) days of the said force majeure occurring.</div>
    <div class="clause">16. That the Lessor shall not sell the Vehicle to any third person during the Agreement period.</div>
    <div class="clause">17. That this Agreement shall be executed in (two) counterparts, one of each which shall both be deemed to be an original and all of which together shall be deemed to be one and the same agreement.</div>
    <div class="clause">18. That Agreement shall not, and neither shall in any manner be deemed to constitute a partnership between the Parties; nor shall either Party have any right or authority to assume, create or incur any liability or obligation of any kind against, in the name of, or on behalf of, the other Party.</div>
    <div class="clause">19. That each Party shall be responsible for payment of their own income tax etc. arising from the outcome of this Agreement.</div>
    <div class="clause">20. That words, phrases and terms, unless explicitly defined in this Agreement shall have their ordinary meaning in common commercial usage. All singular forms as used in this Agreement shall be understood to represent the plural form with equal force and all plural forms as used in this Agreement shall be understood to represent the singular form with equal force.</div>
    
    <div class="clause">21. That amendments, supplements or modifications to this Agreement shall only be binding when executed in writing and duly signed by both Parties.</div>
    <div class="clause">22. That Agreement shall be governed by and construed in accordance with the laws of the Islamic Republic of Pakistan, and the competent Courts of law at Karachi – Pakistan shall have jurisdiction over the matter.</div>

    <div class="text" style="margin-top: 30px; font-weight: bold;">
        IN WITNESS THEREOF, this Agreement is signed by duly authorized representatives of the Parties at Karachi - Pakistan on the date above written.
    </div>

    <table class="signature-table">
        <tr>
            <td>
                _________________<br>
                <strong>Lessee</strong><br><br>
                <strong>Witnesses:</strong><br><br>
                1. _________________<br>
                Name:<br>
                CNIC:<br>
                Date:
            </td>
            <td>
                _________________<br>
                <strong>Lessor</strong><br><br>
                <strong>Witnesses:</strong><br><br>
                2. _________________<br>
                Name:<br>
                CNIC:<br>
                Date:
            </td>
        </tr>
    </table>
</body>
</html>
'''
INVESTOR_INVOICE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        @page { size: A4; margin: 0; }
        body { font-family: 'Inter', sans-serif; margin: 0; padding: 0; color: #1a1a1a; }
        .invoice-container { padding: 40px; }
        .accent-bar { height: 8px; background: #1e3c72; width: 100%; }
        
        .header { display: flex; justify-content: space-between; border-bottom: 2px solid #eee; padding-bottom: 20px; margin-bottom: 30px; }
        .company-info h1 { margin: 0; color: #1e3c72; font-size: 22pt; text-transform: uppercase; }
        .company-info p { margin: 3px 0; font-size: 9pt; color: #555; }
        
        .invoice-meta { text-align: right; }
        .invoice-meta h2 { margin: 0; font-size: 24pt; color: #ddd; letter-spacing: 2px; }
        .meta-box { display: inline-block; background: #f8f9fa; padding: 10px; border-radius: 5px; margin-top: 10px; text-align: left; border: 1px solid #eee; }
        .meta-box div { font-size: 9pt; margin-bottom: 2px; }

        .bill-to { margin-bottom: 30px; }
        .bill-to-label { font-size: 9pt; font-weight: bold; color: #1e3c72; text-transform: uppercase; margin-bottom: 5px; }
        .bill-to-name { font-size: 13pt; font-weight: bold; border-left: 4px solid #1e3c72; padding-left: 15px; }

        .main-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        .main-table th { background: #1e3c72; color: white; padding: 12px 8px; font-size: 8.5pt; text-transform: uppercase; text-align: center; }
        .main-table td { padding: 12px 8px; border-bottom: 1px solid #eee; font-size: 9pt; text-align: center; }
        .main-table .desc-col { text-align: left; }
        
        .totals-section { float: right; margin-top: 25px; width: 340px; }
        .totals-table { width: 100%; border-collapse: collapse; border: 1px solid #eee; }
        .totals-table td { padding: 10px; font-size: 10pt; }
        .grand-total { background: #1e3c72; color: white; font-weight: bold; font-size: 11pt !important; }

        .footer { margin-top: 80px; text-align: center; font-size: 8pt; color: #888; border-top: 1px solid #eee; padding-top: 15px; }
        @media print { .no-print { display: none; } }
    </style>
</head>
<body>
    <div class="accent-bar"></div>
    <div class="no-print" style="text-align: center; padding: 15px; background: #f4f4f4;">
        <button onclick="window.print()" style="padding: 10px 20px; background: #1e3c72; color: white; border: none; cursor: pointer; border-radius: 4px; font-weight: bold;">PRINT INVESTOR INVOICE</button>
    </div>

    <div class="invoice-container">
        <div class="header">
            <div class="company-info">
                <h1>AA Transportation</h1>
                <p>Office # 118, 1st Floor, Office Wing, Park Towers,<br>Block 5, Clifton, Karachi. | Phone: 021-35290310<br><strong>NTN: 3006294-2</strong></p>
            </div>
            <div class="invoice-meta">
                <h2>INVESTOR INVOICE</h2>
                <div class="meta-box">
                    <div><strong>Inv-ID:</strong> AA-INV-{{ investor.id + 100 }}</div>
                    <div><strong>Date:</strong> {{ current_date }}</div>
                    <div><strong>Type:</strong> Investment Return</div>
                </div>
            </div>
        </div>

        <div class="bill-to">
            <div class="bill-to-label">Investor Details:</div>
            <div class="bill-to-name">{{ investor.name }}</div>
            <div style="font-size: 9pt; color: #666; padding-left: 20px; margin-top: 5px;">{{ investor.address or 'Karachi, Pakistan' }}</div>
        </div>

        <table class="main-table">
            <thead>
                <tr>
                    <th>S.No</th>
                    <th style="width: 20%;">Period</th>
                    <th>Vehicle</th>
                    <th>Model</th>
                    <th>Registration</th>
                    <th>Duration</th>
                    <th>Monthly Profit</th>
                    <th style="text-align: right;">Total Return</th>
                </tr>
            </thead>
            <tbody>
                {% for v in vehicles %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td style="font-size: 8pt;">{{ start_date }} - {{ end_date }}</td>
                    <td class="desc-col"><strong>{{ v.company_name or 'Honda' }}</strong></td>
                    <td>{{ v.car_model }}</td>
                    <td><span style="background: #f0f0f0; padding: 2px 5px; border-radius: 3px; font-family: monospace;">{{ v.reg_no }}</span></td>
                    <td>30 Days</td>
                    <td>{{ "{:,.0f}".format(v.monthly_rent) }}</td>
                    <td style="text-align: right; font-weight: 600;">{{ "{:,.0f}".format(v.monthly_rent) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="totals-section">
            <table class="totals-table">
                <tr>
                    <td>Gross Profit Share</td>
                    <td style="text-align: right;">{{ "{:,.0f}".format(total_rent) }}</td>
                </tr>
                <tr class="grand-total">
                    <td>NET PAYABLE TO INVESTOR</td>
                    <td style="text-align: right;">PKR {{ "{:,.0f}".format(total_rent) }}</td>
                </tr>
            </table>
        </div>

        <div style="clear: both;"></div>
        
        <div class="footer">
            <p>This is a computer-generated statement for investment returns. For any queries, contact accounts at 021-35290310.<br>
            <strong>AA Transportation</strong> - Partnering in Progress.</p>
        </div>
    </div>
</body>
</html>
'''
COMPANY_INVOICE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        @page { size: A4; margin: 0; }
        body { font-family: 'Inter', sans-serif; margin: 0; padding: 0; color: #1a1a1a; }
        .invoice-container { padding: 40px; }
        .accent-bar { height: 8px; background: #0d6efd; width: 100%; }
        
        .header { display: flex; justify-content: space-between; border-bottom: 2px solid #eee; padding-bottom: 20px; margin-bottom: 30px; }
        .company-info h1 { margin: 0; color: #0d6efd; font-size: 22pt; text-transform: uppercase; }
        .company-info p { margin: 3px 0; font-size: 9pt; color: #555; }
        
        .invoice-meta { text-align: right; }
        .invoice-meta h2 { margin: 0; font-size: 28pt; color: #ddd; }
        .meta-box { display: inline-block; background: #f8f9fa; padding: 10px; border-radius: 5px; margin-top: 10px; text-align: left; border: 1px solid #eee; }
        .meta-box div { font-size: 9pt; margin-bottom: 2px; }

        .bill-to { margin-bottom: 30px; }
        .bill-to-label { font-size: 9pt; font-weight: bold; color: #0d6efd; text-transform: uppercase; margin-bottom: 5px; }
        .bill-to-name { font-size: 13pt; font-weight: bold; border-left: 4px solid #0d6efd; padding-left: 15px; }

        .main-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        .main-table th { background: #0d6efd; color: white; padding: 12px 8px; font-size: 8.5pt; text-transform: uppercase; text-align: center; }
        .main-table td { padding: 12px 8px; border-bottom: 1px solid #eee; font-size: 9pt; text-align: center; }
        .main-table .desc-col { text-align: left; }
        
        .totals-section { float: right; margin-top: 25px; width: 320px; }
        .totals-table { width: 100%; border-collapse: collapse; border: 1px solid #eee; }
        .totals-table td { padding: 10px; font-size: 10pt; }
        .grand-total { background: #0d6efd; color: white; font-weight: bold; font-size: 11pt !important; }

        .footer { margin-top: 80px; text-align: center; font-size: 8pt; color: #888; border-top: 1px solid #eee; padding-top: 15px; }
        @media print { .no-print { display: none; } }
    </style>
</head>
<body>
    <div class="accent-bar"></div>
    <div class="no-print" style="text-align: center; padding: 15px; background: #f4f4f4;">
        <button onclick="window.print()" style="padding: 10px 20px; background: #0d6efd; color: white; border: none; cursor: pointer; border-radius: 4px; font-weight: bold;">PRINT COMPANY INVOICE</button>
    </div>

    <div class="invoice-container">
        <div class="header">
            <div class="company-info">
                <h1>AA Transportation</h1>
                <p>Office # 118, 1st Floor, Office Wing, Park Towers,<br>Block 5, Clifton, Karachi. | Phone: 021-35290310<br><strong>NTN: 3006294-2</strong></p>
            </div>
            <div class="invoice-meta">
                <h2>INVOICE</h2>
                <div class="meta-box">
                    <div><strong>Invoice #:</strong> AA-CORP-{{ company.id + 100 }}</div>
                    <div><strong>Date:</strong> {{ current_date }}</div>
                    <div><strong>Status:</strong> Generated</div>
                </div>
            </div>
        </div>

        <div class="bill-to">
            <div class="bill-to-label">Bill To (Company):</div>
            <div class="bill-to-name">{{ company.name }}</div>
            <div style="font-size: 9pt; color: #666; padding-left: 20px; margin-top: 5px;">{{ company.address or 'Karachi, Pakistan' }}</div>
        </div>

        <table class="main-table">
            <thead>
                <tr>
                    <th>S.No</th>
                    <th style="width: 20%;">Billing Period</th>
                    <th>Make</th>
                    <th>Model</th>
                    <th>Registration</th>
                    <th>Rent Type</th>
                    <th style="text-align: right;">Amount</th>
                </tr>
            </thead>
            <tbody>
                {% for v in vehicles %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td style="font-size: 8pt;">{{ start_date }} - {{ end_date }}</td>
                    <td class="desc-col"><strong>{{ v.make }}</strong></td>
                    <td>{{ v.variant }}</td>
                    <td><span style="background: #f0f0f0; padding: 2px 5px; border-radius: 3px; font-family: monospace;">{{ v.reg }}</span></td>
                    <td>Monthly Rental</td>
                    <td style="text-align: right; font-weight: 600;">{{ "{:,.0f}".format(v.monthly_rent_from_company) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="totals-section">
            <table class="totals-table">
                <tr>
                    <td>Gross Total</td>
                    <td style="text-align: right;">{{ "{:,.0f}".format(total_revenue) }}</td>
                </tr>
                <tr class="grand-total">
                    <td>NET PAYABLE (PKR)</td>
                    <td style="text-align: right;">{{ "{:,.0f}".format(total_revenue) }}</td>
                </tr>
            </table>
        </div>

        <div style="clear: both;"></div>
        
        <div class="footer">
            <p>Computer generated corporate invoice. Please make payments in favor of <strong>AA Transportation</strong>.<br>
            Thank you for your business!</p>
        </div>
    </div>
</body>
</html>
'''

# ================ DATABASE SETUP ================
def init_db():
    """Initialize database with AA Transportation schema"""
    print("Initializing AA Transportation database...")

    # Remove old database if exists
    if os.path.exists(DB):
        try:
            os.remove(DB)
            print("Removed old database file")
        except:
            pass

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
                   CREATE TABLE users
                   (
                       id         INTEGER PRIMARY KEY AUTOINCREMENT,
                       username   TEXT UNIQUE NOT NULL,
                       password   TEXT        NOT NULL,
                       role       TEXT        NOT NULL,
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )''')

    # Create investors table (owners who provide vehicles)
    cursor.execute('''
                   CREATE TABLE investors
                   (
                       id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                       name                 TEXT NOT NULL,
                       father_name          TEXT,
                       email                TEXT,
                       phone                TEXT,
                       address              TEXT,
                       cnic                 TEXT,
                       agreement_start      TEXT,
                       agreement_end        TEXT,
                       witness_1_name       TEXT,
                       witness_1_cnic       TEXT,
                       witness_2_name       TEXT,
                       witness_2_cnic       TEXT,
                       bank_details         TEXT,
                       monthly_payment_rate REAL      DEFAULT 75000.0,
                       status               TEXT      DEFAULT 'Active',
                       created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )''')

    # Create companies table (companies we rent to)
    cursor.execute('''
                   CREATE TABLE companies
                   (
                       id              INTEGER PRIMARY KEY AUTOINCREMENT,
                       name            TEXT NOT NULL,
                       contact_person  TEXT,
                       manager_cnic    TEXT,
                       email           TEXT,
                       phone           TEXT,
                       address         TEXT,
                       billing_address TEXT,
                       effective_date TEXT,
                       termination_date TEXT,
                       witness_1_name TEXT,
                       witness_1_cnic TEXT,
                       witness_2_name TEXT,
                       witness_2_cnic TEXT,
                       ntn             TEXT,
                       payment_terms   TEXT      DEFAULT 'Net 30',
                       status          TEXT      DEFAULT 'Active',
                       created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )''')

    # Create vehicles table
    cursor.execute('''
                   CREATE TABLE vehicles
                   (
                       id                        INTEGER PRIMARY KEY AUTOINCREMENT,
                       reg                       TEXT UNIQUE NOT NULL,
                       variant                   TEXT        NOT NULL,
                       model                     TEXT,
                       year                      INTEGER,
                       color                     TEXT,
		       engine_no                 TEXT,
		       chassis_no                TEXT,
		       meter_reading             INTEGER,
                       investor_id               INTEGER,
                       company_id                INTEGER,
                       monthly_rent_from_company REAL,
                       monthly_pay_to_investor   REAL,
                       status                    TEXT      DEFAULT 'Available',
                       onboarded_by              TEXT,
                       deployed_to               TEXT,
                       rent_stopped_date         DATE,
                       created_at                TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       FOREIGN KEY (investor_id) REFERENCES investors (id),
                       FOREIGN KEY (company_id) REFERENCES companies (id)
                   )''')

    # Create short_term_rentals table (daily rentals)
    cursor.execute('''
                   CREATE TABLE short_term_rentals
                   (
                       id                     INTEGER PRIMARY KEY AUTOINCREMENT,
                       vehicle_id             INTEGER NOT NULL,
                       client_name            TEXT    NOT NULL,
                       booker_name            TEXT,
                       start_date             DATE    NOT NULL,
                       end_date               DATE    NOT NULL,
                       per_day_rate           REAL,
                       duration_days          INTEGER,
                       total_amount           REAL,
                       fuel_expense           REAL      DEFAULT 0,
                       investor_cost          REAL,
                       driver_cost            REAL      DEFAULT 0,
                       maintenance_percentage REAL      DEFAULT 0,
                       profit                 REAL,
                       agent_id               INTEGER,
                       agent_commission       REAL,
                       status                 TEXT      DEFAULT 'Active',
                       driver_name            TEXT,
                       notes                  TEXT,
                       created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       FOREIGN KEY (vehicle_id) REFERENCES vehicles (id),
                       FOREIGN KEY (agent_id) REFERENCES agents (id)
                   )''')

    # Create agents table (booking agents)
    cursor.execute('''
                   CREATE TABLE agents
                   (
                       id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                       name                  TEXT NOT NULL,
                       phone                 TEXT,
                       email                 TEXT,
                       commission_percentage REAL      DEFAULT 20.0,
                       status                TEXT      DEFAULT 'Active',
                       created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )''')

    # Create investor_payments table
    cursor.execute('''
                   CREATE TABLE investor_payments
                   (
                       id             INTEGER PRIMARY KEY AUTOINCREMENT,
                       investor_id    INTEGER NOT NULL,
                       vehicle_id     INTEGER,
                       amount         REAL    NOT NULL,
                       payment_date   DATE    NOT NULL,
                       cheque_no      TEXT,
                       description    TEXT,
                       month_year     TEXT,
                       status         TEXT      DEFAULT 'Pending',
                       payment_method TEXT      DEFAULT 'Cheque',
                       notes          TEXT,
                       created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       FOREIGN KEY (investor_id) REFERENCES investors (id),
                       FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
                   )''')

    # Create agent_commissions table
    cursor.execute('''
                   CREATE TABLE agent_commissions
                   (
                       id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                       agent_id              INTEGER NOT NULL,
                       rental_id             INTEGER,
                       amount                REAL    NOT NULL,
                       commission_percentage REAL      DEFAULT 20.0,
                       payment_date          DATE,
                       status                TEXT      DEFAULT 'Pending',
                       notes                 TEXT,
                       created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       FOREIGN KEY (agent_id) REFERENCES agents (id)
                   )''')

# Create maintenance table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS maintenance
                   (
                       id                INTEGER PRIMARY KEY AUTOINCREMENT,
                       vehicle_id        INTEGER NOT NULL,
                       description       TEXT NOT NULL,
		       workshop          TEXT,
                       amount            REAL DEFAULT 0,
                       maintenance_date  DATE,
                       current_mileage   INTEGER,
                       next_due_date     DATE,
                       status            TEXT DEFAULT 'Completed',
                       created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
                   )''')





    # Insert admin user
    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin', 'Admin')")
        print("Admin user created")
    except:
        print("Admin user already exists")

    conn.commit()
    conn.close()
    print("Database initialized successfully!")


# Initialize database
init_db()


# ================ SAMPLE DATA GENERATOR ================
def generate_sample_data():
    """Generate sample records matching AA Transportation business model"""
    print("\nGenerating sample data for AA Transportation...")

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    # Check if we already have data
    cursor.execute("SELECT COUNT(*) FROM vehicles")
    count = cursor.fetchone()[0]

    if count > 0:
        print(f"Database already has {count} vehicles. Skipping sample data generation.")
        conn.close()
        return

    print("Creating sample data matching AA Transportation operations...")

    # Generate sample investors
    investors = [
        ('Irfan AGHA', 'Irfan AGHA', 'irfan@example.com', '+92-300-111-1111', 'Karachi', '42301-1234567-8',
         'HBL Account #123456', 100000.0),
        ('Ramzan Ali', 'Ramzan Ali', 'ramzan@example.com', '+92-300-222-2222', 'Karachi', '42301-2345678-9',
         'MCB Account #654321', 95000.0),
        ('Anthony', 'Anthony', 'anthony@example.com', '+92-300-333-3333', 'Karachi', '42301-3456789-0',
         'UBL Account #789012', 80000.0),
        ('Muhammad Rafiq', 'Muhammad Rafiq', 'rafiq@example.com', '+92-300-444-4444', 'Karachi', '42301-4567890-1',
         'ABL Account #345678', 85000.0),
    ]

    cursor.executemany('''
                       INSERT INTO investors (name, father_name, email, phone, address, cnic, bank_details,
                                              monthly_payment_rate)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                       ''', investors)

    print("✓ 4 investors created")

    # Get investor IDs
    cursor.execute("SELECT id FROM investors")
    investor_ids = [row[0] for row in cursor.fetchall()]

    # Generate sample companies
    companies = [
        ('Magento', 'John Smith', 'john@magento.com', '+92-300-666-6666', 'Karachi', 'Karachi', 'TIN-001'),
        ('GCS', 'Sarah Khan', 'sarah@gcs.com', '+92-300-777-7777', 'Lahore', 'Lahore', 'TIN-002'),
        ('Umair', 'Ali Ahmed', 'ali@umair.com', '+92-300-888-8888', 'Islamabad', 'Islamabad', 'TIN-003'),
        ('Kapec', 'Fatima Raza', 'fatima@kapec.com', '+92-300-999-9999', 'Rawalpindi', 'Rawalpindi', 'TIN-004'),
    ]

    cursor.executemany('''
                       INSERT INTO companies (name, contact_person, email, phone, address, billing_address, ntn)
                       VALUES (?, ?, ?, ?, ?, ?, ?)
                       ''', companies)

    print("✓ 4 companies created")

    # Get company IDs
    cursor.execute("SELECT id FROM companies")
    company_ids = [row[0] for row in cursor.fetchall()]

    # Generate sample vehicles
    vehicles = [
        ('BRG-522', 'Honda Civic', 'Civic', 2019, 'White', investor_ids[0], company_ids[0], 125000, 100000, 'Deployed',
         'Saqib', 'Farhan', None),
        ('BWB-513', 'Toyota Corolla Altis X', 'Corolla Altis X', 2022, 'Black', investor_ids[0], company_ids[1], 120000,
         95000, 'Deployed', 'Saqib', 'Farhan', None),
        ('BXU-846', 'Suzuki Alto AGS', 'Alto AGS', 2022, 'Red', investor_ids[0], company_ids[2], 65000, 60000,
         'Available', 'Saqib', 'Tariq', None),
        ('BST-609', 'Suzuki Alto AGS', 'Alto AGS', 2021, 'Silver', investor_ids[1], company_ids[3], 65000, 50000,
         'Deployed', 'Saqib', 'Farhan', None),
    ]

    cursor.executemany('''
                       INSERT INTO vehicles (reg, variant, model, year, color, investor_id, company_id,
                                             monthly_rent_from_company, monthly_pay_to_investor, status,
                                             onboarded_by, deployed_to, rent_stopped_date)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ''', vehicles)

    print("✓ 4 vehicles created")

    # Generate sample agents
    agents = [
        ('Farhan', '+92-300-111-2222', 'farhan@aatransport.com', 20.0),
        ('Tariq', '+92-300-222-3333', 'tariq@aatransport.com', 20.0),
        ('Shahzaib', '+92-300-333-4444', 'shahzaib@aatransport.com', 20.0),
    ]

    cursor.executemany('''
                       INSERT INTO agents (name, phone, email, commission_percentage)
                       VALUES (?, ?, ?, ?)
                       ''', agents)

    print("✓ 3 agents created")

    # Generate sample short-term rentals
    vehicle_regs = ['BRG-522', 'BWB-513', 'BXU-846', 'BST-609']
    vehicle_ids = {}

    for reg in vehicle_regs:
        cursor.execute("SELECT id FROM vehicles WHERE reg = ?", (reg,))
        result = cursor.fetchone()
        if result:
            vehicle_ids[reg] = result[0]

    agent_map = {'Farhan': 1, 'Tariq': 2, 'Shahzaib': 3}

    # Create 4 sample rentals
    for i in range(4):
        vehicle_id = vehicle_ids.get(vehicle_regs[i % 4], 1)
        agent_id = list(agent_map.values())[i % 3]

        total_amount = (i + 1) * 5000
        investor_cost = total_amount * 0.7
        profit = total_amount - investor_cost
        agent_commission = profit * 0.20

        cursor.execute('''
                       INSERT INTO short_term_rentals
                       (vehicle_id, client_name, booker_name, start_date, end_date, per_day_rate,
                        duration_days, total_amount, investor_cost, profit, agent_id, agent_commission, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ''', (
                           vehicle_id,
                           f'Client {i + 1}',
                           list(agent_map.keys())[i % 3],
                           (date.today() - timedelta(days=i * 2)).isoformat(),
                           (date.today() + timedelta(days=(i + 1) * 2)).isoformat(),
                           5000,
                           i + 1,
                           total_amount,
                           investor_cost,
                           profit,
                           agent_id,
                           agent_commission,
                           'Active'
                       ))

        # Add to agent commissions table
        rental_id = cursor.lastrowid
        cursor.execute('''
                       INSERT INTO agent_commissions (agent_id, rental_id, amount, commission_percentage, status)
                       VALUES (?, ?, ?, ?, ?)
                       ''', (agent_id, rental_id, agent_commission, 20.0, 'Pending'))

    print("✓ 4 short-term rental records created")

    # Generate sample investor payments
    for i in range(3):
        conn.execute('''
                     INSERT INTO investor_payments (investor_id, vehicle_id, amount, payment_date,
                                                    cheque_no, description, month_year, status)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                     ''', (
                         investor_ids[i % 4],
                         vehicle_ids.get(vehicle_regs[i % 4]),
                         75000 + (i * 10000),
                         (date.today() - timedelta(days=30 - i * 10)).isoformat(),
                         f'0000320{7 + i}',
                         f'Payment for the month of {date.today().strftime("%b %Y")}',
                         f'{date.today().strftime("%b %Y")}',
                         'Completed' if i < 2 else 'Pending'
                     ))

    print("✓ 3 investor payment records created")

    conn.commit()
    conn.close()

    print("\n✅ AA Transportation sample data generated successfully!")


# Generate sample data
generate_sample_data()


# ================ HELPER FUNCTIONS ================
def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def logged():
    """Check if user is logged in"""
    return 'user' in session


def calculate_profit(company_rent, investor_payment, duration_days=30):
    """Calculate profit for a rental"""
    if duration_days == 30:
        return company_rent - investor_payment
    else:
        daily_company = company_rent / 30
        daily_investor = investor_payment / 30
        return (daily_company * duration_days) - (daily_investor * duration_days)


# ================ AUTHENTICATION ================
@app.route('/', methods=['GET', 'POST'])
def login():
    if logged():
        return redirect('/dashboard')

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session['user'] = user['username']
            session['role'] = user['role']
            session['user_id'] = user['id']
            return redirect('/dashboard')
        else:
            error = "Invalid credentials. Try admin/admin"
            return render_template_string(LOGIN_PAGE, error=error)

    return render_template_string(LOGIN_PAGE)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ================ BASE TEMPLATE RENDERER ================
def render_with_base(title, content):
    """Render page with base template"""
    return render_template_string(BASE_TEMPLATE, title=title, content=content, session=session, request=request)


# ================ DASHBOARD (PROFESSIONAL VERSION) ================
@app.route('/dashboard')
def dashboard():
    if not logged():
        return redirect('/')

    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row

        # 1. Counts aur Data fetch karein (Logic remains SAME)
        total_vehicles = conn.execute('SELECT COUNT(*) FROM vehicles').fetchone()[0]
        active_investors_count = conn.execute("SELECT COUNT(*) FROM investors WHERE status = 'Active'").fetchone()[0]
        active_companies_count = conn.execute("SELECT COUNT(*) FROM companies WHERE status = 'Active'").fetchone()[0]
        
        total_company_rev = conn.execute("SELECT SUM(monthly_rent_from_company) FROM vehicles WHERE company_id IS NOT NULL").fetchone()[0] or 0
        total_investor_pay = conn.execute("SELECT SUM(monthly_pay_to_investor) FROM vehicles WHERE investor_id IS NOT NULL").fetchone()[0] or 0
        calc_profit = total_company_rev - total_investor_pay

        all_investors = conn.execute("SELECT id, name FROM investors ORDER BY name ASC").fetchall()
        all_companies = conn.execute("SELECT id, name FROM companies ORDER BY name ASC").fetchall()
        recent_rentals = conn.execute('''
            SELECT str.*, v.reg FROM short_term_rentals str
            LEFT JOIN vehicles v ON str.vehicle_id = v.id
            ORDER BY str.start_date DESC LIMIT 5
        ''').fetchall()

        conn.close()

        # 2. Options Generate (SAME as before)
        inv_opts = "".join([f'<option value="{i["id"]}">{i["name"]}</option>' for i in all_investors])
        comp_opts = "".join([f'<option value="{c["id"]}">{c["name"]}</option>' for c in all_companies])

        # 3. Rentals Table generate karein (Professional Badges)
        rentals_rows = ""
        if recent_rentals:
            for r in recent_rentals:
                badge = '<span class="badge rounded-pill bg-success-subtle text-success border border-success-subtle">Active</span>' if r['status'] == 'Active' else f'<span class="badge rounded-pill bg-secondary-subtle text-secondary border border-secondary-subtle">{r["status"]}</span>'
                rentals_rows += f"""
                <tr>
                    <td class="py-3 fw-medium">{r['client_name']}</td>
                    <td><span class="badge bg-light text-dark border">{r['reg']}</span></td>
                    <td>{r['duration_days']} Days</td>
                    <td class="fw-bold text-primary">PKR {r['total_amount']:,.0f}</td>
                    <td>{badge}</td>
                </tr>"""
        else:
            rentals_rows = "<tr><td colspan='5' class='text-center py-4 text-muted'>No recent rentals found</td></tr>"

        # 4. Professional Dashboard UI (Only HTML/CSS Changed)
        dashboard_content = '''
        <div class="container-fluid px-4 py-3">
            <div class="d-flex justify-content-between align-items-center mb-4 pb-3 border-bottom">
                <div>
                    <h3 class="fw-bold text-dark mb-0">Analytics Overview</h3>
                    <p class="text-secondary mb-0 small">Real-time status of AA Transportation</p>
                </div>
                <div class="text-end">
                    <div class="p-2 bg-white rounded shadow-sm border small fw-bold"><i class="bi bi-calendar3 me-2 text-primary"></i>{}</div>
                </div>
            </div>

            <div class="row g-4 mb-5">
                <div class="col-md-3">
                    <div class="card h-100 border-0 shadow-sm rounded-4 p-3 bg-white">
                        <div class="d-flex align-items-center">
                            <div class="flex-shrink-0 bg-primary-subtle p-3 rounded-3 me-3"><i class="bi bi-truck fs-4 text-primary"></i></div>
                            <div><p class="text-muted small mb-0 fw-medium text-uppercase">Total Fleet</p><h3 class="fw-bold mb-0">{}</h3></div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card h-100 border-0 shadow-sm rounded-4 p-3 bg-white">
                        <div class="d-flex align-items-center">
                            <div class="flex-shrink-0 bg-success-subtle p-3 rounded-3 me-3"><i class="bi bi-people fs-4 text-success"></i></div>
                            <div><p class="text-muted small mb-0 fw-medium text-uppercase">Investors</p><h3 class="fw-bold mb-0">{}</h3></div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card h-100 border-0 shadow-sm rounded-4 p-3 bg-white">
                        <div class="d-flex align-items-center">
                            <div class="flex-shrink-0 bg-warning-subtle p-3 rounded-3 me-3"><i class="bi bi-building fs-4 text-warning"></i></div>
                            <div><p class="text-muted small mb-0 fw-medium text-uppercase">Companies</p><h3 class="fw-bold mb-0">{}</h3></div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card h-100 border-0 shadow-sm rounded-4 p-3 bg-primary text-white">
                        <div class="d-flex align-items-center">
                            <div class="flex-shrink-0 bg-white bg-opacity-25 p-3 rounded-3 me-3"><i class="bi bi-cash-coin fs-4 text-white"></i></div>
                            <div><p class="text-white-50 small mb-0 fw-medium text-uppercase">Net Profit</p><h3 class="fw-bold mb-0">PKR {}</h3></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row g-4">
                <div class="col-lg-4">
                    <div class="card border-0 shadow-sm rounded-4 mb-4">
                        <div class="card-body p-4 text-center">
                            <div class="bg-primary-subtle d-inline-block p-3 rounded-circle mb-3"><i class="bi bi-file-earmark-pdf text-primary fs-3"></i></div>
                            <h5 class="fw-bold mb-3">Billing & Invoices</h5>
                            <form action="/generate_investor_invoice_redirect" method="POST" class="mb-3">
                                <label class="small fw-bold text-muted d-block text-start mb-1">Investor Payouts</label>
                                <div class="input-group">
                                    <select name="investor_id" class="form-select border-end-0 bg-light" required>
                                        <option value="">Choose Investor...</option>
                                        {}
                                    </select>
                                    <button type="submit" class="btn btn-primary px-3">Go</button>
                                </div>
                            </form>
                            <form action="/generate_company_invoice_redirect" method="POST">
                                <label class="small fw-bold text-muted d-block text-start mb-1">Corporate Billing</label>
                                <div class="input-group">
                                    <select name="company_id" class="form-select border-end-0 bg-light" required>
                                        <option value="">Choose Company...</option>
                                        {}
                                    </select>
                                    <button type="submit" class="btn btn-info text-white px-3">Go</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>

                <div class="col-lg-8">
                    <div class="card border-0 shadow-sm rounded-4 overflow-hidden">
                        <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center">
                            <h6 class="mb-0 fw-bold"><i class="bi bi-clock-history me-2"></i>Recent Rental Activity</h6>
                            <a href="/short_term_rentals" class="btn btn-sm btn-outline-primary rounded-pill px-3">View All</a>
                        </div>
                        <div class="table-responsive">
                            <table class="table table-hover align-middle mb-0">
                                <thead class="bg-light">
                                    <tr>
                                        <th class="border-0 px-4">CLIENT NAME</th>
                                        <th class="border-0">VEHICLE</th>
                                        <th class="border-0">DURATION</th>
                                        <th class="border-0">AMOUNT</th>
                                        <th class="border-0">STATUS</th>
                                    </tr>
                                </thead>
                                <tbody>{}</tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''.format(
            date.today().strftime('%A, %B %d, %Y'),
            total_vehicles,
            active_investors_count,
            active_companies_count,
            "{:,.0f}".format(calc_profit),
            inv_opts,
            comp_opts,
            rentals_rows
        )

        return render_with_base("Dashboard", dashboard_content)

    except Exception as e:
        return f"Dashboard Error: {str(e)}", 500

@app.route('/generate_investor_invoice_redirect', methods=['POST'])
def generate_investor_invoice_redirect():
    investor_id = request.form.get('investor_id')
    return redirect(f'/generate_investor_invoice/{investor_id}')

@app.route('/generate_company_invoice_redirect', methods=['POST'])
def generate_company_invoice_redirect():
    company_id = request.form.get('company_id')
    return redirect(f'/generate_company_invoice/{company_id}')

# ================ INVESTORS MANAGEMENT ================
@app.route('/investors', methods=['GET', 'POST'])
def investors():
    if not logged():
        return redirect('/')

    conn = get_db_connection()

    if request.method == 'POST':
        action = request.form.get('action', 'add')

        if action == 'add':
            conn.execute('''
                         INSERT INTO investors (name, father_name, email, phone, address, 
                                                cnic, agreement_start, agreement_end, 
                                                witness_1_name, witness_1_cnic, 
                                                witness_2_name, witness_2_cnic, 
                                                bank_details, monthly_payment_rate, status)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                         ''', (
                             request.form['name'],
                             request.form.get('father_name', ''),
                             request.form.get('email', ''),
                             request.form.get('phone', ''),
                             request.form.get('address', ''),
                             request.form.get('cnic', ''),
                             request.form.get('agreement_start', ''),
                             request.form.get('agreement_end', ''),
                             request.form.get('witness_1_name', ''),
                             request.form.get('witness_1_cnic', ''),
                             request.form.get('witness_2_name', ''),
                             request.form.get('witness_2_cnic', ''),
                             request.form.get('bank_details', ''),
                             float(request.form.get('monthly_payment_rate', 75000.0)),
                             request.form.get('status', 'Active')
                         ))
            conn.commit()
            conn.close()
            return redirect('/investors?success=added')

        elif action == 'edit':
            conn.execute('''
                         UPDATE investors
                         SET name=?, father_name=?, email=?, phone=?, address=?, 
                             cnic=?, agreement_start=?, agreement_end=?, 
                             witness_1_name=?, witness_1_cnic=?, 
                             witness_2_name=?, witness_2_cnic=?, 
                             bank_details=?, monthly_payment_rate=?, status=?
                         WHERE id = ?
                         ''', (
                             request.form['name'],
                             request.form.get('father_name', ''),
                             request.form.get('email', ''),
                             request.form.get('phone', ''),
                             request.form.get('address', ''),
                             request.form.get('cnic', ''),
                             request.form.get('agreement_start', ''),
                             request.form.get('agreement_end', ''),
                             request.form.get('witness_1_name', ''),
                             request.form.get('witness_1_cnic', ''),
                             request.form.get('witness_2_name', ''),
                             request.form.get('witness_2_cnic', ''),
                             request.form.get('bank_details', ''),
                             float(request.form.get('monthly_payment_rate', 75000.0)),
                             request.form.get('status', 'Active'),
                             request.form['id']
                         ))
            conn.commit()
            conn.close()
            return redirect('/investors?success=updated')

        elif action == 'delete':
            conn.execute('DELETE FROM investors WHERE id=?', (request.form['id'],))
            conn.commit()
            conn.close()
            return redirect('/investors?success=deleted')

    # Get all investors with vehicle count
    investors_list = conn.execute('''
                                  SELECT i.*, 
                                         (SELECT COUNT(*) FROM vehicles WHERE investor_id = i.id) as vehicle_count
                                  FROM investors i
                                  ORDER BY i.status DESC, i.name ASC
                                  ''').fetchall()
    conn.close()

    success_message = ''
    success = request.args.get('success')
    if success == 'added':
        success_message = '<div class="alert alert-success alert-dismissible fade show">Investor added successfully!<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
    elif success == 'updated':
        success_message = '<div class="alert alert-success alert-dismissible fade show">Investor updated successfully!<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
    elif success == 'deleted':
        success_message = '<div class="alert alert-success alert-dismissible fade show">Investor deleted successfully!<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'

    investors_content = f'''
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h4 class="fw-bold mb-1"><i class="bi bi-people me-2"></i>Investors/Owners Management</h4>
            <p class="text-muted mb-0">Manage vehicle owners who provide vehicles to AA Transportation</p>
        </div>
        <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addInvestorModal">
            <i class="bi bi-plus-circle me-1"></i>Add Investor
        </button>
    </div>

    {success_message}

    <div class="card">
        <div class="card-header"><h6 class="mb-0">All Investors ({len(investors_list)})</h6></div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Contact</th>
                            <th>CNIC</th>
                            <th>Monthly Rate</th>
                            <th>Vehicles</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
    '''

    for investor in investors_list:
        status_badge = f'<span class="badge bg-{"success" if investor["status"]=="Active" else "secondary"}">{investor["status"]}</span>'
        
        investors_content += f'''
            <tr>
                <td><strong>{investor['name']}</strong><br><small class="text-muted">{investor['father_name'] or ''}</small></td>
                <td><small>{investor['phone'] or ''}<br>{investor['email'] or ''}</small></td>
                <td>{investor['cnic'] or 'N/A'}</td>
                <td><span class="badge bg-info">PKR {investor['monthly_payment_rate']:,.2f}</span></td>
                <td>{investor['vehicle_count']}</td>
                <td>{status_badge}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button type="button" class="btn btn-outline-warning" data-bs-toggle="modal" data-bs-target="#editInvestorModal" 
                                onclick="loadInvestorData({investor['id']}, '{investor['name']}', '{investor['father_name'] or ''}', 
                                '{investor['email'] or ''}', '{investor['phone'] or ''}', '{investor['address'] or ''}', 
                                '{investor['cnic'] or ''}', '{investor['agreement_start'] or ''}', '{investor['agreement_end'] or ''}', 
                                '{investor['witness_1_name'] or ''}', '{investor['witness_1_cnic'] or ''}', 
                                '{investor['witness_2_name'] or ''}', '{investor['witness_2_cnic'] or ''}', 
                                '{investor['bank_details'] or ''}', {investor['monthly_payment_rate']}, '{investor['status']}')">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <form method="POST" style="display:inline">
                            <input type="hidden" name="action" value="delete">
                            <input type="hidden" name="id" value="{investor['id']}">
                            <button type="submit" class="btn btn-outline-danger" onclick="return confirm('Delete investor?')"><i class="bi bi-trash"></i></button>
                        </form>
                    </div>
                </td>
            </tr>
        '''

    investors_content += f'''
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="modal fade" id="addInvestorModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header"><h5 class="modal-title">Add New Investor</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
                <form method="POST">
                    <input type="hidden" name="action" value="add">
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6 mb-3"><label class="form-label">Name *</label><input type="text" name="name" class="form-control" required></div>
                            <div class="col-md-6 mb-3"><label class="form-label">Father Name</label><input type="text" name="father_name" class="form-control"></div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3"><label class="form-label">CNIC</label><input type="text" name="cnic" class="form-control"></div>
                            <div class="col-md-6 mb-3"><label class="form-label">Phone</label><input type="text" name="phone" class="form-control"></div>
                        </div>
                        <div class="mb-3"><label class="form-label">Address</label><textarea name="address" class="form-control" rows="2"></textarea></div>
                        <div class="row border-top pt-3">
                            <div class="col-md-6 mb-3"><label class="form-label">Agreement Start</label><input type="date" name="agreement_start" class="form-control"></div>
                            <div class="col-md-6 mb-3"><label class="form-label">Agreement End</label><input type="date" name="agreement_end" class="form-control"></div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3"><label class="form-label">Witness 1 Name</label><input type="text" name="witness_1_name" class="form-control"></div>
                            <div class="col-md-6 mb-3"><label class="form-label">Witness 1 CNIC</label><input type="text" name="witness_1_cnic" class="form-control"></div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3"><label class="form-label">Witness 2 Name</label><input type="text" name="witness_2_name" class="form-control"></div>
                            <div class="col-md-6 mb-3"><label class="form-label">Witness 2 CNIC</label><input type="text" name="witness_2_cnic" class="form-control"></div>
                        </div>
                        <div class="row border-top pt-3">
                            <div class="col-md-6 mb-3"><label class="form-label">Monthly Rate</label><input type="number" step="0.01" name="monthly_payment_rate" class="form-control" value="75000"></div>
                            <div class="col-md-6 mb-3"><label class="form-label">Status</label><select name="status" class="form-select"><option value="Active">Active</option><option value="Inactive">Inactive</option></select></div>
                        </div>
                        <div class="mb-3"><label class="form-label">Bank Details</label><textarea name="bank_details" class="form-control" rows="2"></textarea></div>
                    </div>
                    <div class="modal-footer"><button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button><button type="submit" class="btn btn-primary">Save Investor</button></div>
                </form>
            </div>
        </div>
    </div>

    <div class="modal fade" id="editInvestorModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header"><h5 class="modal-title">Edit Investor</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
                <form method="POST">
                    <input type="hidden" name="action" value="edit">
                    <input type="hidden" name="id" id="edit_investor_id">
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6 mb-3"><label class="form-label">Name *</label><input type="text" name="name" id="edit_investor_name" class="form-control" required></div>
                            <div class="col-md-6 mb-3"><label class="form-label">Father Name</label><input type="text" name="father_name" id="edit_investor_father" class="form-control"></div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3"><label class="form-label">CNIC</label><input type="text" name="cnic" id="edit_investor_cnic" class="form-control"></div>
                            <div class="col-md-6 mb-3"><label class="form-label">Phone</label><input type="text" name="phone" id="edit_investor_phone" class="form-control"></div>
                        </div>
                        <div class="mb-3"><label class="form-label">Address</label><textarea name="address" id="edit_investor_address" class="form-control" rows="2"></textarea></div>
                        <div class="row border-top pt-3">
                            <div class="col-md-6 mb-3"><label class="form-label">Agreement Start</label><input type="date" name="agreement_start" id="edit_investor_start" class="form-control"></div>
                            <div class="col-md-6 mb-3"><label class="form-label">Agreement End</label><input type="date" name="agreement_end" id="edit_investor_end" class="form-control"></div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3"><label class="form-label">Witness 1 Name</label><input type="text" name="witness_1_name" id="edit_investor_w1n" class="form-control"></div>
                            <div class="col-md-6 mb-3"><label class="form-label">Witness 1 CNIC</label><input type="text" name="witness_1_cnic" id="edit_investor_w1c" class="form-control"></div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3"><label class="form-label">Witness 2 Name</label><input type="text" name="witness_2_name" id="edit_investor_w2n" class="form-control"></div>
                            <div class="col-md-6 mb-3"><label class="form-label">Witness 2 CNIC</label><input type="text" name="witness_2_cnic" id="edit_investor_w2c" class="form-control"></div>
                        </div>
                        <div class="row border-top pt-3">
                            <div class="col-md-6 mb-3"><label class="form-label">Monthly Rate</label><input type="number" step="0.01" name="monthly_payment_rate" id="edit_investor_rate" class="form-control"></div>
                            <div class="col-md-6 mb-3"><label class="form-label">Status</label><select name="status" id="edit_investor_status" class="form-select"><option value="Active">Active</option><option value="Inactive">Inactive</option></select></div>
                        </div>
                        <div class="mb-3"><label class="form-label">Bank Details</label><textarea name="bank_details" id="edit_investor_bank" class="form-control" rows="2"></textarea></div>
                    </div>
                    <div class="modal-footer"><button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button><button type="submit" class="btn btn-primary">Update Investor</button></div>
                </form>
            </div>
        </div>
    </div>

    <script>
    function loadInvestorData(id, name, father, email, phone, address, cnic, start, end, w1n, w1c, w2n, w2c, bank, rate, status) {{
        document.getElementById('edit_investor_id').value = id;
        document.getElementById('edit_investor_name').value = name;
        document.getElementById('edit_investor_father').value = father;
        document.getElementById('edit_investor_phone').value = phone;
        document.getElementById('edit_investor_address').value = address;
        document.getElementById('edit_investor_cnic').value = cnic;
        document.getElementById('edit_investor_start').value = start;
        document.getElementById('edit_investor_end').value = end;
        document.getElementById('edit_investor_w1n').value = w1n;
        document.getElementById('edit_investor_w1c').value = w1c;
        document.getElementById('edit_investor_w2n').value = w2n;
        document.getElementById('edit_investor_w2c').value = w2c;
        document.getElementById('edit_investor_bank').value = bank;
        document.getElementById('edit_investor_rate').value = rate;
        document.getElementById('edit_investor_status').value = status;
    }}
    </script>
    '''

    return render_with_base("Investors", investors_content)


# ================ COMPANIES MANAGEMENT ================
@app.route('/companies', methods=['GET', 'POST'])
def companies():
    if not logged():
        return redirect('/')

    # IS LINE KO BADLEIN:
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    if request.method == 'POST':
        action = request.form.get('action', 'add')
        if action == 'add':    
            conn.execute('''
                INSERT INTO companies (name, contact_person, manager_cnic, email, phone, address, 
                                               billing_address, ntn,  effective_date, termination_date,
                                               witness_1_name, witness_1_cnic, witness_2_name, witness_2_cnic,
                                               payment_terms, status)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                         ''', (
                             request.form['name'],
                             request.form.get('contact_person', ''),
                             request.form.get('manager_cnic', ''),  # Naya Variable
                             request.form.get('email', ''),
                             request.form.get('phone', ''),
                             request.form.get('address', ''),
                             request.form.get('billing_address', ''),
                             request.form.get('ntn', ''),
                             request.form.get('effective_date', ''),
                             request.form.get('termination_date', ''),
                             request.form.get('witness_1_name', ''),
                             request.form.get('witness_1_cnic', ''),
                             request.form.get('witness_2_name', ''),
                             request.form.get('witness_2_cnic', ''),
                             request.form.get('payment_terms', 'Net 30'),
                             request.form.get('status', 'Active')
                         ))
            conn.commit()
            conn.close()
            return redirect('/companies?success=added')

        elif action == 'edit':
            conn.execute('''
                         UPDATE companies
                         SET name=?,
                             contact_person=?,
                             manager_cnic=?,  -- Naya Variable
                             email=?,
                             phone=?,
                             address=?,
                             billing_address=?,
                             ntn=?,
                             effective_date=?,    -- Naya Variable
                             termination_date=?,  -- Naya Variable
                             witness_1_name=?,    -- Naya Variable
                             witness_1_cnic=?,    -- Naya Variable
                             witness_2_name=?,    -- Naya Variable
                             witness_2_cnic=?,    -- Naya Variable
                             payment_terms=?,
                             status=?
                         WHERE id = ?
                         ''', (
                             request.form['name'],
                             request.form.get('contact_person', ''),
                             request.form.get('manager_cnic', ''), # Naya Variable
                             request.form.get('email', ''),
                             request.form.get('phone', ''),
                             request.form.get('address', ''),
                             request.form.get('billing_address', ''),
                             request.form.get('ntn', ''),
                             request.form.get('effective_date', ''),
                             request.form.get('termination_date', ''),
                             request.form.get('witness_1_name', ''),
                             request.form.get('witness_1_cnic', ''),
                             request.form.get('witness_2_name', ''),
                             request.form.get('witness_2_cnic', ''),
                             request.form.get('payment_terms', 'Net 30'),
                             request.form.get('status', 'Active'),
                             request.form['id']
                         ))
            conn.commit()
            conn.close()
            return redirect('/companies?success=updated')

        elif action == 'delete':
            conn.execute('DELETE FROM companies WHERE id=?', (request.form['id'],))
            conn.commit()
            conn.close()
            return redirect('/companies?success=deleted')

    # Get all companies with vehicle count
    companies_list = conn.execute('''
                                  SELECT c.*, 
                                         (SELECT COUNT(*) FROM vehicles WHERE company_id = c.id) as vehicle_count
                                  FROM companies c
                                  ORDER BY c.status DESC, c.name ASC
                                  ''').fetchall()

    conn.close()

    # Check for success message
    success_message = ''
    success = request.args.get('success')
    if success == 'added':
        success_message = '<div class="alert alert-success alert-dismissible fade show">Company added successfully!<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
    elif success == 'updated':
        success_message = '<div class="alert alert-success alert-dismissible fade show">Company updated successfully!<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
    elif success == 'deleted':
        success_message = '<div class="alert alert-success alert-dismissible fade show">Company deleted successfully!<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'

    companies_content = f'''
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h4 class="fw-bold mb-1"><i class="bi bi-building me-2"></i>Companies Management</h4>
            <p class="text-muted mb-0">Manage companies that rent vehicles from AA Transportation</p>
        </div>
        <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addCompanyModal">
            <i class="bi bi-plus-circle me-1"></i>Add Company
        </button>
    </div>

    {success_message}

    <div class="card">
        <div class="card-header">
            <h6 class="mb-0">All Companies ({len(companies_list)})</h6>
        </div>
        <div class="card-body">
    '''

    if companies_list:
        companies_content += '''
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Company Name</th>
                            <th>Contact Person</th>
                            <th>Contact Info</th>
                            <th>NTN</th>
                            <th>Vehicles</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        '''

        for company in companies_list:
            if company['status'] == 'Active':
                status_badge = '<span class="badge bg-success">Active</span>'
            elif company['status'] == 'Inactive':
                status_badge = '<span class="badge bg-secondary">Inactive</span>'
            else:
                status_badge = f'<span class="badge bg-warning">{company["status"]}</span>'

            companies_content += f'''
                <tr>
                    <td>
                        <strong>{company['name']}</strong><br>
                        <small class="text-muted">{company['billing_address'] or company['address'] or 'No address'}</small>
                    </td>
                    <td>
                        {company['contact_person'] or 'N/A'}<br>
                        <small class="text-muted">CNIC: {company['manager_cnic'] or 'N/A'}</small>
                    </td>
                    <td>
                        <small>{company['phone'] or 'No phone'}</small><br>
                        <small><strong>Eff:</strong> {company['effective_date'] or '-'}</small><br>
                        <small><strong>Term:</strong> {company['termination_date'] or '-'}</small><br>
                        <small>{company['email'] or 'No email'}</small>
                    </td>
                    <td>{company['ntn'] or 'N/A'}</td>
                    <td>{company['vehicle_count']}</td>
                    <td>{status_badge}</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button type="button" class="btn btn-outline-warning" data-bs-toggle="modal" data-bs-target="#editCompanyModal" 
                                    onclick="loadCompanyData({company['id']}, '{company['name']}', '{company['contact_person'] or ''}', 
                                    '{company['manager_cnic'] or ''}', '{company['email'] or ''}', '{company['phone'] or ''}', '{company['address'] or ''}', 
                                    '{company['billing_address'] or ''}', '{company['ntn'] or ''}', '{company['payment_terms'] or ''}', 
                                    '{company['status']}', '{company['effective_date'] or ''}', '{company['termination_date'] or ''}',
				    '{company['witness_1_name'] or ''}', '{company['witness_1_cnic'] or ''}',
                                    '{company['witness_2_name'] or ''}', '{company['witness_2_cnic'] or ''}',)" title="Edit">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <form method="POST" style="display:inline">
                                <input type="hidden" name="action" value="delete">
                                <input type="hidden" name="id" value="{company['id']}">
                                <button type="submit" class="btn btn-outline-danger" 
                                        onclick="return confirm('Delete company {company["name"]}?')"
                                        title="Delete">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </form>
                        </div>
                    </td>
                </tr>
            '''

        companies_content += '''
                    </tbody>
                </table>
            </div>
        '''
    else:
        companies_content += '''
            <div class="text-center py-5">
                <i class="bi bi-building text-muted" style="font-size: 3rem;"></i>
                <h5 class="mt-3 text-muted">No companies found</h5>
                <p class="text-muted">Add your first company client to get started</p>
                <button type="button" class="btn btn-primary mt-2" data-bs-toggle="modal" data-bs-target="#addCompanyModal">
                    <i class="bi bi-plus-circle me-1"></i>Add Company
                </button>
            </div>
        '''

    companies_content += f'''
        </div>
    </div>

    <div class="modal fade" id="addCompanyModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Add New Company Client</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <form method="POST">
                    <input type="hidden" name="action" value="add">
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">Company Name *</label>
                            <input type="text" name="name" class="form-control" placeholder="Magento" required>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Contact Person (Manager)</label>
                                <input type="text" name="contact_person" class="form-control" placeholder="John Smith">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Manager CNIC</label>
                                <input type="text" name="manager_cnic" class="form-control" placeholder="42101-XXXXXXX-X">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Email</label>
                                <input type="email" name="email" class="form-control" placeholder="contact@company.com">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Phone</label>
                                <input type="tel" name="phone" class="form-control" placeholder="+92-300-123-4567">
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Address</label>
                            <textarea name="address" class="form-control" rows="2" placeholder="Office address..."></textarea>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Billing Address</label>
                            <textarea name="billing_address" class="form-control" rows="2" placeholder="Billing address (if different)..."></textarea>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">NTN Number</label>
                                <input type="text" name="ntn" class="form-control" placeholder="TIN-123456">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Effective Date</label>
                                <input type="date" name="effective_date" class="form-control">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Termination Date</label>
                                <input type="date" name="termination_date" class="form-control">
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Witness 1 Name</label>
                                <input type="text" name="witness_1_name" class="form-control">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Witness 1 CNIC</label>
                                <input type="text" name="witness_1_cnic" class="form-control">
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Witness 2 Name</label>
                                <input type="text" name="witness_2_name" class="form-control">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Witness 2 CNIC</label>
                                <input type="text" name="witness_2_cnic" class="form-control">
                            </div>
                        </div>


                            <div class="col-md-6 mb-3">
                                <label class="form-label">Payment Terms</label>
                                <select name="payment_terms" class="form-select">
                                    <option value="Net 30">Net 30</option>
                                    <option value="Net 15">Net 15</option>
                                    <option value="Net 60">Net 60</option>
                                    <option value="Due on Receipt">Due on Receipt</option>
                                </select>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Status</label>
                            <select name="status" class="form-select">
                                <option value="Active">Active</option>
                                <option value="Inactive">Inactive</option>
                            </select>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-primary">Add Company</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <div class="modal fade" id="editCompanyModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Edit Company Client</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <form method="POST">
                    <input type="hidden" name="action" value="edit">
                    <input type="hidden" name="id" id="edit_company_id">
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Company Name *</label>
                                <input type="text" name="name" id="edit_company_name" class="form-control" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Manager CNIC</label>
                                <input type="text" name="manager_cnic" id="edit_company_cnic" class="form-control">
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Effective Date</label>
                                <input type="date" name="effective_date" id="edit_eff_date" class="form-control">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Termination Date</label>
                                <input type="date" name="termination_date" id="edit_term_date" class="form-control">
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Witness 1 Name</label>
                                <input type="text" name="witness_1_name" id="edit_w1n" class="form-control">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Witness 1 CNIC</label>
                                <input type="text" name="witness_1_cnic" id="edit_w1c" class="form-control">
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Witness 2 Name</label>
                                <input type="text" name="witness_2_name" id="edit_w2n" class="form-control">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Witness 2 CNIC</label>
                                <input type="text" name="witness_2_cnic" id="edit_w2c" class="form-control">
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Phone</label>
                                <input type="tel" name="phone" id="edit_company_phone" class="form-control">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Payment Terms</label>
                                <select name="payment_terms" id="edit_company_terms" class="form-select">
                                    <option value="Net 30">Net 30</option>
                                    <option value="Net 15">Net 15</option>
                                    <option value="Net 60">Net 60</option>
                                    <option value="Due on Receipt">Due on Receipt</option>
                                </select>
                            </div>
                        </div>

                        <div class="mb-3">
                            <label class="form-label">Status</label>
                            <select name="status" id="edit_company_status" class="form-select">
                                <option value="Active">Active</option>
                                <option value="Inactive">Inactive</option>
                            </select>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-primary">Update Company</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script>
    function loadCompanyData(id, name, contact, cnic, email, phone, address, billing, ntn, eff_date, term_date, w1n, w1c, w2n, w2c, terms, status) {{
        document.getElementById('edit_company_id').value = id;
        document.getElementById('edit_company_name').value = name;
        document.getElementById('edit_company_contact').value = contact;
        document.getElementById('edit_company_cnic').value = cnic;
        document.getElementById('edit_company_email').value = email;
        document.getElementById('edit_company_phone').value = phone;
        document.getElementById('edit_company_address').value = address;
        document.getElementById('edit_company_billing').value = billing;
        document.getElementById('edit_company_ntn').value = ntn;
        document.getElementById('edit_eff_date').value = eff_date;
        document.getElementById('edit_term_date').value = term_date;
        document.getElementById('edit_w1n').value = w1n;
        document.getElementById('edit_w1c').value = w1c;
        document.getElementById('edit_w2n').value = w2n;
        document.getElementById('edit_w2c').value = w2c;
        document.getElementById('edit_company_terms').value = terms;
        document.getElementById('edit_company_status').value = status;
    }}
    </script>
    '''

    return render_with_base("Companies", companies_content)


# ================ VEHICLES MANAGEMENT ================
@app.route('/vehicles', methods=['GET', 'POST'])
def vehicles():
    if not logged():
        return redirect('/')

    conn = get_db_connection()

    if request.method == 'POST':
        action = request.form.get('action', 'add')

        if action == 'add':
            conn.execute('''
                         INSERT INTO vehicles (reg, variant, model, year, color, engine_no, chassis_no,meter_reading, investor_id, company_id,
                                               monthly_rent_from_company, monthly_pay_to_investor, status,
                                               onboarded_by, deployed_to, rent_stopped_date)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                         ''', (
                             request.form['reg'],
                             request.form['variant'],
                             request.form.get('model', ''),
                             request.form.get('year') or None,
                             request.form.get('color', ''),
                             request.form.get('engine_no', ''),
                             request.form.get('chassis_no', ''),
                             request.form.get('meter_reading', ''),
                             request.form.get('investor_id') or None,
                             request.form.get('company_id') or None,
                             request.form.get('monthly_rent_from_company') or 0,
                             request.form.get('monthly_pay_to_investor') or 0,
                             request.form.get('status', 'Available'),
                             request.form.get('onboarded_by', ''),
                             request.form.get('deployed_to', ''),
                             request.form.get('rent_stopped_date') or None
                         ))
            conn.commit()
            conn.close()
            return redirect('/vehicles?success=added')

        elif action == 'edit':
            conn.execute('''
                         UPDATE vehicles
                         SET reg=?,
                             variant=?,
                             model=?,
                             year=?,
                             color=?,
                             engine_no=?,   -- Naya field
                             chassis_no=?,  -- Naya field
                             meter_reading=?,
                             investor_id=?,
                             company_id=?,
                             monthly_rent_from_company=?,
                             monthly_pay_to_investor=?,
                             status=?,
                             onboarded_by=?,
                             deployed_to=?,
                             rent_stopped_date=?
                         WHERE id = ?
                         ''', (
                             request.form['reg'],
                             request.form['variant'],
                             request.form.get('model', ''),
                             request.form.get('year') or None,
                             request.form.get('color', ''),
                             request.form.get('engine_no', ''),  # Naya field
                             request.form.get('chassis_no', ''), # Naya field
                             request.form.get('meter_reading', ''),
                             request.form.get('investor_id') or None,
                             request.form.get('company_id') or None,
                             request.form.get('monthly_rent_from_company') or 0,
                             request.form.get('monthly_pay_to_investor') or 0,
                             request.form.get('status', 'Available'),
                             request.form.get('onboarded_by', ''),
                             request.form.get('deployed_to', ''),
                             request.form.get('rent_stopped_date') or None,
                             request.form['id']
                         ))
            conn.commit()
            conn.close()
            return redirect('/vehicles?success=updated')

        elif action == 'delete':
            conn.execute('DELETE FROM vehicles WHERE id=?', (request.form['id'],))
            conn.commit()
            conn.close()
            return redirect('/vehicles?success=deleted')

    # Get all vehicles with investor and company info
    vehicles_list = conn.execute('''
                                  SELECT v.*,
                                         inv.name  as investor_name,
                                         comp.name as company_name
                                  FROM vehicles v
                                           LEFT JOIN investors inv ON v.investor_id = inv.id
                                           LEFT JOIN companies comp ON v.company_id = comp.id
                                  ORDER BY v.reg ASC
                                  ''').fetchall()

    # Get investors for dropdown
    investors_list = conn.execute('SELECT id, name FROM investors WHERE status = "Active" ORDER BY name').fetchall()

    # Get companies for dropdown
    companies_list = conn.execute('SELECT id, name FROM companies WHERE status = "Active" ORDER BY name').fetchall()

    conn.close()

    # Build dropdown options
    investor_options = '<option value="">Select Investor</option>'
    investor_options += ''.join([f'<option value="{i["id"]}">{i["name"]}</option>' for i in investors_list])

    company_options = '<option value="">Select Company</option>'
    company_options += ''.join([f'<option value="{c["id"]}">{c["name"]}</option>' for c in companies_list])

    # Check for success message
    success_message = ''
    success = request.args.get('success')
    if success == 'added':
        success_message = '<div class="alert alert-success alert-dismissible fade show">Vehicle added successfully!<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
    elif success == 'updated':
        success_message = '<div class="alert alert-success alert-dismissible fade show">Vehicle updated successfully!<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
    elif success == 'deleted':
        success_message = '<div class="alert alert-success alert-dismissible fade show">Vehicle deleted successfully!<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'

    vehicles_content = f'''
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h4 class="fw-bold mb-1"><i class="bi bi-truck me-2"></i>Vehicle Fleet Management</h4>
            <p class="text-muted mb-0">Manage vehicles from investors to companies</p>
        </div>
        <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addVehicleModal">
            <i class="bi bi-plus-circle me-1"></i>Add Vehicle
        </button>
    </div>

    {success_message}

    <div class="card">
        <div class="card-header">
            <h6 class="mb-0">All Vehicles ({len(vehicles_list)})</h6>
        </div>
        <div class="card-body">
    '''

    if vehicles_list:
        vehicles_content += '''
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Registration</th>
                            <th>Variant/Model</th>
                            <th>Investor</th>
                            <th>Company</th>
                            <th>Rent from Co.</th>
                            <th>Pay to Investor</th>
                            <th>Profit</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        '''

        for vehicle in vehicles_list:
            if vehicle['status'] == 'Available':
                status_badge = '<span class="badge bg-success">Available</span>'
            elif vehicle['status'] == 'Deployed':
                status_badge = '<span class="badge bg-primary">Deployed</span>'
            elif vehicle['status'] == 'Maintenance':
                status_badge = '<span class="badge bg-warning">Maintenance</span>'
            else:
                status_badge = f'<span class="badge bg-secondary">{vehicle["status"]}</span>'

            investor_info = f'<span class="badge bg-info">{vehicle["investor_name"]}</span>' if vehicle[
                'investor_name'] else '<span class="badge bg-secondary">No Investor</span>'
            company_info = f'<span class="badge bg-success">{vehicle["company_name"]}</span>' if vehicle[
                'company_name'] else '<span class="badge bg-secondary">Available</span>'

            profit = (vehicle['monthly_rent_from_company'] or 0) - (vehicle['monthly_pay_to_investor'] or 0)
            profit_class = 'text-success' if profit > 0 else 'text-danger' if profit < 0 else ''

            vehicles_content += f'''
                <tr>
                    <td><strong>{vehicle['reg']}</strong></td>
                    <td>{vehicle['variant']} {vehicle['model'] or ''} ({vehicle['year'] or 'N/A'})</td>
                    <td>{investor_info}</td>
                    <td>{company_info}</td>
                    <td>PKR {vehicle['monthly_rent_from_company'] or '0':,.2f}</td>
                    <td>PKR {vehicle['monthly_pay_to_investor'] or '0':,.2f}</td>
                    <td><strong class="{profit_class}">PKR {profit:,.2f}</strong></td>
                    <td>{status_badge}</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button type="button" class="btn btn-outline-warning" data-bs-toggle="modal" data-bs-target="#editVehicleModal" 
                                    onclick="loadVehicleData({vehicle['id']}, '{vehicle['reg']}', '{vehicle['variant']}', 
                                    '{vehicle['model'] or ''}', '{vehicle['year'] or ''}', '{vehicle['color'] or ''}', 
                                    '{vehicle['engine_no'] or ''}', '{vehicle['chassis_no'] or ''}','{vehicle['meter_reading'] or ''}', 
                                    {vehicle['investor_id'] or 'null'}, {vehicle['company_id'] or 'null'}, 
                                    {vehicle['monthly_rent_from_company'] or 0}, {vehicle['monthly_pay_to_investor'] or 0}, 
                                    '{vehicle['status']}', '{vehicle['onboarded_by'] or ''}', '{vehicle['deployed_to'] or ''}', 
                                    '{vehicle['rent_stopped_date'] or ''}')" title="Edit">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <form method="POST" style="display:inline">
                                <input type="hidden" name="action" value="delete">
                                <input type="hidden" name="id" value="{vehicle['id']}">
                                <button type="submit" class="btn btn-outline-danger" 
                                        onclick="return confirm('Delete vehicle {vehicle["reg"]}?')"
                                        title="Delete">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </form>
                        </div>
                    </td>
                </tr>
            '''

        vehicles_content += '''
                    </tbody>
                </table>
            </div>
        '''
    else:
        vehicles_content += '''
            <div class="text-center py-5">
                <i class="bi bi-truck text-muted" style="font-size: 3rem;"></i>
                <h5 class="mt-3 text-muted">No vehicles found</h5>
                <p class="text-muted">Add your first vehicle to get started</p>
                <button type="button" class="btn btn-primary mt-2" data-bs-toggle="modal" data-bs-target="#addVehicleModal">
                    <i class="bi bi-plus-circle me-1"></i>Add Vehicle
                </button>
            </div>
        '''

    vehicles_content += f'''
        </div>
    </div>

    <div class="modal fade" id="addVehicleModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Add New Vehicle</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <form method="POST">
                    <input type="hidden" name="action" value="add">
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">Registration Number *</label>
                            <input type="text" name="reg" class="form-control" placeholder="e.g., BRG-522" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Variant *</label>
                            <input type="text" name="variant" class="form-control" placeholder="e.g., Honda Civic" required>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Model</label>
                                <input type="text" name="model" class="form-control" placeholder="e.g., 1.5 Aspire">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">Year</label>
                                <input type="number" name="year" class="form-control" placeholder="e.g., 2021">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">Color</label>
                                <input type="text" name="color" class="form-control" placeholder="e.g., White">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Engine Number</label>
                                <input type="text" name="engine_no" class="form-control" placeholder="Engine No.">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Chassis Number</label>
                                <input type="text" name="chassis_no" class="form-control" placeholder="Chassis No.">
                            </div>
>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Meter Reading</label>
                                <input type="text" name="meter_reading" class="form-control" placeholder="Chassis No.">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Investor/Owner</label>
                                <select name="investor_id" class="form-select">
                                    {investor_options}
                                </select>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Company (Rented to)</label>
                                <select name="company_id" class="form-select">
                                    {company_options}
                                </select>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Monthly Rent from Company (PKR)</label>
                                <input type="number" step="0.01" name="monthly_rent_from_company" 
                                       class="form-control" placeholder="e.g., 125000">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Monthly Pay to Investor (PKR)</label>
                                <input type="number" step="0.01" name="monthly_pay_to_investor" 
                                       class="form-control" placeholder="e.g., 100000">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Onboarded By</label>
                                <input type="text" name="onboarded_by" class="form-control" placeholder="e.g., Saqib">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Deployed To</label>
                                <input type="text" name="deployed_to" class="form-control" placeholder="e.g., Farhan">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Status</label>
                                <select name="status" class="form-select">
                                    <option value="Available">Available</option>
                                    <option value="Deployed">Deployed</option>
                                    <option value="Maintenance">Maintenance</option>
                                    <option value="Inactive">Inactive</option>
                                </select>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Rent Stopped Date</label>
                                <input type="date" name="rent_stopped_date" class="form-control">
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-primary">Add Vehicle</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <div class="modal fade" id="editVehicleModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Edit Vehicle</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <form method="POST">
                    <input type="hidden" name="action" value="edit">
                    <input type="hidden" name="id" id="edit_vehicle_id">
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">Registration Number *</label>
                            <input type="text" name="reg" id="edit_vehicle_reg" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Variant *</label>
                            <input type="text" name="variant" id="edit_vehicle_variant" class="form-control" required>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Model</label>
                                <input type="text" name="model" id="edit_vehicle_model" class="form-control">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">Year</label>
                                <input type="number" name="year" id="edit_vehicle_year" class="form-control">
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">Color</label>
                                <input type="text" name="color" id="edit_vehicle_color" class="form-control">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Engine Number</label>
                                <input type="text" name="engine_no" id="edit_vehicle_engine" class="form-control">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Chassis Number</label>
                                <input type="text" name="chassis_no" id="edit_vehicle_chassis" class="form-control">
                            </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Meter Reading</label>
                                <input type="text" name="meter_reading" id="edit_vehicle_chassis" class="form-control">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Investor/Owner</label>
                                <select name="investor_id" id="edit_vehicle_investor" class="form-select">
                                    {investor_options}
                                </select>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Company (Rented to)</label>
                                <select name="company_id" id="edit_vehicle_company" class="form-select">
                                    {company_options}
                                </select>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Monthly Rent from Company (PKR)</label>
                                <input type="number" step="0.01" name="monthly_rent_from_company" 
                                       id="edit_vehicle_rent" class="form-control">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Monthly Pay to Investor (PKR)</label>
                                <input type="number" step="0.01" name="monthly_pay_to_investor" 
                                       id="edit_vehicle_pay" class="form-control">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Onboarded By</label>
                                <input type="text" name="onboarded_by" id="edit_vehicle_onboarded" class="form-control">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Deployed To</label>
                                <input type="text" name="deployed_to" id="edit_vehicle_deployed" class="form-control">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Status</label>
                                <select name="status" id="edit_vehicle_status" class="form-select">
                                    <option value="Available">Available</option>
                                    <option value="Deployed">Deployed</option>
                                    <option value="Maintenance">Maintenance</option>
                                    <option value="Inactive">Inactive</option>
                                </select>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Rent Stopped Date</label>
                                <input type="date" name="rent_stopped_date" id="edit_vehicle_stopped" class="form-control">
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-primary">Update Vehicle</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script>
    function loadVehicleData(id, reg, variant, model, year, color, engine, chassis,reading, investorId, companyId, rent, pay, status, onboarded, deployed, stopped) {{
        document.getElementById('edit_vehicle_id').value = id;
        document.getElementById('edit_vehicle_reg').value = reg;
        document.getElementById('edit_vehicle_variant').value = variant;
        document.getElementById('edit_vehicle_model').value = model;
        document.getElementById('edit_vehicle_year').value = year;
        document.getElementById('edit_vehicle_color').value = color;
        document.getElementById('edit_vehicle_engine').value = engine;   // Added
        document.getElementById('edit_vehicle_chassis').value = chassis; // Added
        document.getElementById('edit_meter_reading').value = reading; // Added
        document.getElementById('edit_vehicle_investor').value = investorId;
        document.getElementById('edit_vehicle_company').value = companyId;
        document.getElementById('edit_vehicle_rent').value = rent;
        document.getElementById('edit_vehicle_pay').value = pay;
        document.getElementById('edit_vehicle_status').value = status;
        document.getElementById('edit_vehicle_onboarded').value = onboarded;
        document.getElementById('edit_vehicle_deployed').value = deployed;
        document.getElementById('edit_vehicle_stopped').value = stopped;
    }}
    </script>
    '''

    return render_with_base("Vehicles", vehicles_content)


# ================ VEHICLE MAINTENANCE ================
@app.route('/maintenance', methods=['GET', 'POST'])
def maintenance():
    if not logged():
        return redirect('/')

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row

    if request.method == 'POST':
        action = request.form.get('action', 'add')

        if action == 'add':
            v_id = request.form.get('vehicle_id')
            desc = request.form.get('description')
            workshop = request.form.get('workshop', '')  # <--- Naya variable
            amt = float(request.form.get('amount', 0))
            m_date = request.form.get('maintenance_date')
            mileage = request.form.get('current_mileage')
            next_due = request.form.get('next_due_date')
            status = request.form.get('status', 'Completed')

            # UPDATE: Query mein 'workshop' column add kiya gaya hai
            conn.execute('''INSERT INTO maintenance 
                         (vehicle_id, description, workshop, amount, maintenance_date, current_mileage, next_due_date, status) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                         (v_id, desc, workshop, amt, m_date, mileage, next_due, status))
            conn.commit()
            conn.close()
            return redirect('/maintenance?success=added')

        elif action == 'edit':
            m_id = request.form.get('id')
            v_id = request.form.get('vehicle_id')
            desc = request.form.get('description')
            workshop = request.form.get('workshop', '') # <--- Naya variable
            amt = float(request.form.get('amount', 0))
            m_date = request.form.get('maintenance_date')
            mileage = request.form.get('current_mileage')
            next_due = request.form.get('next_due_date')
            status = request.form.get('status')

            # UPDATE: Edit query mein bhi workshop add kiya
            conn.execute('''UPDATE maintenance SET 
                         vehicle_id=?, description=?, workshop=?, amount=?, maintenance_date=?, 
                         current_mileage=?, next_due_date=?, status=?
                         WHERE id=?''', 
                         (v_id, desc, workshop, amt, m_date, mileage, next_due, status, m_id))
            conn.commit()
            conn.close()
            return redirect('/maintenance?success=updated')

        elif action == 'delete':
            conn.execute('DELETE FROM maintenance WHERE id=?', (request.form['id'],))
            conn.commit()
            conn.close()
            return redirect('/maintenance?success=deleted')

    # Fetching Data
    records = conn.execute('''
        SELECT m.*, v.reg, v.variant 
        FROM maintenance m 
        JOIN vehicles v ON m.vehicle_id = v.id 
        ORDER BY m.maintenance_date DESC
    ''').fetchall()
    
    vehicles = conn.execute("SELECT id, reg, variant FROM vehicles").fetchall()
    conn.close()

    success_message = ''
    success = request.args.get('success')
    if success == 'added':
        success_message = '<div class="alert alert-success alert-dismissible fade show">Maintenance record added!</div>'
    elif success == 'updated':
        success_message = '<div class="alert alert-success alert-dismissible fade show">Record updated!</div>'

    v_opts = "".join([f'<option value="{v["id"]}">{v["reg"]} - {v["variant"]}</option>' for v in vehicles])

    # Clean Dropdown Datalist
    clean_datalist = '''
    <datalist id="clean_maintenance_list">
        <option value="Engine Oil">
        <option value="Oil Filter">
        <option value="Ac Filter">
        <option value="Air Filter">
    </datalist>
    '''

    rows = ""
    for r in records:
        status_color = "success" if r['status'] == 'Completed' else "warning"
        # Workshop field handle karne ke liye check
        ws = r['workshop'] if 'workshop' in r.keys() and r['workshop'] else '-'
        
        rows += f'''
        <tr>
            <td>{r['maintenance_date']}</td>
            <td><strong>{r['reg']}</strong></td>
            <td>{r['description']}<br><small class="text-primary">WS: {ws}</small></td>
            <td class="text-danger fw-bold">PKR {float(r['amount']):,.0f}</td>
            <td>{r['current_mileage']} km</td>
            <td><span class="badge bg-{status_color}">{r['status']}</span></td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-warning" data-bs-toggle="modal" data-bs-target="#editMModal" 
                        onclick="loadMData({r['id']}, {r['vehicle_id']}, '{r['description']}', '{ws}', {r['amount']}, '{r['maintenance_date']}', '{r['current_mileage']}', '{r['status']}')">
                        <i class="bi bi-pencil"></i>
                    </button>
                </div>
            </td>
        </tr>'''

    content = f'''
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h4 class="fw-bold"><i class="bi bi-wrench-adjustable me-2"></i>Maintenance Logs</h4>
        <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addMModal">Add Repair Record</button>
    </div>
    {success_message}

    <div class="card border-0 shadow-sm">
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
                <thead class="bg-light">
                    <tr><th>Date</th><th>Vehicle</th><th>Repair & Workshop</th><th>Cost</th><th>Mileage</th><th>Status</th><th>Actions</th></tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </div>

    <div class="modal fade" id="addMModal" tabindex="-1">
        <div class="modal-dialog">
            <form class="modal-content" method="POST">
                <input type="hidden" name="action" value="add">
                <div class="modal-body">
                    <div class="mb-3"><label>Vehicle *</label><select name="vehicle_id" class="form-select" required>{v_opts}</select></div>
                    <div class="mb-3"><label>Description *</label>
                        <input type="text" name="description" class="form-control" list="clean_maintenance_list" autocomplete="off" required>
                        {clean_datalist}
                    </div>
                    <div class="mb-3"><label>Workshop Name</label><input type="text" name="workshop" class="form-control"></div>
                    <div class="row">
                        <div class="col-6 mb-3"><label>Cost (PKR)</label><input type="number" name="amount" class="form-control" required></div>
                        <div class="col-6 mb-3"><label>Current Mileage</label><input type="number" name="current_mileage" class="form-control"></div>
                    </div>
                    <div class="row">
                        <div class="col-6 mb-3"><label>Date</label><input type="date" name="maintenance_date" class="form-control" value="{date.today()}"></div>
                        <div class="col-6 mb-3"><label>Next Due</label><input type="date" name="next_due_date" class="form-control"></div>
                    </div>
                </div>
                <div class="modal-footer"><button type="submit" class="btn btn-primary w-100">Save Record</button></div>
            </form>
        </div>
    </div>

    <div class="modal fade" id="editMModal" tabindex="-1">
        <div class="modal-dialog">
            <form class="modal-content" method="POST">
                <input type="hidden" name="action" value="edit">
                <input type="hidden" name="id" id="edit_m_id">
                <div class="modal-body">
                    <div class="mb-3"><label>Description</label><input type="text" name="description" id="edit_m_desc" class="form-control" list="clean_maintenance_list"></div>
                    <div class="mb-3"><label>Workshop</label><input type="text" name="workshop" id="edit_m_workshop" class="form-control"></div>
                    <div class="row">
                        <div class="col-6 mb-3"><label>Cost</label><input type="number" name="amount" id="edit_m_amt" class="form-control"></div>
                        <div class="col-6 mb-3"><label>Status</label>
                            <select name="status" id="edit_m_status" class="form-select">
                                <option value="Completed">Completed</option>
                                <option value="Pending">Pending</option>
                            </select>
                        </div>
                    </div>
                </div>
                <div class="modal-footer"><button type="submit" class="btn btn-warning w-100">Update Record</button></div>
            </form>
        </div>
    </div>

    <script>
    function loadMData(id, vId, desc, workshop, amt, mDate, mileage, status) {{
        document.getElementById('edit_m_id').value = id;
        document.getElementById('edit_m_desc').value = desc;
        document.getElementById('edit_m_workshop').value = workshop;
        document.getElementById('edit_m_amt').value = amt;
        document.getElementById('edit_m_status').value = status;
    }}
    </script>
    '''
    return render_with_base("Maintenance", content)

# ================ SHORT-TERM RENTALS ================
@app.route('/short-term-rentals', methods=['GET', 'POST'])
def short_term_rentals():
    if not logged():
        return redirect('/')

    conn = get_db_connection()

    if request.method == 'POST':
        action = request.form.get('action', 'add')

        if action == 'add':
            # Get vehicle info for investor cost
            vehicle_id = request.form['vehicle_id']
            cursor = conn.execute('SELECT investor_id, monthly_pay_to_investor FROM vehicles WHERE id = ?',
                                  (vehicle_id,))
            vehicle = cursor.fetchone()

            start_date = request.form['start_date']
            end_date = request.form['end_date']
            per_day_rate = float(request.form.get('per_day_rate', 0))

            # Calculate duration
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            duration_days = (end_dt - start_dt).days

            total_amount = per_day_rate * duration_days

            # Calculate investor cost (pro-rata)
            investor_monthly = vehicle['monthly_pay_to_investor'] if vehicle else 0
            investor_cost = (investor_monthly * duration_days / 30) if duration_days < 30 else investor_monthly

            # Calculate other costs
            fuel_expense = float(request.form.get('fuel_expense', 0))
            driver_cost = float(request.form.get('driver_cost', 0))
            maintenance_percentage = float(request.form.get('maintenance_percentage', 1.0))

            maintenance_cost = total_amount * (maintenance_percentage / 100)

            # Calculate profit
            profit = total_amount - investor_cost - driver_cost - maintenance_cost - fuel_expense

            # Calculate agent commission (20% of profit)
            agent_id = request.form.get('agent_id')
            agent_commission = profit * 0.20 if agent_id else 0

            conn.execute('''
                         INSERT INTO short_term_rentals
                         (vehicle_id, client_name, booker_name, start_date, end_date, per_day_rate,
                          duration_days, total_amount, fuel_expense, investor_cost, driver_cost,
                          maintenance_percentage, profit, agent_id, agent_commission, status,
                          driver_name, notes)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                         ''', (
                             vehicle_id,
                             request.form['client_name'],
                             request.form.get('booker_name', ''),
                             start_date,
                             end_date,
                             per_day_rate,
                             duration_days,
                             total_amount,
                             fuel_expense,
                             investor_cost,
                             driver_cost,
                             maintenance_percentage,
                             profit,
                             agent_id,
                             agent_commission,
                             request.form.get('status', 'Active'),
                             request.form.get('driver_name', ''),
                             request.form.get('notes', '')
                         ))

            conn.commit()
            conn.close()
            return redirect('/short-term-rentals?success=added')

        elif action == 'edit':
            vehicle_id = request.form['vehicle_id']
            cursor = conn.execute('SELECT investor_id, monthly_pay_to_investor FROM vehicles WHERE id = ?',
                                  (vehicle_id,))
            vehicle = cursor.fetchone()

            start_date = request.form['start_date']
            end_date = request.form['end_date']
            per_day_rate = float(request.form.get('per_day_rate', 0))

            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            duration_days = (end_dt - start_dt).days

            total_amount = per_day_rate * duration_days

            investor_monthly = vehicle['monthly_pay_to_investor'] if vehicle else 0
            investor_cost = (investor_monthly * duration_days / 30) if duration_days < 30 else investor_monthly

            fuel_expense = float(request.form.get('fuel_expense', 0))
            driver_cost = float(request.form.get('driver_cost', 0))
            maintenance_percentage = float(request.form.get('maintenance_percentage', 1.0))

            maintenance_cost = total_amount * (maintenance_percentage / 100)

            profit = total_amount - investor_cost - driver_cost - maintenance_cost - fuel_expense

            agent_id = request.form.get('agent_id')
            agent_commission = profit * 0.20 if agent_id else 0

            conn.execute('''
                         UPDATE short_term_rentals
                         SET vehicle_id=?,
                             client_name=?,
                             booker_name=?,
                             start_date=?,
                             end_date=?,
                             per_day_rate=?,
                             duration_days=?,
                             total_amount=?,
                             fuel_expense=?,
                             investor_cost=?,
                             driver_cost=?,
                             maintenance_percentage=?,
                             profit=?,
                             agent_id=?,
                             agent_commission=?,
                             status=?,
                             driver_name=?,
                             notes=?
                         WHERE id = ?
                         ''', (
                             vehicle_id,
                             request.form['client_name'],
                             request.form.get('booker_name', ''),
                             start_date,
                             end_date,
                             per_day_rate,
                             duration_days,
                             total_amount,
                             fuel_expense,
                             investor_cost,
                             driver_cost,
                             maintenance_percentage,
                             profit,
                             agent_id,
                             agent_commission,
                             request.form.get('status', 'Active'),
                             request.form.get('driver_name', ''),
                             request.form.get('notes', ''),
                             request.form['id']
                         ))

            conn.commit()
            conn.close()
            return redirect('/short-term-rentals?success=updated')

        elif action == 'delete':
            conn.execute('DELETE FROM short_term_rentals WHERE id=?', (request.form['id'],))
            conn.commit()
            conn.close()
            return redirect('/short-term-rentals?success=deleted')

    # Get all short-term rentals
    rentals_list = conn.execute('''
                                SELECT str.*, v.reg, v.variant, a.name as agent_name
                                FROM short_term_rentals str
                                         LEFT JOIN vehicles v ON str.vehicle_id = v.id
                                         LEFT JOIN agents a ON str.agent_id = a.id
                                ORDER BY str.start_date DESC
                                ''').fetchall()

    # Get available vehicles
    available_vehicles = conn.execute('''
                                      SELECT v.id, v.reg, v.variant, v.model, v.monthly_pay_to_investor
                                      FROM vehicles v
                                      WHERE v.status = 'Available'
                                         OR v.status = 'Deployed'
                                      ORDER BY v.reg
                                      ''').fetchall()

    # Get agents
    agents_list = conn.execute('SELECT id, name FROM agents WHERE status = "Active"').fetchall()

    conn.close()

    # Build dropdowns
    vehicle_options = ''.join([
                                  f'<option value="{v["id"]}">{v["reg"]} - {v["variant"]} (Monthly: PKR {v["monthly_pay_to_investor"] or 0:,.0f})</option>'
                                  for v in available_vehicles])

    agent_options = '<option value="">No Agent</option>'
    agent_options += ''.join([f'<option value="{a["id"]}">{a["name"]} (20% commission)</option>' for a in agents_list])

    # Check for success message
    success_message = ''
    success = request.args.get('success')
    if success == 'added':
        success_message = '<div class="alert alert-success alert-dismissible fade show">Short-term rental created successfully!<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
    elif success == 'updated':
        success_message = '<div class="alert alert-success alert-dismissible fade show">Rental updated successfully!<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
    elif success == 'deleted':
        success_message = '<div class="alert alert-success alert-dismissible fade show">Rental deleted successfully!<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'

    rentals_content = f'''
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h4 class="fw-bold mb-1"><i class="bi bi-calendar-week me-2"></i>Short-term Rentals Management</h4>
            <p class="text-muted mb-0">Manage daily rentals with agent commissions (20% of profit)</p>
        </div>
        <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addRentalModal">
            <i class="bi bi-plus-circle me-1"></i>New Short-term Rental
        </button>
    </div>

    {success_message}

    <!-- Rentals Table -->
    <div class="card">
        <div class="card-header">
            <h6 class="mb-0">All Short-term Rentals ({len(rentals_list)})</h6>
        </div>
        <div class="card-body">
    '''

    if rentals_list:
        rentals_content += '''
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Client</th>
                            <th>Vehicle</th>
                            <th>Dates</th>
                            <th>Duration</th>
                            <th>Total Amount</th>
                            <th>Investor Cost</th>
                            <th>Profit</th>
                            <th>Agent</th>
                            <th>Agent Commission</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        '''

        for rental in rentals_list:
            if rental['status'] == 'Active':
                status_badge = '<span class="badge bg-success">Active</span>'
            elif rental['status'] == 'Completed':
                status_badge = '<span class="badge bg-info">Completed</span>'
            elif rental['status'] == 'Pending':
                status_badge = '<span class="badge bg-warning">Pending</span>'
            else:
                status_badge = f'<span class="badge bg-secondary">{rental["status"]}</span>'

            dates = f"{rental['start_date']} to {rental['end_date']}"

            agent_info = f'<span class="badge bg-info">{rental["agent_name"]}</span>' if rental[
                'agent_name'] else '<span class="badge bg-secondary">No Agent</span>'

            rentals_content += f'''
                <tr>
                    <td>
                        <strong>{rental['client_name']}</strong><br>
                        <small class="text-muted">Booker: {rental['booker_name'] or 'N/A'}</small>
                    </td>
                    <td>{rental['reg']} ({rental['variant']})</td>
                    <td>{dates}</td>
                    <td>{rental['duration_days']} days</td>
                    <td><strong>PKR {rental['total_amount']:,.2f}</strong></td>
                    <td>PKR {rental['investor_cost']:,.2f}</td>
                    <td><strong class="text-success">PKR {rental['profit']:,.2f}</strong></td>
                    <td>{agent_info}</td>
                    <td>PKR {rental['agent_commission'] or '0':,.2f}</td>
                    <td>{status_badge}</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button type="button" class="btn btn-outline-warning" data-bs-toggle="modal" data-bs-target="#editRentalModal" 
                                    onclick="loadRentalData({rental['id']}, {rental['vehicle_id']}, '{rental['client_name']}', 
                                    '{rental['booker_name'] or ''}', '{rental['start_date']}', '{rental['end_date']}', 
                                    {rental['per_day_rate']}, {rental['fuel_expense'] or 0}, {rental['driver_cost'] or 0}, 
                                    {rental['maintenance_percentage'] or 1.0}, {rental['agent_id'] or 'null'}, 
                                    '{rental['driver_name'] or ''}', '{rental['status']}', '{rental['notes'] or ''}')" title="Edit">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <form method="POST" style="display:inline">
                                <input type="hidden" name="action" value="delete">
                                <input type="hidden" name="id" value="{rental['id']}">
                                <button type="submit" class="btn btn-outline-danger" 
                                        onclick="return confirm('Delete this short-term rental?')"
                                        title="Delete">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </form>
                        </div>
                    </td>
                </tr>
            '''

        rentals_content += '''
                    </tbody>
                </table>
            </div>
        '''
    else:
        rentals_content += '''
            <div class="text-center py-5">
                <i class="bi bi-calendar-week text-muted" style="font-size: 3rem;"></i>
                <h5 class="mt-3 text-muted">No short-term rentals</h5>
                <p class="text-muted">Create your first short-term rental</p>
                <button type="button" class="btn btn-primary mt-2" data-bs-toggle="modal" data-bs-target="#addRentalModal">
                    <i class="bi bi-plus-circle me-1"></i>Create Rental
                </button>
            </div>
        '''

    rentals_content += f'''
        </div>
    </div>

    <!-- Add Rental Modal -->
    <div class="modal fade" id="addRentalModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Create Short-term Rental</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <form method="POST">
                    <input type="hidden" name="action" value="add">
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Client Name *</label>
                                <input type="text" name="client_name" class="form-control" required placeholder="Abdul Rehman F">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Booker Name</label>
                                <input type="text" name="booker_name" class="form-control" placeholder="Farhan">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Vehicle *</label>
                                <select name="vehicle_id" class="form-select" required>
                                    <option value="">Select Vehicle</option>
                                    {vehicle_options}
                                </select>
                                <small class="text-muted">Investor cost calculated automatically based on monthly rate</small>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Agent</label>
                                <select name="agent_id" class="form-select">
                                    {agent_options}
                                </select>
                                <small class="text-muted">Agent gets 20% commission of profit</small>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Start Date *</label>
                                <input type="date" name="start_date" class="form-control" required value="{date.today().isoformat()}">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">End Date *</label>
                                <input type="date" name="end_date" class="form-control" required value="{(date.today() + timedelta(days=2)).isoformat()}">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Per Day Rate (PKR) *</label>
                                <input type="number" step="0.01" name="per_day_rate" class="form-control" required value="5000.00">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Fuel Expense (PKR)</label>
                                <input type="number" step="0.01" name="fuel_expense" class="form-control" value="0.00">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Driver Cost (PKR)</label>
                                <input type="number" step="0.01" name="driver_cost" class="form-control" value="0.00">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Driver Name</label>
                                <input type="text" name="driver_name" class="form-control" placeholder="Driver name if applicable">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Maintenance Percentage (%)</label>
                                <input type="number" step="0.01" name="maintenance_percentage" class="form-control" value="1.0">
                                <small class="text-muted">Percentage of total amount for maintenance</small>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Status</label>
                                <select name="status" class="form-select">
                                    <option value="Active">Active</option>
                                    <option value="Pending">Pending</option>
                                    <option value="Completed">Completed</option>
                                </select>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Notes</label>
                            <textarea name="notes" class="form-control" rows="2" placeholder="Additional notes..."></textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-primary">Create Rental</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- Edit Rental Modal -->
    <div class="modal fade" id="editRentalModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Edit Short-term Rental</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <form method="POST">
                    <input type="hidden" name="action" value="edit">
                    <input type="hidden" name="id" id="edit_rental_id">
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Client Name *</label>
                                <input type="text" name="client_name" id="edit_rental_client" class="form-control" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Booker Name</label>
                                <input type="text" name="booker_name" id="edit_rental_booker" class="form-control">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Vehicle *</label>
                                <select name="vehicle_id" id="edit_rental_vehicle" class="form-select" required>
                                    <option value="">Select Vehicle</option>
                                    {vehicle_options}
                                </select>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Agent</label>
                                <select name="agent_id" id="edit_rental_agent" class="form-select">
                                    {agent_options}
                                </select>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Start Date *</label>
                                <input type="date" name="start_date" id="edit_rental_start" class="form-control" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">End Date *</label>
                                <input type="date" name="end_date" id="edit_rental_end" class="form-control" required>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Per Day Rate (PKR) *</label>
                                <input type="number" step="0.01" name="per_day_rate" id="edit_rental_rate" class="form-control" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Fuel Expense (PKR)</label>
                                <input type="number" step="0.01" name="fuel_expense" id="edit_rental_fuel" class="form-control">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Driver Cost (PKR)</label>
                                <input type="number" step="0.01" name="driver_cost" id="edit_rental_driver_cost" class="form-control">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Driver Name</label>
                                <input type="text" name="driver_name" id="edit_rental_driver_name" class="form-control">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Maintenance Percentage (%)</label>
                                <input type="number" step="0.01" name="maintenance_percentage" id="edit_rental_maintenance" class="form-control" value="1.0">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Status</label>
                                <select name="status" id="edit_rental_status" class="form-select">
                                    <option value="Active">Active</option>
                                    <option value="Pending">Pending</option>
                                    <option value="Completed">Completed</option>
                                </select>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Notes</label>
                            <textarea name="notes" id="edit_rental_notes" class="form-control" rows="2"></textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-primary">Update Rental</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script>
    function loadRentalData(id, vehicleId, client, booker, startDate, endDate, rate, fuel, driverCost, maintenance, agentId, driverName, status, notes) {{
        document.getElementById('edit_rental_id').value = id;
        document.getElementById('edit_rental_client').value = client;
        document.getElementById('edit_rental_booker').value = booker;
        document.getElementById('edit_rental_vehicle').value = vehicleId;
        document.getElementById('edit_rental_agent').value = agentId;
        document.getElementById('edit_rental_start').value = startDate;
        document.getElementById('edit_rental_end').value = endDate;
        document.getElementById('edit_rental_rate').value = rate;
        document.getElementById('edit_rental_fuel').value = fuel;
        document.getElementById('edit_rental_driver_cost').value = driverCost;
        document.getElementById('edit_rental_driver_name').value = driverName;
        document.getElementById('edit_rental_maintenance').value = maintenance;
        document.getElementById('edit_rental_status').value = status;
        document.getElementById('edit_rental_notes').value = notes;
    }}
    </script>
    '''

    return render_with_base("Short-term Rentals", rentals_content)


# ================ AGENTS MANAGEMENT ================
@app.route('/agents', methods=['GET', 'POST'])
def agents():
    if not logged():
        return redirect('/')

    conn = get_db_connection()

    if request.method == 'POST':
        action = request.form.get('action', 'add')

        if action == 'add':
            conn.execute('''
                         INSERT INTO agents (name, phone, email, commission_percentage, status)
                         VALUES (?, ?, ?, ?, ?)
                         ''', (
                             request.form['name'],
                             request.form.get('phone', ''),
                             request.form.get('email', ''),
                             float(request.form.get('commission_percentage', 20.0)),
                             request.form.get('status', 'Active')
                         ))
            conn.commit()
            conn.close()
            return redirect('/agents?success=added')

        elif action == 'edit':
            conn.execute('''
                         UPDATE agents
                         SET name=?,
                             phone=?,
                             email=?,
                             commission_percentage=?,
                             status=?
                         WHERE id = ?
                         ''', (
                             request.form['name'],
                             request.form.get('phone', ''),
                             request.form.get('email', ''),
                             float(request.form.get('commission_percentage', 20.0)),
                             request.form.get('status', 'Active'),
                             request.form['id']
                         ))
            conn.commit()
            conn.close()
            return redirect('/agents?success=updated')

        elif action == 'delete':
            conn.execute('DELETE FROM agents WHERE id=?', (request.form['id'],))
            conn.commit()
            conn.close()
            return redirect('/agents?success=deleted')

    # Get all agents with commission summary
    agents_list = conn.execute('''
                               SELECT a.*,
                                      (SELECT COUNT(*) FROM short_term_rentals WHERE agent_id = a.id)              as rental_count,
                                      (SELECT SUM(agent_commission)
                                       FROM short_term_rentals
                                       WHERE agent_id = a.id)                                                      as total_commission
                               FROM agents a
                               ORDER BY a.status DESC, a.name ASC
                               ''').fetchall()

    conn.close()

    # Check for success message
    success_message = ''
    success = request.args.get('success')
    if success == 'added':
        success_message = '<div class="alert alert-success alert-dismissible fade show">Agent added successfully!<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
    elif success == 'updated':
        success_message = '<div class="alert alert-success alert-dismissible fade show">Agent updated successfully!<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
    elif success == 'deleted':
        success_message = '<div class="alert alert-success alert-dismissible fade show">Agent deleted successfully!<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'

    agents_content = f'''
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h4 class="fw-bold mb-1"><i class="bi bi-person-badge me-2"></i>Agents Management</h4>
            <p class="text-muted mb-0">Manage booking agents with 20% commission on short-term rentals</p>
        </div>
        <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addAgentModal">
            <i class="bi bi-plus-circle me-1"></i>Add Agent
        </button>
    </div>

    {success_message}

    <!-- Agents Table -->
    <div class="card">
        <div class="card-header">
            <h6 class="mb-0">All Agents ({len(agents_list)})</h6>
        </div>
        <div class="card-body">
    '''

    if agents_list:
        agents_content += '''
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Agent Name</th>
                            <th>Contact Info</th>
                            <th>Commission %</th>
                            <th>Rentals</th>
                            <th>Total Commission</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        '''

        for agent in agents_list:
            if agent['status'] == 'Active':
                status_badge = '<span class="badge bg-success">Active</span>'
            elif agent['status'] == 'Inactive':
                status_badge = '<span class="badge bg-secondary">Inactive</span>'
            else:
                status_badge = f'<span class="badge bg-warning">{agent["status"]}</span>'

            total_commission = agent['total_commission'] or 0

            agents_content += f'''
                <tr>
                    <td><strong>{agent['name']}</strong></td>
                    <td>
                        <small>{agent['phone'] or 'No phone'}</small><br>
                        <small>{agent['email'] or 'No email'}</small>
                    </td>
                    <td><span class="badge bg-info">{agent['commission_percentage']}%</span></td>
                    <td>{agent['rental_count']}</td>
                    <td><strong>PKR {total_commission:,.2f}</strong></td>
                    <td>{status_badge}</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button type="button" class="btn btn-outline-warning" data-bs-toggle="modal" data-bs-target="#editAgentModal" 
                                    onclick="loadAgentData({agent['id']}, '{agent['name']}', '{agent['phone'] or ''}', 
                                    '{agent['email'] or ''}', {agent['commission_percentage']}, '{agent['status']}')" title="Edit">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <form method="POST" style="display:inline">
                                <input type="hidden" name="action" value="delete">
                                <input type="hidden" name="id" value="{agent['id']}">
                                <button type="submit" class="btn btn-outline-danger" 
                                        onclick="return confirm('Delete agent {agent["name"]}?')"
                                        title="Delete">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </form>
                        </div>
                    </td>
                </tr>
            '''

        agents_content += '''
                    </tbody>
                </table>
            </div>
        '''
    else:
        agents_content += '''
            <div class="text-center py-5">
                <i class="bi bi-person-badge text-muted" style="font-size: 3rem;"></i>
                <h5 class="mt-3 text-muted">No agents found</h5>
                <p class="text-muted">Add your first booking agent</p>
                <button type="button" class="btn btn-primary mt-2" data-bs-toggle="modal" data-bs-target="#addAgentModal">
                    <i class="bi bi-plus-circle me-1"></i>Add Agent
                </button>
            </div>
        '''

    agents_content += f'''
        </div>
    </div>

    <!-- Add Agent Modal -->
    <div class="modal fade" id="addAgentModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Add New Agent</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <form method="POST">
                    <input type="hidden" name="action" value="add">
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">Agent Name *</label>
                            <input type="text" name="name" class="form-control" placeholder="Farhan" required>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Phone</label>
                                <input type="tel" name="phone" class="form-control" placeholder="+92-300-123-4567">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Email</label>
                                <input type="email" name="email" class="form-control" placeholder="agent@example.com">
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Commission Percentage (%)</label>
                            <div class="input-group">
                                <input type="number" step="0.1" min="0" max="100" name="commission_percentage" 
                                       class="form-control" value="20.0" required>
                                <span class="input-group-text">%</span>
                            </div>
                            <small class="text-muted">Standard is 20% of profit from short-term rentals</small>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Status</label>
                            <select name="status" class="form-select">
                                <option value="Active">Active</option>
                                <option value="Inactive">Inactive</option>
                            </select>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-primary">Add Agent</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- Edit Agent Modal -->
    <div class="modal fade" id="editAgentModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Edit Agent</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <form method="POST">
                    <input type="hidden" name="action" value="edit">
                    <input type="hidden" name="id" id="edit_agent_id">
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">Agent Name *</label>
                            <input type="text" name="name" id="edit_agent_name" class="form-control" required>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Phone</label>
                                <input type="tel" name="phone" id="edit_agent_phone" class="form-control">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Email</label>
                                <input type="email" name="email" id="edit_agent_email" class="form-control">
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Commission Percentage (%)</label>
                            <div class="input-group">
                                <input type="number" step="0.1" min="0" max="100" name="commission_percentage" 
                                       id="edit_agent_commission" class="form-control" required>
                                <span class="input-group-text">%</span>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Status</label>
                            <select name="status" id="edit_agent_status" class="form-select">
                                <option value="Active">Active</option>
                                <option value="Inactive">Inactive</option>
                            </select>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-primary">Update Agent</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script>
    function loadAgentData(id, name, phone, email, commission, status) {{
        document.getElementById('edit_agent_id').value = id;
        document.getElementById('edit_agent_name').value = name;
        document.getElementById('edit_agent_phone').value = phone;
        document.getElementById('edit_agent_email').value = email;
        document.getElementById('edit_agent_commission').value = commission;
        document.getElementById('edit_agent_status').value = status;
    }}
    </script>
    '''

    return render_with_base("Agents", agents_content)


# ================ INVESTOR PAYMENTS ================
@app.route('/investor-payments', methods=['GET', 'POST'])
def investor_payments():
    if not logged():
        return redirect('/')

    conn = get_db_connection()

    if request.method == 'POST':
        action = request.form.get('action', 'add')

        if action == 'add':
            conn.execute('''
                         INSERT INTO investor_payments (investor_id, vehicle_id, amount, payment_date,
                                                        cheque_no, description, month_year, status,
                                                        payment_method, notes)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                         ''', (
                             request.form['investor_id'],
                             request.form.get('vehicle_id') or None,
                             float(request.form['amount']),
                             request.form['payment_date'],
                             request.form.get('cheque_no', ''),
                             request.form.get('description', ''),
                             request.form.get('month_year', ''),
                             request.form.get('status', 'Pending'),
                             request.form.get('payment_method', 'Cheque'),
                             request.form.get('notes', '')
                         ))
            conn.commit()
            conn.close()
            return redirect('/investor-payments?success=added')

        elif action == 'edit':
            conn.execute('''
                         UPDATE investor_payments
                         SET investor_id=?,
                             vehicle_id=?,
                             amount=?,
                             payment_date=?,
                             cheque_no=?,
                             description=?,
                             month_year=?,
                             status=?,
                             payment_method=?,
                             notes=?
                         WHERE id = ?
                         ''', (
                             request.form['investor_id'],
                             request.form.get('vehicle_id') or None,
                             float(request.form['amount']),
                             request.form['payment_date'],
                             request.form.get('cheque_no', ''),
                             request.form.get('description', ''),
                             request.form.get('month_year', ''),
                             request.form.get('status', 'Pending'),
                             request.form.get('payment_method', 'Cheque'),
                             request.form.get('notes', ''),
                             request.form['id']
                         ))
            conn.commit()
            conn.close()
            return redirect('/investor-payments?success=updated')

        elif action == 'update_status':
            conn.execute('''
                         UPDATE investor_payments
                         SET status = ?
                         WHERE id = ?
                         ''', (request.form['status'], request.form['id']))
            conn.commit()
            conn.close()
            return redirect('/investor-payments?success=updated')

        elif action == 'delete':
            conn.execute('DELETE FROM investor_payments WHERE id=?', (request.form['id'],))
            conn.commit()
            conn.close()
            return redirect('/investor-payments?success=deleted')

    # Get all investor payments
    payments_list = conn.execute('''
                                 SELECT ip.*, inv.name as investor_name, v.reg as vehicle_reg
                                 FROM investor_payments ip
                                          LEFT JOIN investors inv ON ip.investor_id = inv.id
                                          LEFT JOIN vehicles v ON ip.vehicle_id = v.id
                                 ORDER BY ip.payment_date DESC
                                 ''').fetchall()

    # Get investors for dropdown
    investors_list = conn.execute('SELECT id, name FROM investors WHERE status = "Active" ORDER BY name').fetchall()

    # Get vehicles for dropdown
    vehicles_list = conn.execute('SELECT id, reg FROM vehicles ORDER BY reg').fetchall()

    conn.close()

    # Build dropdowns
    investor_options = '<option value="">Select Investor</option>'
    investor_options += ''.join([f'<option value="{i["id"]}">{i["name"]}</option>' for i in investors_list])

    vehicle_options = '<option value="">Select Vehicle (Optional)</option>'
    vehicle_options += ''.join([f'<option value="{v["id"]}">{v["reg"]}</option>' for v in vehicles_list])

    # Check for success message
    success_message = ''
    success = request.args.get('success')
    if success == 'added':
        success_message = '<div class="alert alert-success alert-dismissible fade show">Payment recorded successfully!<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
    elif success == 'updated':
        success_message = '<div class="alert alert-success alert-dismissible fade show">Payment updated successfully!<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
    elif success == 'deleted':
        success_message = '<div class="alert alert-success alert-dismissible fade show">Payment deleted successfully!<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'

    # Calculate summary
    total_paid = sum(p['amount'] for p in payments_list if p['status'] == 'Completed')
    total_pending = sum(p['amount'] for p in payments_list if p['status'] == 'Pending')

    payments_content = f'''
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h4 class="fw-bold mb-1"><i class="bi bi-cash-coin me-2"></i>Investor Payments</h4>
            <p class="text-muted mb-0">Record and track payments to vehicle owners/investors</p>
        </div>
        <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addPaymentModal">
            <i class="bi bi-plus-circle me-1"></i>Record Payment
        </button>
    </div>

    {success_message}

    <!-- Summary Cards -->
    <div class="row mb-4">
        <div class="col-md-4">
            <div class="stat-card">
                <i class="bi bi-cash text-success"></i>
                <h3 class="fw-bold">PKR {total_paid:,.0f}</h3>
                <p class="text-muted mb-0">Total Paid</p>
            </div>
        </div>
        <div class="col-md-4">
            <div class="stat-card">
                <i class="bi bi-clock-history text-warning"></i>
                <h3 class="fw-bold">PKR {total_pending:,.0f}</h3>
                <p class="text-muted mb-0">Pending Payments</p>
            </div>
        </div>
        <div class="col-md-4">
            <div class="stat-card">
                <i class="bi bi-receipt text-info"></i>
                <h3 class="fw-bold">{len(payments_list)}</h3>
                <p class="text-muted mb-0">Total Records</p>
            </div>
        </div>
    </div>

    <!-- Payments Table -->
    <div class="card">
        <div class="card-header">
            <h6 class="mb-0">Payment Records</h6>
        </div>
        <div class="card-body">
    '''

    if payments_list:
        payments_content += '''
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Investor</th>
                            <th>Vehicle</th>
                            <th>Amount</th>
                            <th>Cheque No</th>
                            <th>Description</th>
                            <th>Month/Year</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        '''

        for payment in payments_list:
            if payment['status'] == 'Completed':
                status_badge = '<span class="badge bg-success">Completed</span>'
            elif payment['status'] == 'Pending':
                status_badge = '<span class="badge bg-warning">Pending</span>'
            else:
                status_badge = f'<span class="badge bg-secondary">{payment["status"]}</span>'

            payments_content += f'''
                <tr>
                    <td>{payment['payment_date']}</td>
                    <td><strong>{payment['investor_name']}</strong></td>
                    <td>{payment['vehicle_reg'] or 'Multiple/N/A'}</td>
                    <td><strong>PKR {payment['amount']:,.2f}</strong></td>
                    <td>{payment['cheque_no'] or 'N/A'}</td>
                    <td><small>{payment['description'] or 'No description'}</small></td>
                    <td>{payment['month_year'] or 'N/A'}</td>
                    <td>{status_badge}</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button type="button" class="btn btn-outline-warning" data-bs-toggle="modal" data-bs-target="#editPaymentModal" 
                                    onclick="loadPaymentData({payment['id']}, {payment['investor_id']}, {payment['vehicle_id'] or 'null'}, 
                                    {payment['amount']}, '{payment['payment_date']}', '{payment['cheque_no'] or ''}', 
                                    '{payment['description'] or ''}', '{payment['month_year'] or ''}', '{payment['status']}', 
                                    '{payment['payment_method'] or 'Cheque'}', '{payment['notes'] or ''}')" title="Edit">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <form method="POST" style="display:inline">
                                <input type="hidden" name="action" value="delete">
                                <input type="hidden" name="id" value="{payment['id']}">
                                <button type="submit" class="btn btn-outline-danger" 
                                        onclick="return confirm('Delete this payment record?')"
                                        title="Delete">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </form>
                        </div>
                    </td>
                </tr>
            '''

        payments_content += '''
                    </tbody>
                </table>
            </div>
        '''
    else:
        payments_content += '''
            <div class="text-center py-5">
                <i class="bi bi-cash-coin text-muted" style="font-size: 3rem;"></i>
                <h5 class="mt-3 text-muted">No payment records</h5>
                <p class="text-muted">Record your first investor payment</p>
                <button type="button" class="btn btn-primary mt-2" data-bs-toggle="modal" data-bs-target="#addPaymentModal">
                    <i class="bi bi-plus-circle me-1"></i>Record Payment
                </button>
            </div>
        '''

    payments_content += f'''
        </div>
    </div>

    <!-- Add Payment Modal -->
    <div class="modal fade" id="addPaymentModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Record Investor Payment</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <form method="POST">
                    <input type="hidden" name="action" value="add">
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">Investor *</label>
                            <select name="investor_id" class="form-select" required>
                                {investor_options}
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Vehicle (Optional)</label>
                            <select name="vehicle_id" class="form-select">
                                {vehicle_options}
                            </select>
                            <small class="text-muted">Leave blank for multiple vehicle payments</small>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Amount (PKR) *</label>
                            <input type="number" step="0.01" name="amount" class="form-control" required placeholder="0.00">
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Payment Date *</label>
                                <input type="date" name="payment_date" class="form-control" required value="{date.today().isoformat()}">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Cheque Number</label>
                                <input type="text" name="cheque_no" class="form-control" placeholder="00003207">
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Description</label>
                            <input type="text" name="description" class="form-control" placeholder="Payment for the month of Nov 2025">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Month/Year</label>
                            <input type="text" name="month_year" class="form-control" placeholder="Nov 2025">
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Payment Method</label>
                                <select name="payment_method" class="form-select">
                                    <option value="Cheque">Cheque</option>
                                    <option value="Cash">Cash</option>
                                    <option value="Bank Transfer">Bank Transfer</option>
                                </select>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Status</label>
                                <select name="status" class="form-select">
                                    <option value="Pending">Pending</option>
                                    <option value="Completed">Completed</option>
                                </select>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Notes</label>
                            <textarea name="notes" class="form-control" rows="2" placeholder="Additional notes..."></textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-primary">Record Payment</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- Edit Payment Modal -->
    <div class="modal fade" id="editPaymentModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Edit Investor Payment</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <form method="POST">
                    <input type="hidden" name="action" value="edit">
                    <input type="hidden" name="id" id="edit_payment_id">
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">Investor *</label>
                            <select name="investor_id" id="edit_payment_investor" class="form-select" required>
                                {investor_options}
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Vehicle (Optional)</label>
                            <select name="vehicle_id" id="edit_payment_vehicle" class="form-select">
                                {vehicle_options}
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Amount (PKR) *</label>
                            <input type="number" step="0.01" name="amount" id="edit_payment_amount" class="form-control" required>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Payment Date *</label>
                                <input type="date" name="payment_date" id="edit_payment_date" class="form-control" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Cheque Number</label>
                                <input type="text" name="cheque_no" id="edit_payment_cheque" class="form-control">
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Description</label>
                            <input type="text" name="description" id="edit_payment_desc" class="form-control">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Month/Year</label>
                            <input type="text" name="month_year" id="edit_payment_month" class="form-control">
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Payment Method</label>
                                <select name="payment_method" id="edit_payment_method" class="form-select">
                                    <option value="Cheque">Cheque</option>
                                    <option value="Cash">Cash</option>
                                    <option value="Bank Transfer">Bank Transfer</option>
                                </select>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Status</label>
                                <select name="status" id="edit_payment_status" class="form-select">
                                    <option value="Pending">Pending</option>
                                    <option value="Completed">Completed</option>
                                </select>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Notes</label>
                            <textarea name="notes" id="edit_payment_notes" class="form-control" rows="2"></textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-primary">Update Payment</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script>
    function loadPaymentData(id, investorId, vehicleId, amount, date, cheque, desc, month, status, method, notes) {{
        document.getElementById('edit_payment_id').value = id;
        document.getElementById('edit_payment_investor').value = investorId;
        document.getElementById('edit_payment_vehicle').value = vehicleId;
        document.getElementById('edit_payment_amount').value = amount;
        document.getElementById('edit_payment_date').value = date;
        document.getElementById('edit_payment_cheque').value = cheque;
        document.getElementById('edit_payment_desc').value = desc;
        document.getElementById('edit_payment_month').value = month;
        document.getElementById('edit_payment_status').value = status;
        document.getElementById('edit_payment_method').value = method;
        document.getElementById('edit_payment_notes').value = notes;
    }}
    </script>
    '''

    return render_with_base("Investor Payments", payments_content)


# ================ AGENT COMMISSIONS ================
@app.route('/agent-commissions')
def agent_commissions_page():
    if not logged():
        return redirect('/')

    conn = get_db_connection()

    # Get all agent commissions
    commissions = conn.execute('''
                               SELECT ac.*, a.name as agent_name, str.client_name, str.total_amount, str.profit
                               FROM agent_commissions ac
                                        LEFT JOIN agents a ON ac.agent_id = a.id
                                        LEFT JOIN short_term_rentals str ON ac.rental_id = str.id
                               ORDER BY ac.status, ac.created_at DESC
                               ''').fetchall()

    conn.close()

    # Calculate summary
    total_commission = sum(c['amount'] for c in commissions)
    total_paid = sum(c['amount'] for c in commissions if c['status'] == 'Paid')
    total_pending = sum(c['amount'] for c in commissions if c['status'] == 'Pending')

    commissions_content = f'''
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h4 class="fw-bold mb-1"><i class="bi bi-percent me-2"></i>Agent Commissions</h4>
            <p class="text-muted mb-0">Track and manage 20% commission payments to booking agents</p>
        </div>
    </div>

    <!-- Summary Cards -->
    <div class="row mb-4">
        <div class="col-md-4">
            <div class="stat-card">
                <i class="bi bi-cash text-success"></i>
                <h3 class="fw-bold">PKR {total_paid:,.0f}</h3>
                <p class="text-muted mb-0">Total Paid</p>
            </div>
        </div>
        <div class="col-md-4">
            <div class="stat-card">
                <i class="bi bi-clock-history text-warning"></i>
                <h3 class="fw-bold">PKR {total_pending:,.0f}</h3>
                <p class="text-muted mb-0">Pending Commissions</p>
            </div>
        </div>
        <div class="col-md-4">
            <div class="stat-card">
                <i class="bi bi-receipt text-info"></i>
                <h3 class="fw-bold">{len(commissions)}</h3>
                <p class="text-muted mb-0">Total Records</p>
            </div>
        </div>
    </div>

    <!-- Commissions Table -->
    <div class="card">
        <div class="card-header">
            <h6 class="mb-0">Commission Records</h6>
        </div>
        <div class="card-body">
    '''

    if commissions:
        commissions_content += '''
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Agent</th>
                            <th>Client/Rental</th>
                            <th>Rental Profit</th>
                            <th>Commission %</th>
                            <th>Commission Amount</th>
                            <th>Payment Date</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        '''

        for commission in commissions:
            if commission['status'] == 'Paid':
                status_badge = '<span class="badge bg-success">Paid</span>'
            elif commission['status'] == 'Pending':
                status_badge = '<span class="badge bg-warning">Pending</span>'
            else:
                status_badge = f'<span class="badge bg-secondary">{commission["status"]}</span>'

            commissions_content += f'''
                <tr>
                    <td><strong>{commission['agent_name']}</strong></td>
                    <td>{commission['client_name'] or 'N/A'}</td>
                    <td>PKR {commission['profit'] or '0':,.2f}</td>
                    <td><span class="badge bg-info">{commission['commission_percentage']}%</span></td>
                    <td><strong>PKR {commission['amount']:,.2f}</strong></td>
                    <td>{commission['payment_date'] or 'Not Paid'}</td>
                    <td>{status_badge}</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <form method="POST" action="/update-commission-status" style="display:inline">
                                <input type="hidden" name="commission_id" value="{commission['id']}">
                                <button type="submit" name="status" value="Paid" 
                                        class="btn btn-outline-success" title="Mark as Paid">
                                    <i class="bi bi-check-circle"></i>
                                </button>
                            </form>
                        </div>
                    </td>
                </tr>
            '''

        commissions_content += '''
                    </tbody>
                </table>
            </div>
        '''
    else:
        commissions_content += '''
            <div class="text-center py-5">
                <i class="bi bi-percent text-muted" style="font-size: 3rem;"></i>
                <h5 class="mt-3 text-muted">No commission records</h5>
                <p class="text-muted">Agent commissions are automatically created when short-term rentals are booked</p>
            </div>
        '''

    commissions_content += f'''
        </div>
    </div>
    '''

    return render_with_base("Agent Commissions", commissions_content)


@app.route('/update-commission-status', methods=['POST'])
def update_commission_status():
    if not logged():
        return redirect('/')

    commission_id = request.form.get('commission_id')
    status = request.form.get('status')

    conn = get_db_connection()
    conn.execute('''
                 UPDATE agent_commissions
                 SET status       = ?,
                     payment_date = ?
                 WHERE id = ?
                 ''', (status, date.today().isoformat(), commission_id))
    conn.commit()
    conn.close()

    return redirect('/agent-commissions?success=updated')


# ================ PROFIT & LOSS REPORT ================
@app.route('/reports/profit-loss')
def profit_loss_report():
    if not logged():
        return redirect('/')

    conn = get_db_connection()

    # Get vehicle profit summary
    vehicle_summary = conn.execute('''
                                   SELECT SUM(monthly_rent_from_company)                           as total_company_rent,
                                          SUM(monthly_pay_to_investor)                             as total_investor_payment,
                                          SUM(monthly_rent_from_company - monthly_pay_to_investor) as total_profit,
                                          COUNT(*)                                                 as vehicle_count
                                   FROM vehicles
                                   WHERE company_id IS NOT NULL
                                     AND investor_id IS NOT NULL
                                   ''').fetchone()

    # Get short-term rental summary
    short_term_summary = conn.execute('''
                                      SELECT SUM(total_amount)                                  as total_revenue,
                                             SUM(investor_cost + driver_cost + fuel_expense +
                                                 (total_amount * maintenance_percentage / 100)) as total_costs,
                                             SUM(profit)                                        as total_profit,
                                             SUM(agent_commission)                              as total_agent_commission,
                                             COUNT(*)                                           as rental_count
                                      FROM short_term_rentals
                                      WHERE status = 'Active'
                                      ''').fetchone()

    # Get investor payments
    investor_payments = \
    conn.execute('SELECT SUM(amount) as total FROM investor_payments WHERE status = "Completed"').fetchone()[0] or 0

    conn.close()

    # Calculate totals
    total_revenue = (vehicle_summary['total_company_rent'] or 0) + (short_term_summary['total_revenue'] or 0)
    total_investor_costs = investor_payments
    total_agent_commissions = short_term_summary['total_agent_commission'] or 0

    total_costs = total_investor_costs + total_agent_commissions
    net_profit = total_revenue - total_costs

    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

    report_content = f'''
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h4 class="fw-bold mb-1"><i class="bi bi-graph-up me-2"></i>Profit & Loss Report</h4>
            <p class="text-muted mb-0">Financial summary of AA Transportation operations</p>
        </div>
    </div>

    <!-- Summary Cards -->
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="stat-card">
                <i class="bi bi-cash-coin text-primary"></i>
                <h3 class="fw-bold">PKR {total_revenue:,.0f}</h3>
                <p class="text-muted mb-0">Total Revenue</p>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card">
                <i class="bi bi-currency-exchange text-warning"></i>
                <h3 class="fw-bold">PKR {total_costs:,.0f}</h3>
                <p class="text-muted mb-0">Total Costs</p>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card">
                <i class="bi bi-graph-up-arrow text-success"></i>
                <h3 class="fw-bold">PKR {net_profit:,.0f}</h3>
                <p class="text-muted mb-0">Net Profit</p>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card">
                <i class="bi bi-percent text-info"></i>
                <h3 class="fw-bold">{profit_margin:.1f}%</h3>
                <p class="text-muted mb-0">Profit Margin</p>
            </div>
        </div>
    </div>

    <!-- Detailed Breakdown -->
    <div class="row">
        <div class="col-md-6">
            <div class="card mb-4">
                <div class="card-header">
                    <h6 class="mb-0">Revenue Breakdown</h6>
                </div>
                <div class="card-body">
                    <table class="table">
                        <tr>
                            <td>Corporate Rentals (Monthly)</td>
                            <td class="text-end">PKR {vehicle_summary['total_company_rent'] or 0:,.2f}</td>
                        </tr>
                        <tr>
                            <td>Short-term Rentals (Daily)</td>
                            <td class="text-end">PKR {short_term_summary['total_revenue'] or 0:,.2f}</td>
                        </tr>
                        <tr class="table-light">
                            <th>Total Revenue</th>
                            <th class="text-end">PKR {total_revenue:,.2f}</th>
                        </tr>
                    </table>
                </div>
            </div>
        </div>
        
        <div class="col-md-6">
            <div class="card mb-4">
                <div class="card-header">
                    <h6 class="mb-0">Cost Breakdown</h6>
                </div>
                <div class="card-body">
                    <table class="table">
                        <tr>
                            <td>Investor Payments</td>
                            <td class="text-end">PKR {total_investor_costs:,.2f}</td>
                        </tr>
                        <tr>
                            <td>Agent Commissions (20%)</td>
                            <td class="text-end">PKR {total_agent_commissions:,.2f}</td>
                        </tr>
                        <tr class="table-light">
                            <th>Total Costs</th>
                            <th class="text-end">PKR {total_costs:,.2f}</th>
                        </tr>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- Profit Calculation -->
    <div class="card">
        <div class="card-header">
            <h6 class="mb-0">Profit Calculation</h6>
        </div>
        <div class="card-body">
            <div class="row text-center">
                <div class="col-md-6">
                    <h5 class="fw-bold">Corporate Rentals</h5>
                    <p class="mb-1">Profit = Company Rent - Investor Payment</p>
                    <p class="mb-0"><strong>PKR {vehicle_summary['total_profit'] or 0:,.2f}</strong></p>
                </div>
                <div class="col-md-6">
                    <h5 class="fw-bold">Short-term Rentals</h5>
                    <p class="mb-1">Profit = Total - (Investor Cost + Driver + Fuel + Maintenance) - Agent Commission</p>
                    <p class="mb-0"><strong>PKR {(short_term_summary['total_profit'] or 0) - (short_term_summary['total_agent_commission'] or 0):,.2f}</strong></p>
                </div>
            </div>
            <hr>
            <div class="text-center">
                <h4 class="fw-bold text-success">Total Net Profit: PKR {net_profit:,.2f}</h4>
                <p class="text-muted">After all costs and commissions</p>
            </div>
        </div>
    </div>
    '''

    return render_with_base("Profit & Loss Report", report_content)


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('aa_transportation.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/contracts')
def contracts_page():
    """Main contracts page"""
    if not logged():
        return redirect('/')

    conn = get_db_connection()

    # Get all companies
    companies = conn.execute('SELECT * FROM companies WHERE status = "Active" ORDER BY name').fetchall()

    # Get all investors
    investors = conn.execute('SELECT * FROM investors WHERE status = "Active" ORDER BY name').fetchall()

    conn.close()

    return render_template_string(CONTRACTS_PAGE,
                                  companies=companies,
                                  investors=investors,
                                  session=session,
                                  request=request)


@app.route('/contracts/company-agreement')
def company_agreement():
    """Generate company rental agreement with AUTO-FIX for database error"""
    if not logged():
        return redirect('/')

    company_id = request.args.get('company_id')
    if not company_id:
        return redirect('/contracts')

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    company = conn.execute('SELECT * FROM companies WHERE id = ?', (company_id,)).fetchone()

    # --- ERROR FIXING LOGIC ---
    vehicle = None
    if company:
        try:
            # Hum koshish karenge gari ka data nikalne ki
            vehicle = conn.execute('SELECT * FROM vehicles WHERE assigned_to = ?', (company['name'],)).fetchone()
        except sqlite3.OperationalError:
            # Agar 'assigned_to' column database mein nahi hai, toh Error nahi aayega
            # Bas vehicle ki jagah agreement mein khali lines (______) aa jayengi
            vehicle = None
    
    conn.close()

    if not company:
        return "Company not found", 404

    # --- LIVE DATE LOGIC (Always Current) ---
    today = datetime.now() 
    day = today.day
    if 11 <= day <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    
    day_str = f"{day}{suffix}"
    month_str = today.strftime("%B")
    year_str = today.strftime("%Y")

    agreement_no = str(int(datetime.now().timestamp()))[-6:]

    return render_template_string(COMPANY_AGREEMENT_TEMPLATE,
                                  company=company,
                                  vehicle=vehicle,
                                  day_str=day_str,
                                  month_str=month_str,
                                  year_str=year_str,
                                  agreement_no=agreement_no)

@app.route('/contracts/vendor-agreement') # Form submit wala purana rasta
@app.route('/print_agreement/<int:id>')   # Direct ID wala rasta
def print_agreement(id=None):
    if id is None:
        # Agar form se aaya hai toh investor_id nikal lo
        id = request.args.get('investor_id')
    
    if not id:
        return redirect('/contracts')

    conn = get_db_connection()

@app.route('/generate_investor_invoice/<int:investor_id>')
def generate_investor_invoice(investor_id):
    if 'user' not in session: return redirect('/')
    
    conn = sqlite3.connect(DB)
    # Row factory lazmi hai taake v['column_name'] kaam kare
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    try:
        # 1. Investor details
        cur.execute("SELECT * FROM investors WHERE id=?", (investor_id,))
        investor = cur.fetchone()
        
        if not investor:
            return "Investor database mein nahi mila!", 404
        
        # 2. Vehicles fetch karein
        cur.execute("SELECT * FROM vehicles WHERE investor_id=?", (investor_id,))
        vehicles_rows = cur.fetchall()
        
        total_rent = 0
        formatted_vehicles = []
        
        # 3. Data ko saaf karke template ke liye tayyar karein
        for v in vehicles_rows:
            # Investor payout column check karein
            v_rent = 0
            if 'monthly_pay_to_investor' in v.keys():
                v_rent = v['monthly_pay_to_investor'] or 0
            
            total_rent += v_rent
            
            # Gaari ka naam aur details
            v_make = v['make'] if 'make' in v.keys() else 'Vehicle'
            v_variant = v['variant'] if 'variant' in v.keys() else ''
            v_reg = v['reg'] if 'reg' in v.keys() else 'N/A'
            
            formatted_vehicles.append({
                'company_name': v_make,
                'car_model': v_variant,
                'reg_no': v_reg,
                'monthly_rent': v_rent
            })
        
        # 4. Dates logic
        today = datetime.now()
        current_date = today.strftime("%d-%b-%y")
        start_date = today.replace(day=1).strftime("%b 1, %Y")
        next_month = today.replace(day=28) + timedelta(days=4)
        last_day = next_month - timedelta(days=next_month.day)
        end_date = last_day.strftime("%b %d, %Y")
        
        conn.close()
        
        # Yahan humne INVESTOR_INVOICE_TEMPLATE istemaal kiya hai
        return render_template_string(INVESTOR_INVOICE_TEMPLATE, 
                                      investor=investor, 
                                      vehicles=formatted_vehicles, 
                                      total_rent=total_rent,
                                      current_date=current_date,
                                      start_date=start_date,
                                      end_date=end_date)
                                      
    except Exception as e:
        if conn: conn.close()
        return f"Bhae error ye hai: {str(e)}", 500
@app.route('/generate_company_invoice/<int:company_id>')
def generate_company_invoice(company_id):
    if not logged(): return redirect('/')
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    try:
        company = conn.execute("SELECT * FROM companies WHERE id=?", (company_id,)).fetchone()
        vehicles = conn.execute("SELECT * FROM vehicles WHERE company_id=?", (company_id,)).fetchall()
        
        total_revenue = sum(v['monthly_rent_from_company'] or 0 for v in vehicles)
        
        today = datetime.now()
        current_date = today.strftime("%d-%b-%y")
        start_date = today.replace(day=1).strftime("%b 1, %Y")
        next_month = today.replace(day=28) + timedelta(days=4)
        last_day = next_month - timedelta(days=next_month.day)
        end_date = last_day.strftime("%b %d, %Y")
        
        conn.close()
        return render_template_string(COMPANY_INVOICE_TEMPLATE, 
                                      company=company, vehicles=vehicles, 
                                      total_revenue=total_revenue, current_date=current_date,
                                      start_date=start_date, end_date=end_date)
    except Exception as e:
        return f"Error: {str(e)}", 500
# ================ RUN APP ================
if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🚗 AA Transportation - Vehicle Rental Management System")
    print("=" * 70)
    print("✅ Database initialized with AA Transportation business model")
    print("✅ Investors → AA Transportation → Companies model implemented")
    print("✅ Short-term rentals with agent commissions (20%)")
    print("✅ FULL CRUD operations with working edit modals")
    print("✅ Investor payments tracking with cheque numbers")
    print("✅ Profit calculation for both corporate and short-term rentals")
    print(f"🌐 Access URL: http://localhost:5000")
    print("🔑 Login: admin / admin")
    print("💰 Currency: PKR (Pakistani Rupees)")
    print("🏢 Business Model: Vehicle Owners → AA Transportation → Corporate Clients")
    print("👨‍💼 Agents: Farhan, Tariq, Shahzaib with 20% commission")
    print("📊 Reports: Profit & Loss with detailed breakdown")
    print("💳 Payments: Investor payment tracking with status")
    print("=" * 70 + "\n")

    try:
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Try changing port: app.run(port=5001)")
