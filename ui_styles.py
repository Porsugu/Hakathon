"""
UI Styles for Personal Learning OS
Contains all CSS styling and UI components
"""
import streamlit as st

def get_custom_css():
    """Return custom CSS for the application"""
    return """
    <style>
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        }

        .stat-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            text-align: center;
            min-width: 140px;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            transition: transform 0.3s ease;
        }

        .stat-box:hover {
            transform: translateY(-3px);
        }

        .api-status {
            position: fixed;
            top: 10px;
            right: 10px;
            background: #28a745;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.8em;
            z-index: 1000;
        }

        .api-status.error {
            background: #dc3545;
        }

        .mission-card {
            background: #f8f9fc;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
            transition: all 0.3s ease;
            border-left: 5px solid #28a745;
        }

        .completed {
            border-left-color: #28a745;
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        }

        .current {
            border-left-color: #ffc107;
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        }

        .pending {
            border-left-color: #6c757d;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        }

        .success-message {
            background: #d4edda;
            color: #155724;
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #28a745;
            margin: 1rem 0;
        }
    </style>
    """

def render_header(api_connected: bool = False):
    """Render main application header with API status"""
    status_text = "🟢 AI Connected" if api_connected else "🔴 API Error"
    status_class = "" if api_connected else "error"

    return f'''
    <div class="api-status {status_class}">{status_text}</div>
    <div class="main-header">
        <h1>🧠 Personal Learning OS</h1>
        <p>AI-Powered Learning Companion</p>
        <small>Modular Production Architecture</small>
    </div>
    '''

def render_stat_box(title: str, value: str, subtitle: str = ""):
    """Render a statistics box"""
    return f'''
    <div class="stat-box">
        <h3>{value}</h3>
        <p>{title}</p>
        <small>{subtitle}</small>
    </div>
    '''
