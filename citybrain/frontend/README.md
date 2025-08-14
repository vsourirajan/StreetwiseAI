# City Brain Frontend

A beautiful, ChatGPT-style web interface for the City Brain Urban Planning AI Assistant with **real Modal API integration**.

## 🚀 Features

- **Modern ChatGPT-style UI** with smooth animations and responsive design
- **Dynamic textbox** that expands as you type (like ChatGPT)
- **Real-time character count** with visual feedback
- **Loading states** with animated progress steps
- **Markdown-like formatting** support for AI responses
- **Mobile-responsive** design that works on all devices
- **Professional urban planning** interface
- **🔗 Real Modal API Integration** - No more hardcoded responses!

## 🛠️ Quick Start

### Option 1: Full Stack with Backend Proxy (Recommended)

```bash
# Navigate to the frontend directory
cd citybrain/frontend

# Install backend dependencies
pip install -r requirements.txt

# Deploy your Modal app first (in another terminal)
modal deploy ../../citybrain/modal_app.py

# Start the backend proxy server
python backend_proxy.py

# Open your browser to http://localhost:5001
```

### Option 2: Frontend Only (Demo Mode)

```bash
# Navigate to the frontend directory
cd citybrain/frontend

# Start the simple HTTP server
python server.py

# Open your browser to http://localhost:8000
```

## 🔗 Modal API Integration

### How It Works

1. **Frontend** sends user query to `/api/modal`
2. **Backend Proxy** calls Modal CLI: `modal run city-brain-urban-planning::get_scenario_insights --query "your query"`
3. **Modal** executes the function with Llama 3 AI model
4. **Response** flows back through the proxy to the frontend
5. **User** sees real AI-generated urban planning insights!

### Backend Proxy Endpoints

- `POST /api/modal` - Call Modal functions
- `GET /api/modal/status` - Check Modal deployment status
- `GET /api/modal/test` - Test Modal connection
- `GET /health` - Health check

### Testing the Integration

```bash
# Test Modal status
curl http://localhost:5001/api/modal/status

# Test Modal connection
curl http://localhost:5001/api/modal/test

# Test with a real query
curl -X POST http://localhost:5001/api/modal \
  -H "Content-Type: application/json" \
  -d '{"query": "What zoning applies to Times Square?"}'
```

## 🎯 Try These Real Queries

Once your Modal app is deployed and backend proxy is running:

- "If we pedestrianize Broadway from 14th to 34th in NYC, what zoning amendments would be required?"
- "What are the zoning requirements for commercial development in Manhattan?"
- "How do I conduct a traffic impact study for a new building?"
- "What happens to traffic if we close 5th Avenue to cars?"

## 🏗️ Architecture

```
User Query → Frontend → Backend Proxy → Modal CLI → Modal Cloud → Llama 3 AI → Response
```

### Components

- **Frontend**: Beautiful ChatGPT-style UI (HTML/CSS/JS)
- **Backend Proxy**: Flask server that bridges frontend and Modal
- **Modal App**: Cloud functions with Llama 3 AI model
- **Data Sources**: NYC zoning, traffic, and urban planning data

## 🔧 Technical Details

### File Structure
```
frontend/
├── index.html              # Main HTML structure
├── styles.css              # CSS styling and animations
├── script.js               # JavaScript functionality
├── server.py               # Simple HTTP server (demo mode)
├── backend_proxy.py        # Flask backend proxy (production)
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

### Key Features
- **ES6 Classes**: Modern JavaScript architecture
- **CSS Grid/Flexbox**: Responsive layout system
- **CSS Animations**: Smooth transitions and keyframes
- **Event Handling**: Comprehensive user interaction management
- **Error Handling**: Graceful fallbacks and user feedback
- **Real API Calls**: Actual Modal function execution

## 🚀 Deployment Options

### 1. Local Development
```bash
python backend_proxy.py  # Full stack with Modal integration
```

### 2. Production Backend
Deploy the Flask backend to:
- **Heroku**: Easy deployment with Git
- **Railway**: Simple container deployment
- **DigitalOcean**: VPS with full control
- **AWS/GCP**: Enterprise-grade infrastructure

### 3. Frontend Hosting
Deploy the static frontend to:
- **Netlify**: Drag & drop deployment
- **Vercel**: Git-based deployment
- **GitHub Pages**: Free hosting for open source

## 🐛 Troubleshooting

### Modal Not Deployed
```bash
# Check Modal status
modal app list

# Deploy if needed
modal deploy ../../citybrain/modal_app.py
```

### Backend Proxy Issues
```bash
# Check Modal CLI
modal --version

# Test Modal connection
curl http://localhost:5001/api/modal/status

# Check logs
python backend_proxy.py
```

### Port Conflicts
```bash
# Use different port
python backend_proxy.py --port 5001
```

## 📱 Mobile Testing

The interface is fully responsive and works on:
- **Desktop**: Full-featured experience with Modal integration
- **Tablet**: Optimized touch interface
- **Mobile**: Compact, mobile-friendly layout

## 🎉 Ready for Production!

Your City Brain frontend now has:

1. ✅ **Beautiful UI** - ChatGPT-style interface
2. ✅ **Real AI Integration** - Llama 3 via Modal
3. ✅ **Backend Proxy** - Flask server for API calls
4. ✅ **Error Handling** - Graceful fallbacks
5. ✅ **Production Ready** - Deployable architecture

## 🔮 Next Steps

1. **Deploy Modal App**: `modal deploy citybrain/modal_app.py`
2. **Start Backend Proxy**: `python backend_proxy.py`
3. **Test Integration**: Ask real urban planning questions
4. **Deploy to Production**: Choose your hosting platform
5. **Customize**: Add your branding and features

Start the backend proxy and experience **real AI-powered urban planning insights**! 🏙️✨ 