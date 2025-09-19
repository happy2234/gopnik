# Netlify Deployment Guide

This guide explains how to deploy the Gopnik web demo to Netlify.

## 🚀 Quick Deploy

### Option 1: Manual Upload (Recommended - Avoids Config Issues)

1. **Clone the repository** locally
2. **Run the build script**: `python scripts/build-netlify.py`
3. **Go to** [netlify.com](https://netlify.com) and sign up
4. **Drag and drop** the `netlify/dist` folder to Netlify dashboard
5. **Done!** Your site will be live immediately

### Option 2: One-Click Deploy

[![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/happy2234/gopnik)

*Note: If you encounter configuration parsing errors, use Option 1 instead.*

### Option 2: Manual Setup

1. **Fork this repository** to your GitHub account

2. **Sign up for Netlify** at [netlify.com](https://netlify.com)

3. **Connect your repository**:
   - Go to Netlify dashboard
   - Click "New site from Git"
   - Choose GitHub and select your forked repository

4. **Configure build settings**:
   - Build command: `python scripts/build-netlify.py`
   - Publish directory: `netlify/dist`
   - Leave Functions directory empty

5. **Deploy!** - Netlify will automatically build and deploy your site

## 🔧 Configuration

### Environment Variables

For full functionality, add these environment variables in Netlify:

```bash
PYTHON_VERSION=3.9
GOPNIK_ENV=production
GOPNIK_LOG_LEVEL=INFO
```

### Custom Domain (Optional)

1. Go to your Netlify site dashboard
2. Click "Domain settings"
3. Add your custom domain
4. Update DNS records as instructed

## 📁 Project Structure

```
netlify/
├── functions/
│   └── api.py          # Serverless API handler
├── dist/               # Built static files (auto-generated)
└── requirements.txt    # Python dependencies

scripts/
└── build-netlify.py   # Build script

netlify.toml           # Netlify configuration
```

## 🛠️ Local Development

Test the Netlify build locally:

```bash
# Install dependencies
pip install -e .
pip install -r netlify/requirements.txt

# Build for Netlify
python scripts/build-netlify.py

# Serve locally (optional)
cd netlify/dist
python -m http.server 8000
```

## 🔍 Troubleshooting

### Build Fails

1. Check Python version (should be 3.9)
2. Verify all dependencies are in `netlify/requirements.txt`
3. Check build logs in Netlify dashboard

### Functions Not Working

1. Ensure `mangum` is installed
2. Check function logs in Netlify dashboard
3. Verify API routes are correctly configured

### Static Files Missing

1. Check if `src/gopnik/interfaces/web/static/` exists
2. Verify build script runs successfully
3. Check `netlify/dist/` contains expected files

## 📊 Features

The deployed demo includes:

- ✅ **Welcome Page** - Introduction and getting started
- ✅ **Demo Interface** - File upload and processing
- ✅ **API Endpoints** - RESTful API for processing
- ✅ **Static Assets** - CSS, JavaScript, images
- ✅ **Responsive Design** - Works on mobile and desktop

## 🔗 Links

- **Netlify Documentation**: https://docs.netlify.com/
- **Netlify Functions**: https://docs.netlify.com/functions/overview/
- **FastAPI + Netlify**: https://github.com/tiangolo/fastapi/discussions/1992

## 🆘 Support

If you encounter issues:

1. Check the [troubleshooting section](#-troubleshooting)
2. Review Netlify build logs
3. Open an issue on GitHub
4. Join our [discussions](https://github.com/happy2234/gopnik/discussions)