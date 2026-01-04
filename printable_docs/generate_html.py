#!/usr/bin/env python3
"""
HTML Generator for Printable Documentation
Converts markdown files to print-ready HTML with download and print options
Optimized for black & white printing with code snippets
"""

import os
import markdown
import base64
from pathlib import Path
from datetime import datetime

# Configuration
BASE_DIR = Path(__file__).parent.parent
DOCS_DIR = BASE_DIR
OUTPUT_DIR = Path(__file__).parent / 'html'
OUTPUT_DIR.mkdir(exist_ok=True)

# Documents to convert
DOCUMENTS = [
    # Main Documentation
    {
        'source': 'README.md',
        'output': 'readme.html',
        'title': 'Movie Booking System - README',
        'description': 'Project overview, features, and setup instructions',
        'category': 'Main',
        'priority': 1
    },
    {
        'source': 'DOCUMENTATION_INDEX.md',
        'output': 'documentation_index.html',
        'title': 'Documentation Index',
        'description': 'Complete index of all project documentation',
        'category': 'Main',
        'priority': 2
    },
    {
        'source': 'QUICK_VISUAL_GUIDE.md',
        'output': 'quick_visual_guide.html',
        'title': 'Quick Visual Guide',
        'description': 'Visual guide to the project structure and features',
        'category': 'Main',
        'priority': 3
    },
    
    # Utilities Documentation
    {
        'source': 'UTILITIES_IMPLEMENTATION_GUIDE.md',
        'output': 'utilities_implementation_guide.html',
        'title': 'Utilities Implementation Guide',
        'description': 'Complete guide to rate limiting, caching, and performance monitoring',
        'category': 'Utilities',
        'priority': 1
    },
    {
        'source': 'UTILITIES_GUIDE.md',
        'output': 'utilities_guide.html',
        'title': 'Utilities Guide',
        'description': 'User-friendly utilities documentation with examples',
        'category': 'Utilities',
        'priority': 2
    },
    
    # Email System
    {
        'source': 'EMAIL_SYSTEM_COMPLETE_GUIDE.md',
        'output': 'email_system_guide.html',
        'title': 'Email System Complete Guide',
        'description': 'Complete email system documentation and setup',
        'category': 'Email',
        'priority': 1
    },
    {
        'source': 'email_templates/README.md',
        'output': 'email_templates_readme.html',
        'title': 'Email Templates README',
        'description': 'Email templates structure and usage guide',
        'category': 'Email',
        'priority': 2
    },
    
    # Services & Architecture
    {
        'source': 'services_guide.md',
        'output': 'services_guide.html',
        'title': 'Services Guide',
        'description': 'Backend services, architecture, and API documentation',
        'category': 'Architecture',
        'priority': 1
    },
    {
        'source': 'UNDERSTANDING_CELERY.md',
        'output': 'understanding_celery.html',
        'title': 'Understanding Celery',
        'description': 'Celery task queue and async processing guide',
        'category': 'Architecture',
        'priority': 2
    },
    {
        'source': 'UNDERSTANDING_REDIS.md',
        'output': 'understanding_redis.html',
        'title': 'Understanding Redis',
        'description': 'Redis caching and session management guide',
        'category': 'Architecture',
        'priority': 3
    },
    {
        'source': 'UNDERSTANDING_RAZORPAY.md',
        'output': 'understanding_razorpay.html',
        'title': 'Understanding Razorpay',
        'description': 'Payment gateway integration and implementation',
        'category': 'Architecture',
        'priority': 4
    },
    {
        'source': 'bookings/caching_guide.md',
        'output': 'caching_guide.html',
        'title': 'Caching Guide',
        'description': 'Detailed caching strategies for bookings module',
        'category': 'Architecture',
        'priority': 5
    },
    
    # API & Frontend
    {
        'source': 'js_api_interaction.md',
        'output': 'js_api_interaction.html',
        'title': 'JavaScript API Interaction',
        'description': 'Frontend JavaScript API integration guide',
        'category': 'Frontend',
        'priority': 1
    },
    
    # Interview Preparation
    {
        'source': 'interview/beginner_questions.md',
        'output': 'interview_beginner_questions.html',
        'title': 'Interview - Beginner Questions',
        'description': 'Common beginner-level interview questions and answers',
        'category': 'Interview',
        'priority': 1
    },
    {
        'source': 'interview/interview_questions.md',
        'output': 'interview_questions.html',
        'title': 'Interview Questions',
        'description': 'Comprehensive interview questions for the project',
        'category': 'Interview',
        'priority': 2
    },
    {
        'source': 'interview/technical_deep_dive.md',
        'output': 'interview_technical_deep_dive.html',
        'title': 'Technical Deep Dive',
        'description': 'Advanced technical concepts and deep dive questions',
        'category': 'Interview',
        'priority': 3
    },
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Movie Booking System</title>
    <style>
        /* Screen Styles */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.8;
            color: #000;
            background: #f5f5f5;
            padding: 20px;
            font-size: 12pt;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}
        
        .header {{
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            color: #007bff;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            color: #666;
            font-size: 1.1em;
        }}
        
        .meta {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        .meta-info {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .actions {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s;
        }}
        
        .btn-primary {{
            background: #007bff;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #0056b3;
        }}
        
        .btn-success {{
            background: #28a745;
            color: white;
        }}
        
        .btn-success:hover {{
            background: #218838;
        }}
        
        .btn-secondary {{
            background: #6c757d;
            color: white;
        }}
        
        .btn-secondary:hover {{
            background: #5a6268;
        }}
        
        .content {{
            margin-top: 30px;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            color: #2c3e50;
        }}
        
        h1 {{ font-size: 2em; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        h2 {{ font-size: 1.75em; border-bottom: 1px solid #dee2e6; padding-bottom: 8px; }}
        h3 {{ font-size: 1.5em; }}
        h4 {{ font-size: 1.25em; }}
        
        p {{
            margin-bottom: 1em;
        }}
        
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border: 1px solid #ddd;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 10pt;
            color: #000;
            font-weight: 500;
        }}
        
        pre {{
            background: #f8f8f8;
            color: #000;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow-x: auto;
            margin: 15px 0;
            line-height: 1.6;
            font-size: 10pt;
        }}
        
        pre code {{
            background: none;
            color: #000;
            padding: 0;
            border: none;
            font-size: 10pt;
            font-weight: normal;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        table th, table td {{
            padding: 12px;
            text-align: left;
            border: 1px solid #dee2e6;
        }}
        
        table th {{
            background: #007bff;
            color: white;
            font-weight: 600;
        }}
        
        table tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        
        blockquote {{
            border-left: 4px solid #007bff;
            padding-left: 20px;
            margin: 20px 0;
            color: #666;
            font-style: italic;
        }}
        
        ul, ol {{
            margin: 15px 0;
            padding-left: 30px;
        }}
        
        li {{
            margin: 5px 0;
        }}
        
        a {{
            color: #007bff;
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        hr {{
            border: none;
            border-top: 2px solid #dee2e6;
            margin: 30px 0;
        }}
        
        /* Print Styles - Optimized for Black & White */
        @media print {{
            @page {{
                margin: 0.75in;
                size: A4;
            }}
            
            body {{
                background: white;
                padding: 0;
                color: #000;
                font-size: 11pt;
                line-height: 1.6;
            }}
            
            .container {{
                box-shadow: none;
                padding: 0;
                max-width: 100%;
            }}
            
            .actions, .no-print {{
                display: none !important;
            }}
            
            .header {{
                border-bottom: 2px solid #000;
                padding-bottom: 10pt;
                margin-bottom: 15pt;
            }}
            
            .header h1 {{
                color: #000;
                font-size: 18pt;
            }}
            
            .header p {{
                color: #333;
                font-size: 11pt;
            }}
            
            .meta {{
                background: #f9f9f9;
                border: 1px solid #ddd;
                padding: 10pt;
                margin-bottom: 15pt;
            }}
            
            h1 {{
                font-size: 16pt;
                border-bottom: 2px solid #000;
                padding-bottom: 5pt;
                margin-top: 20pt;
                margin-bottom: 10pt;
                page-break-after: avoid;
            }}
            
            h2 {{
                font-size: 14pt;
                border-bottom: 1px solid #666;
                padding-bottom: 4pt;
                margin-top: 15pt;
                margin-bottom: 8pt;
                page-break-after: avoid;
            }}
            
            h3 {{
                font-size: 13pt;
                margin-top: 12pt;
                margin-bottom: 6pt;
                page-break-after: avoid;
            }}
            
            h4 {{
                font-size: 12pt;
                margin-top: 10pt;
                margin-bottom: 5pt;
                page-break-after: avoid;
            }}
            
            p {{
                margin-bottom: 8pt;
                orphans: 3;
                widows: 3;
            }}
            
            /* Code blocks - BLACK & WHITE optimized */
            code {{
                background: #f0f0f0;
                border: 1px solid #999;
                padding: 2pt 4pt;
                font-family: 'Courier New', 'Consolas', monospace;
                font-size: 9pt;
                color: #000;
                font-weight: 600;
            }}
            
            pre {{
                background: #f8f8f8;
                border: 2px solid #666;
                padding: 10pt;
                margin: 10pt 0;
                page-break-inside: avoid;
                font-size: 9pt;
                line-height: 1.4;
                overflow: visible;
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
            
            pre code {{
                background: none;
                border: none;
                padding: 0;
                font-size: 9pt;
                font-weight: normal;
                color: #000;
            }}
            
            /* Tables - BLACK & WHITE optimized */
            table {{
                page-break-inside: avoid;
                border-collapse: collapse;
                width: 100%;
                margin: 10pt 0;
                border: 2px solid #000;
            }}
            
            table th {{
                background: #e0e0e0;
                color: #000;
                border: 1px solid #666;
                padding: 6pt;
                font-weight: bold;
                text-align: left;
            }}
            
            table td {{
                border: 1px solid #999;
                padding: 6pt;
                color: #000;
            }}
            
            table tr:nth-child(even) {{
                background: #f5f5f5;
            }}
            
            /* Blockquotes */
            blockquote {{
                border-left: 3px solid #000;
                padding-left: 10pt;
                margin: 10pt 0;
                font-style: italic;
                color: #333;
                page-break-inside: avoid;
            }}
            
            /* Links */
            a {{
                color: #000;
                text-decoration: underline;
            }}
            
            a[href]:after {{
                content: " (" attr(href) ")";
                font-size: 9pt;
                color: #666;
            }}
            
            /* Lists */
            ul, ol {{
                margin: 8pt 0;
                padding-left: 20pt;
            }}
            
            li {{
                margin: 4pt 0;
            }}
            
            /* Horizontal rules */
            hr {{
                border: none;
                border-top: 1px solid #000;
                margin: 15pt 0;
            }}
            
            /* Image handling */
            img {{
                max-width: 100%;
                page-break-inside: avoid;
            }}
            
            /* Page breaks */
            .page-break {{
                page-break-before: always;
            }}
            
            /* Ensure visibility of all content */
            * {{
                color: #000 !important;
                background: white !important;
            }}
            
            code, pre {{
                background: #f5f5f5 !important;
                border-color: #666 !important;
            }}
            
            table th {{
                background: #e0e0e0 !important;
            }}
            
            table tr:nth-child(even) {{
                background: #f8f8f8 !important;
            }}
        }}
        
        /* Code syntax highlighting */
        .codehilite .hll {{ background-color: #49483e }}
        .codehilite .c {{ color: #75715e }}
        .codehilite .k {{ color: #66d9ef }}
        .codehilite .l {{ color: #ae81ff }}
        .codehilite .n {{ color: #f8f8f2 }}
        .codehilite .o {{ color: #f92672 }}
        .codehilite .p {{ color: #f8f8f2 }}
        .codehilite .cm {{ color: #75715e }}
        .codehilite .cp {{ color: #75715e }}
        .codehilite .c1 {{ color: #75715e }}
        .codehilite .cs {{ color: #75715e }}
        .codehilite .kc {{ color: #66d9ef }}
        .codehilite .kd {{ color: #66d9ef }}
        .codehilite .kn {{ color: #f92672 }}
        .codehilite .kp {{ color: #66d9ef }}
        .codehilite .kr {{ color: #66d9ef }}
        .codehilite .kt {{ color: #66d9ef }}
        .codehilite .ld {{ color: #e6db74 }}
        .codehilite .m {{ color: #ae81ff }}
        .codehilite .s {{ color: #e6db74 }}
        .codehilite .na {{ color: #a6e22e }}
        .codehilite .nb {{ color: #f8f8f2 }}
        .codehilite .nc {{ color: #a6e22e }}
        .codehilite .no {{ color: #66d9ef }}
        .codehilite .nd {{ color: #a6e22e }}
        .codehilite .ni {{ color: #f8f8f2 }}
        .codehilite .ne {{ color: #a6e22e }}
        .codehilite .nf {{ color: #a6e22e }}
        .codehilite .nl {{ color: #f8f8f2 }}
        .codehilite .nn {{ color: #f8f8f2 }}
        .codehilite .nx {{ color: #a6e22e }}
        .codehilite .py {{ color: #f8f8f2 }}
        .codehilite .nt {{ color: #f92672 }}
        .codehilite .nv {{ color: #f8f8f2 }}
        .codehilite .ow {{ color: #f92672 }}
        .codehilite .w {{ color: #f8f8f2 }}
        .codehilite .mf {{ color: #ae81ff }}
        .codehilite .mh {{ color: #ae81ff }}
        .codehilite .mi {{ color: #ae81ff }}
        .codehilite .mo {{ color: #ae81ff }}
        .codehilite .sb {{ color: #e6db74 }}
        .codehilite .sc {{ color: #e6db74 }}
        .codehilite .sd {{ color: #e6db74 }}
        .codehilite .s2 {{ color: #e6db74 }}
        .codehilite .se {{ color: #ae81ff }}
        .codehilite .sh {{ color: #e6db74 }}
        .codehilite .si {{ color: #e6db74 }}
        .codehilite .sx {{ color: #e6db74 }}
        .codehilite .sr {{ color: #e6db74 }}
        .codehilite .s1 {{ color: #e6db74 }}
        .codehilite .ss {{ color: #e6db74 }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>{description}</p>
        </div>
        
        <div class="meta">
            <div class="meta-info">
                <strong>Generated:</strong> {date}<br>
                <strong>Source:</strong> {source_file}<br>
                <strong>Project:</strong> Movie Booking System
            </div>
            <div class="actions no-print">
                <button class="btn btn-primary" onclick="window.print()">
                    <span>🖨️</span> Print / Save as PDF
                </button>
                <button class="btn btn-success" onclick="downloadMarkdown()">
                    <span>📥</span> Download Markdown
                </button>
                <a href="index.html" class="btn btn-secondary">
                    <span>🏠</span> Back to Index
                </a>
            </div>
        </div>
        
        <div class="content">
            {content}
        </div>
        
        <hr class="no-print">
        <div class="meta no-print" style="margin-top: 30px;">
            <p style="color: #666; font-size: 0.9em;">
                💡 <strong>Tip:</strong> Use <kbd>Ctrl+P</kbd> (Windows/Linux) or <kbd>Cmd+P</kbd> (Mac) to print or save as PDF.
                Select "Save as PDF" as your destination.
            </p>
        </div>
    </div>
    
    <script>
        // Download markdown function
        function downloadMarkdown() {{
            const markdownContent = `{markdown_content}`;
            const blob = new Blob([markdownContent], {{ type: 'text/markdown' }});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '{source_file}';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }}
        
        // Keyboard shortcut for print
        document.addEventListener('keydown', function(e) {{
            if ((e.ctrlKey || e.metaKey) && e.key === 'p') {{
                e.preventDefault();
                window.print();
            }}
        }});
    </script>
</body>
</html>
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Printable Documentation - Movie Booking System</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 50px;
        }}
        
        .header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.3em;
            opacity: 0.95;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
        }}
        
        .card {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s, box-shadow 0.3s;
            cursor: pointer;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }}
        
        .card-icon {{
            font-size: 3em;
            margin-bottom: 15px;
        }}
        
        .card h2 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.5em;
        }}
        
        .card p {{
            color: #666;
            margin-bottom: 20px;
            line-height: 1.6;
        }}
        
        .card-actions {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s;
            font-weight: 500;
        }}
        
        .btn-primary {{
            background: #667eea;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #5568d3;
        }}
        
        .btn-secondary {{
            background: #f0f0f0;
            color: #333;
        }}
        
        .btn-secondary:hover {{
            background: #e0e0e0;
        }}
        
        .stats {{
            background: rgba(255,255,255,0.95);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .stats h3 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5em;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        
        .footer {{
            text-align: center;
            color: white;
            margin-top: 50px;
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Printable Documentation</h1>
            <p>Movie Booking System - Complete Documentation Suite</p>
        </div>
        
        <div class="stats">
            <h3>📊 Documentation Statistics</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">{total_docs}</div>
                    <div class="stat-label">Documents</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">100%</div>
                    <div class="stat-label">Print Ready</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">PDF</div>
                    <div class="stat-label">Export Support</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">✅</div>
                    <div class="stat-label">Up to Date</div>
                </div>
            </div>
        </div>
        
        <div class="grid">
            {cards}
        </div>
        
        <div class="footer">
            <p><strong>Generated:</strong> {date}</p>
            <p>Movie Booking System © 2026</p>
        </div>
    </div>
</body>
</html>
"""

CARD_TEMPLATE = """
<div class="card" onclick="window.location.href='{output}'">
    <div class="card-icon">{icon}</div>
    <h2>{title}</h2>
    <p>{description}</p>
    <div class="card-actions">
        <a href="{output}" class="btn btn-primary">
            <span>📖</span> View Document
        </a>
        <a href="../{source}" class="btn btn-secondary" download>
            <span>📥</span> Download MD
        </a>
    </div>
</div>
"""


def convert_markdown_to_html(doc_info):
    """Convert a markdown file to HTML with print support"""
    source_path = DOCS_DIR / doc_info['source']
    output_path = OUTPUT_DIR / doc_info['output']
    
    print(f"Converting {doc_info['source']}...")
    
    # Check if source exists
    if not source_path.exists():
        print(f"  ⚠️  Warning: Source file not found, skipping.")
        return False
    
    # Read markdown content
    with open(source_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Convert markdown to HTML (no syntax highlighting for B&W print)
    md = markdown.Markdown(extensions=[
        'extra',          # Tables, footnotes, etc.
        'tables',         # GitHub-style tables
        'fenced_code',    # ```code``` blocks
        'toc',            # Table of contents
        'nl2br',          # Newlines to <br>
        'sane_lists',     # Better list handling
        'smarty',         # Smart quotes
        'attr_list',      # Attributes
        'def_list',       # Definition lists
    ])
    html_content = md.convert(markdown_content)
    
    # Count statistics for verification
    code_blocks = markdown_content.count('```')
    tables = markdown_content.count('|---|')
    headings = len([line for line in markdown_content.split('\n') if line.strip().startswith('#')])
    chars = len(markdown_content)
    
    # Escape markdown content for JavaScript
    markdown_escaped = markdown_content.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$').replace('\n', '\\n')
    
    # Generate HTML
    html = HTML_TEMPLATE.format(
        title=doc_info['title'],
        description=doc_info['description'],
        date=datetime.now().strftime('%B %d, %Y'),
        source_file=doc_info['source'],
        content=html_content,
        markdown_content=markdown_escaped
    )
    
    # Write HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"  ✅ Created {doc_info['output']}")
    print(f"     📊 {chars:,} chars | {code_blocks//2} code blocks | {tables} tables | {headings} headings")
    return True


def generate_index():
    """Generate index.html with all documents"""
    print("\nGenerating index page...")
    
    # Icon mapping by category
    category_icons = {
        'Main': '📚',
        'Utilities': '🛠️',
        'Email': '📧',
        'Architecture': '🏗️',
        'Frontend': '🎨',
        'Interview': '💼'
    }
    
    # Icon mapping for specific documents
    doc_icons = {
        'Movie Booking System - README': '📖',
        'Documentation Index': '📑',
        'Quick Visual Guide': '🎯',
        'Utilities Implementation Guide': '🛠️',
        'Utilities Guide': '⚡',
        'Email System Complete Guide': '📧',
        'Email Templates README': '📝',
        'Services Guide': '🔧',
        'Understanding Celery': '📦',
        'Understanding Redis': '🔴',
        'Understanding Razorpay': '�',
        'Caching Guide': '💾',
        'JavaScript API Interaction': '🔌',
        'Interview - Beginner Questions': '📝',
        'Interview Questions': '❓',
        'Technical Deep Dive': '🔍'
    }
    
    # Organize documents by category
    categories = {}
    existing_docs = []
    
    for doc in DOCUMENTS:
        if (OUTPUT_DIR / doc['output']).exists():
            category = doc.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append(doc)
            existing_docs.append(doc)
    
    # Sort categories by order
    category_order = ['Main', 'Utilities', 'Email', 'Architecture', 'Frontend', 'Interview']
    sorted_categories = sorted(categories.items(), 
                               key=lambda x: category_order.index(x[0]) if x[0] in category_order else 999)
    
    # Generate cards by category
    all_cards_html = []
    
    for category, docs in sorted_categories:
        # Sort docs by priority within category
        docs.sort(key=lambda x: x.get('priority', 999))
        
        # Category header
        category_header = f'''
        <div style="grid-column: 1 / -1; margin-top: 20px;">
            <h2 style="color: white; font-size: 2em; border-bottom: 3px solid white; padding-bottom: 10px; margin-bottom: 20px;">
                {category_icons.get(category, '📄')} {category} Documentation
            </h2>
        </div>
        '''
        all_cards_html.append(category_header)
        
        # Generate cards for this category
        for doc in docs:
            icon = doc_icons.get(doc['title'], category_icons.get(category, '📄'))
            card = CARD_TEMPLATE.format(
                icon=icon,
                title=doc['title'],
                description=doc['description'],
                output=doc['output'],
                source=doc['source']
            )
            all_cards_html.append(card)
    
    # Generate index
    index_html = INDEX_TEMPLATE.format(
        total_docs=len(existing_docs),
        cards=''.join(all_cards_html),
        date=datetime.now().strftime('%B %d, %Y at %I:%M %p')
    )
    
    # Write index file
    index_path = OUTPUT_DIR / 'index.html'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    print(f"  ✅ Created index.html with {len(existing_docs)} documents in {len(categories)} categories")


def main():
    """Main conversion function"""
    print("=" * 60)
    print("📄 HTML Documentation Generator")
    print("=" * 60)
    print()
    
    # Convert all documents
    converted = 0
    for doc in DOCUMENTS:
        if convert_markdown_to_html(doc):
            converted += 1
    
    # Generate index
    if converted > 0:
        generate_index()
    
    print()
    print("=" * 60)
    print(f"✅ Successfully converted {converted} documents")
    print("=" * 60)
    print()
    print("📂 Output location:", OUTPUT_DIR.absolute())
    print("🌐 Open in browser: ", (OUTPUT_DIR / 'index.html').absolute())
    print()
    print("To view:")
    print(f"  open {OUTPUT_DIR / 'index.html'}")


if __name__ == '__main__':
    main()
