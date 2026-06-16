# 🚀 Quick Install - Kaggle Data Analysis Skill

## Installation (30 seconds)

### Step 1: Install File
Place `kaggle-data-analysis.skill` in:
```
~/.claude/skills/
```

### Step 2: Install Dependencies
```bash
pip install pandas numpy scikit-learn matplotlib seaborn scipy statsmodels plotly
```

### Step 3: Restart Claude Code
Close and reopen Claude Code.

✅ **Done!** The skill is now available.

---

## First Use

### Run on a CSV file:
```bash
/kaggle-data-analysis run on titanic.csv with shallow insight using medium effort, output to output folder
```

### Or use Python directly:
```bash
python scripts/run_full_analysis.py --input data.csv --output results/
```

---

## Output Structure
```
output/
├── reports/                    (All HTML reports)
│   ├── data_01_eda_report.html
│   ├── data_02_preprocessing_report.html
│   ├── data_03_feature_engineering_report.html
│   ├── data_04_statistical_analysis_report.html
│   └── data_05_visualization_report.html
└── final_analysis_summary.md   (Executive summary)
```

---

## What You Get

✅ Exploratory Data Analysis (EDA)  
✅ Data Preprocessing & Cleaning  
✅ Feature Engineering (14+ features)  
✅ Statistical Analysis  
✅ Interactive Visualizations  
✅ HTML Reports with Insights  

---

## Customization

```bash
# Basic quick analysis
python scripts/run_full_analysis.py --input data.csv --level basic --effort quick

# Advanced thorough analysis
python scripts/run_full_analysis.py --input data.csv --level advanced --effort thorough --model xgboost
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Skill not showing | Restart Claude Code |
| Import error | Run `pip install -r assets/requirements.txt` |
| Permission error | Ensure `~/.claude/skills/` directory exists |

---

**Questions?** Check `SKILL-SHARING-GUIDE.md` for more details.
