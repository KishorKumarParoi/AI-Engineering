# Kaggle Data Analysis Skill - Sharing Guide

## 📦 Skill Package

**File:** `kaggle-data-analysis.skill` (29 KB)

This is a complete, portable skill package that can be shared with anyone using Claude Code.

---

## 🚀 How to Share

### Option 1: Direct File Share
1. Copy `kaggle-data-analysis.skill` to your recipient
2. Have them place it in their Claude Code skills directory:
   ```
   ~/.claude/skills/
   ```
3. The skill will be automatically available in their Claude Code environment

### Option 2: GitHub Release
1. Upload to a GitHub release or repository
2. Share the download link with others
3. Recipients can download and place in `~/.claude/skills/`

### Option 3: Cloud Storage
1. Upload to Google Drive, Dropbox, or similar
2. Share the link with collaborators
3. They download and install locally

---

## 📥 Installation Instructions (for Recipients)

### macOS / Linux
```bash
# 1. Download the .skill file

# 2. Create skills directory if it doesn't exist
mkdir -p ~/.claude/skills

# 3. Copy the skill file
cp kaggle-data-analysis.skill ~/.claude/skills/

# 4. Restart Claude Code to see the skill available
```

### Windows
```powershell
# 1. Download the .skill file

# 2. Create skills directory
mkdir -p $env:USERPROFILE\.claude\skills

# 3. Copy the skill file
Copy-Item kaggle-data-analysis.skill -Destination $env:USERPROFILE\.claude\skills\

# 4. Restart Claude Code
```

---

## 🔍 What's Included

The `.skill` file contains:

```
kaggle-data-analysis.skill
├── SKILL.md                          (Metadata & Documentation)
├── scripts/
│   ├── 01_eda.py                     (Exploratory Data Analysis)
│   ├── 02_preprocessing.py           (Data Cleaning)
│   ├── 03_feature_engineering.py     (Feature Creation)
│   ├── 04_statistical_analysis.py    (Statistical Insights)
│   ├── 05_visualization.py           (Visualizations & Charts)
│   └── run_full_analysis.py          (Main Orchestrator)
├── assets/
│   ├── QUICKSTART.md                 (Quick Start Guide)
│   ├── requirements.txt              (Python Dependencies)
│   └── config_template.yaml          (Configuration Template)
└── references/
    ├── kaggle_best_practices.md
    ├── feature_engineering_guide.md
    ├── statistical_methods.md
    └── data_analysis_toolkit.md
```

---

## ✨ Key Features

- **5-Phase Analysis Pipeline** — EDA, Preprocessing, Feature Engineering, Statistics, Visualization
- **HTML Reports** — Organized in `reports/` subfolder with interactive visualizations
- **Customizable** — 3 analysis levels (basic, standard, advanced) & 3 effort levels (quick, standard, thorough)
- **Python-Based** — Pure Python with pandas, scikit-learn, matplotlib, seaborn
- **No Dependencies** — Includes all analysis scripts, just needs Python packages

---

## 🛠️ Requirements

Before using the skill, install Python dependencies:

```bash
pip install pandas numpy scikit-learn matplotlib seaborn scipy statsmodels plotly
```

Or use the included requirements file:
```bash
pip install -r assets/requirements.txt
```

---

## 📖 Quick Usage

After installation, use in Claude Code:

```bash
/kaggle-data-analysis run on titanic.csv with shallow insight using medium effort, output to output folder
```

Or run directly:
```bash
python scripts/run_full_analysis.py --input data.csv --output results/ --level basic --effort standard
```

---

## 📋 Version Info

- **Skill Name:** kaggle-data-analysis
- **Type:** Data Analysis
- **Created:** April 27, 2026
- **Python Version:** 3.7+
- **Package Size:** 29 KB

---

## 🆘 Support

If recipients encounter issues:

1. **Skill not showing up** — Ensure it's in `~/.claude/skills/` and restart Claude Code
2. **Import errors** — Run `pip install -r assets/requirements.txt`
3. **Output folder issues** — Skill creates reports in `output/reports/` subfolder automatically

---

## 📝 License

Share freely! This skill is designed to be shared and reused.

---

## 💡 Tips for Distribution

- Include this guide (`SKILL-SHARING-GUIDE.md`) with the `.skill` file
- Create a simple README for quick setup
- Test on another machine before sharing
- Include examples of expected outputs

---

**Share your skill with confidence! 🎉**
