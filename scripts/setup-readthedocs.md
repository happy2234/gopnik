# ReadTheDocs Setup Guide

This guide will help you set up automatic documentation building on ReadTheDocs.

## 🚀 Quick Setup Steps

### 1. **Create ReadTheDocs Account**

1. Go to: https://readthedocs.org/
2. Click "Sign up" 
3. Sign up with your GitHub account
4. Authorize ReadTheDocs to access your repositories

### 2. **Import Your Project**

1. Once logged in, click "Import a Project"
2. Click "Import Manually" 
3. Fill in the project details:
   - **Name**: `gopnik`
   - **Repository URL**: `https://github.com/happy2234/gopnik`
   - **Repository type**: `Git`
   - **Description**: `AI-powered forensic-grade deidentification toolkit`
   - **Language**: `English`
   - **Programming Language**: `Python`
   - **Project homepage**: `https://github.com/happy2234/gopnik`
   - **Tags**: `ai, privacy, deidentification, pii, redaction`

4. Click "Next"

### 3. **Configure Build Settings**

ReadTheDocs will automatically detect the `.readthedocs.yaml` configuration file we created. This file specifies:

- **Python version**: 3.9
- **Sphinx configuration**: `docs/conf.py`
- **Requirements**: `docs/requirements.txt` and `requirements.txt`
- **Output formats**: HTML, PDF, ePub

### 4. **Verify Build**

1. After import, ReadTheDocs will automatically trigger a build
2. Go to your project dashboard: `https://readthedocs.org/projects/gopnik/`
3. Click on "Builds" to see the build status
4. If successful, your docs will be available at: `https://gopnik.readthedocs.io/`

### 5. **Configure Webhooks (Automatic)**

ReadTheDocs automatically sets up webhooks with GitHub, so documentation will rebuild automatically when you push changes to the repository.

## 🔧 Troubleshooting

### Build Fails

If the build fails, check:

1. **Build logs** in ReadTheDocs dashboard
2. **Dependencies** in `docs/requirements.txt`
3. **Sphinx configuration** in `docs/conf.py`
4. **Python imports** in documentation files

### Common Issues

**Missing dependencies:**
```bash
# Add to docs/requirements.txt
sphinx>=5.0.0
sphinx-rtd-theme>=1.2.0
myst-parser>=0.18.0
```

**Import errors:**
- Make sure all Python modules can be imported
- Check that `src/` directory is in Python path
- Verify all dependencies are listed in requirements files

**Configuration errors:**
- Check `docs/conf.py` for syntax errors
- Verify all extensions are properly installed
- Check file paths and directory structure

## 📚 Documentation Structure

Our documentation is organized as:

```
docs/
├── conf.py                 # Sphinx configuration
├── index.md               # Main documentation index
├── user-guide/           # User documentation
│   ├── index.md
│   ├── installation.md
│   └── ...
├── developer-guide/      # Developer documentation
│   ├── index.md
│   ├── architecture.md
│   └── ...
├── api-reference/        # API documentation (auto-generated)
├── tutorials/            # Step-by-step tutorials
├── faq.md               # Frequently asked questions
└── requirements.txt     # Documentation build requirements
```

## 🎯 Next Steps

After ReadTheDocs is set up:

1. **Verify documentation builds** successfully
2. **Check all links** work correctly
3. **Add more content** to documentation sections
4. **Set up custom domain** (optional): `docs.gopnik.ai`
5. **Configure analytics** (optional) for usage tracking

## 🔗 Useful Links

- **ReadTheDocs Dashboard**: https://readthedocs.org/projects/gopnik/
- **Documentation URL**: https://gopnik.readthedocs.io/
- **Sphinx Documentation**: https://www.sphinx-doc.org/
- **MyST Parser**: https://myst-parser.readthedocs.io/

---

**📖 Once set up, your documentation will be automatically built and deployed on every commit!**