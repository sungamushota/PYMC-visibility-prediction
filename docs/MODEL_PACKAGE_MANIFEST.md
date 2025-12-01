# Model Package Manifest
## Complete File List for Distribution

To share the trained visibility prediction model with someone, provide them with the following files:

---

## 📦 ESSENTIAL FILES (Minimum Required)

### 1. Model Files (in `models/` directory)
```
models/
├── stormglass_pymc_hierarchical_extended_idata.nc     [2.8 MB] ⭐ REQUIRED
├── stormglass_pymc_hierarchical_extended_scaler.pkl   [2 KB]   ⭐ REQUIRED
└── stormglass_pymc_hierarchical_extended_predictors.pkl [1 KB] ⭐ REQUIRED
```

**What they do:**
- `.nc` file = Trained Bayesian model with all posterior distributions
- `.pkl` scaler = Normalizes input features to same scale as training
- `.pkl` predictors = List of 30 feature names the model expects

### 2. Prediction Script
```
predict_visibility.py                                   [~10 KB] ⭐ REQUIRED
```
**What it does:** Easy-to-use Python class for making predictions

### 3. Documentation
```
MODEL_README.md                                         [~8 KB]  ⭐ REQUIRED
requirements.txt                                        [~0.5 KB] ⭐ REQUIRED
```
**What they do:**
- README = Full documentation, usage examples, site list
- requirements.txt = Python package dependencies

---

## 📋 OPTIONAL FILES (Nice to Have)

### 4. Model Performance Data
```
models/
├── stormglass_pymc_hierarchical_extended_coefficient_summary.csv [3 KB]
└── site_performance_metrics.csv                                  [1 KB]
```
**What they do:**
- Feature importance and coefficient values
- Per-site accuracy metrics

### 5. Site Information
```
site_coordinates.json                                   [~2 KB]
```
**What it does:** GPS coordinates for all 24 dive sites

### 6. Visualizations (in `plots/` directory)
```
plots/
├── predicted_vs_actual_visibility.png                  [~50 KB]
└── site_performance_table.png                          [~100 KB]
```
**What they do:** Show model accuracy and performance by site

---

## 💾 COMPLETE PACKAGE STRUCTURE

```
visibility_prediction_model/
│
├── predict_visibility.py              ⭐ Prediction script
├── MODEL_README.md                    ⭐ Documentation
├── requirements.txt                   ⭐ Dependencies
├── site_coordinates.json                Site GPS data
│
├── models/
│   ├── stormglass_pymc_hierarchical_extended_idata.nc        ⭐ Model
│   ├── stormglass_pymc_hierarchical_extended_scaler.pkl      ⭐ Scaler
│   ├── stormglass_pymc_hierarchical_extended_predictors.pkl  ⭐ Predictors
│   ├── stormglass_pymc_hierarchical_extended_coefficient_summary.csv
│   └── site_performance_metrics.csv
│
└── plots/  (optional)
    ├── predicted_vs_actual_visibility.png
    └── site_performance_table.png
```

---

## 🚀 QUICK START FOR RECIPIENT

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Test the Model
```python
from predict_visibility import VisibilityPredictor

# Load model
predictor = VisibilityPredictor(model_dir='models')

# Check it works
importance = predictor.get_feature_importance()
print("Top 5 features:")
print(importance.head())
```

### Step 3: Make Predictions
See MODEL_README.md for full examples

---

## 📊 TOTAL PACKAGE SIZE

**Minimum (Essential only):** ~3 MB
**Complete (Everything):** ~3.2 MB

Very small and portable! ✅

---

## 🔄 HOW TO SHARE

### Option 1: Zip File (Recommended)
```bash
# Create zip file
zip -r visibility_model.zip \
    predict_visibility.py \
    MODEL_README.md \
    requirements.txt \
    models/ \
    site_coordinates.json \
    plots/
```

### Option 2: GitHub Repository
Upload all files to a GitHub repo. Recipients can clone:
```bash
git clone https://github.com/your-username/visibility-model
cd visibility-model
pip install -r requirements.txt
```

### Option 3: Cloud Storage
Upload to Google Drive/Dropbox and share the link

---

## ✅ CHECKLIST

Before sharing, verify:
- [ ] All 3 model files (.nc, 2x .pkl) are present
- [ ] predict_visibility.py runs without errors
- [ ] MODEL_README.md is up to date
- [ ] requirements.txt includes all dependencies
- [ ] Example data or usage instructions provided

---

## 📧 SUPPORT

**Common Issues:**
1. **"ModuleNotFoundError: No module named 'pymc'"**
   → Run: `pip install -r requirements.txt`

2. **"numpy.dtype size changed" error**
   → Install specific numpy version: `pip install numpy==1.26.4`

3. **Missing features in input data**
   → Check MODEL_README.md "Input Data Format" section

4. **Site code not recognized**
   → Use one of the 24 site codes listed in MODEL_README.md

---

Last updated: December 1, 2025
Model version: hierarchical_extended_v1

