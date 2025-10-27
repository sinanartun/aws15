#!/usr/bin/env python
# coding: utf-8

# In[1]:


# (Run once if needed)
# %pip -q install --upgrade pandas numpy scikit-learn matplotlib seaborn joblib boto3


# # 1) Data Loading & Inspection

# In[2]:


import re
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import joblib

# Optional (only if loading from S3)
import boto3
import io

# Plot style & reproducibility
sns.set_theme(context="notebook", style="whitegrid")
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

pd.set_option("display.max_columns", 120)


# In[3]:


DATA_SOURCE = "local"

# Set these if using S3
S3_BUCKET = "blocket-lake--eun1-az1--x-s3"
S3_KEY = "/car_features.csv"

if DATA_SOURCE == "s3":
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
    df = pd.read_csv(io.BytesIO(obj["Body"].read()))
else:
    # Local CSV path (adjust as needed)
    CSV_PATH = "cars.csv"
    df = pd.read_csv(CSV_PATH)

print(df.shape)
display(df.head())
display(df.isna().mean().sort_values(ascending=False).head(20))
df.info()


# # 2) Data Cleaning & Preparation

# In[4]:


df = df.drop(columns=["ad_id"], errors="ignore")

def to_float_or_nan(x):
    if pd.isna(x): 
        return np.nan
    s = re.sub(r"[^\d]", "", str(x))
    return float(s) if s else np.nan


if "mileage" in df.columns:
    df["mileage"] = df["mileage"].apply(to_float_or_nan)

for col in ["model_year", "horsepower", "equipment_count"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

if "first_traffic_date" in df.columns:
    df["first_traffic_date"] = pd.to_datetime(df["first_traffic_date"], errors="coerce")

df = df[df["price"].notnull()]

cat_cols_all = [
    "brand", "model", "model_family", "fuel", "gearbox", "color",
    "drive_wheels", "body_type", "advertiser_type", "region", "municipality"
]
for c in cat_cols_all:
    if c in df.columns:
        df[c] = df[c].fillna("Unknown")


# # 3) Feature Engineering

# In[5]:


today = pd.Timestamp.today().normalize()

if "model_year" in df.columns:
    df["vehicle_age"] = today.year - df["model_year"]

# Days since first traffic date
if "first_traffic_date" in df.columns:
    df["days_since_first_traffic"] = (today - df["first_traffic_date"]).dt.days

# Location combo
if {"region","municipality"}.issubset(df.columns):
    df["region_municipality"] = df["region"].astype(str) + " | " + df["municipality"].astype(str)

# Subject length
if "subject" in df.columns:
    df["subject_len"] = df["subject"].astype(str).str.len()

# Target transform (log)
df["price_log"] = np.log1p(df["price"].astype(float))

display(df.head())


# # 4) Outlier Detection & Handling

# In[6]:


# ===== 4) Outlier Handling =====

# Optional: remove obvious non-sale rows (e.g., leasing/monthly promos)
df = df[df["price"] >= 10_000]

# Clip unrealistic entries to reasonable bounds
if "model_year" in df.columns:
    df["model_year"] = df["model_year"].clip(lower=2000, upper=today.year + 1)
if "horsepower" in df.columns:
    df["horsepower"] = df["horsepower"].clip(lower=100, upper=800)
if "vehicle_age" in df.columns:
    df["vehicle_age"] = df["vehicle_age"].clip(lower=0, upper=25)
if "equipment_count" in df.columns:
    df["equipment_count"] = df["equipment_count"].clip(lower=0, upper=150)

# Percentile capping function (robust and simple)
def cap_outliers(series, lower_q=0.01, upper_q=0.99):
    lo, hi = series.quantile(lower_q), series.quantile(upper_q)
    return series.clip(lo, hi)

num_for_capping = [c for c in ["price","mileage","horsepower","equipment_count","vehicle_age"] if c in df.columns]
for c in num_for_capping:
    df[c] = cap_outliers(df[c], 0.01, 0.99)

# Optional: log of mileage (skew reduction)
if "mileage" in df.columns:
    df["mileage_log"] = np.log1p(df["mileage"])

# Quick sanity visuals (boxplots)
fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(14, 8))
axes = axes.ravel()
plot_cols = [c for c in ["price","mileage","horsepower","equipment_count","vehicle_age","subject_len"] if c in df.columns]
for i, c in enumerate(plot_cols):
    sns.boxplot(x=df[c], color="lightblue", ax=axes[i], fliersize=2)
    axes[i].set_title(f"{c} (after capping)")
plt.tight_layout()
plt.show()


# In[10]:


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Pick only numeric columns
num_df = df.select_dtypes(include=["number"]).copy()

# Optional: choose what to include (uncomment to focus)
# keep_cols = ["price","price_log","mileage","mileage_log","horsepower",
#              "equipment_count","vehicle_age","days_since_first_traffic","subject_len"]
# num_df = num_df[[c for c in keep_cols if c in num_df.columns]]

corr = num_df.corr(method="pearson")

# Mask upper triangle for a cleaner look
mask = np.triu(np.ones_like(corr, dtype=bool))

plt.figure(figsize=(9,7))
sns.heatmap(
    corr, mask=mask, annot=True, fmt=".2f",
    cmap="coolwarm", linewidths=0.5, cbar_kws={"shrink": .8}
)
plt.title("Correlation Heatmap (Pearson)")
plt.tight_layout()
plt.show()


# In[11]:


corr_s = num_df.corr(method="spearman")
mask = np.triu(np.ones_like(corr_s, dtype=bool))

plt.figure(figsize=(9,7))
sns.heatmap(
    corr_s, mask=mask, annot=True, fmt=".2f",
    cmap="coolwarm", linewidths=0.5, cbar_kws={"shrink": .8}
)
plt.title("Correlation Heatmap (Spearman)")
plt.tight_layout()
plt.show()


# In[12]:


corr_s = num_df.corr(method="spearman")
mask = np.triu(np.ones_like(corr_s, dtype=bool))

plt.figure(figsize=(9,7))
sns.heatmap(
    corr_s, mask=mask, annot=True, fmt=".2f",
    cmap="coolwarm", linewidths=0.5, cbar_kws={"shrink": .8}
)
plt.title("Correlation Heatmap (Spearman)")
plt.tight_layout()
plt.show()


# In[13]:


df = df.drop(columns=[
    "price", "mileage", "model_year", "days_since_first_traffic"
], errors="ignore")


# In[ ]:





# # 5) Data Splitting & Preprocessing

# In[14]:


features = [
    # numeric
    "mileage_log" if "mileage_log" in df.columns else "mileage",
    "horsepower", "equipment_count", "vehicle_age", "days_since_first_traffic", "subject_len",
    # categorical
    "brand", "model", "model_family", "fuel", "gearbox", "color",
    "drive_wheels", "body_type", "advertiser_type", "region", "municipality", "region_municipality"
]
features = [f for f in features if f in df.columns]  # keep existing only

X = df[features].copy()
y = df["price_log"].copy()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=RANDOM_STATE
)

num_cols = X_train.select_dtypes(include=["number"]).columns.tolist()
cat_cols = X_train.select_dtypes(exclude=["number"]).columns.tolist()

numeric_tf = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])

# IMPORTANT: make OneHot dense for HistGradientBoosting
ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)  # use sparse=False if sklearn <1.2

categorical_tf = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("onehot", ohe),
])

preprocess = ColumnTransformer([
    ("num", numeric_tf, num_cols),
    ("cat", categorical_tf, cat_cols),
], remainder="drop")


# # 6) Modeling & Evaluation

# In[15]:


model = HistGradientBoostingRegressor(
    learning_rate=0.06,
    max_iter=1000,
    early_stopping=True,
    random_state=RANDOM_STATE,
)

pipe = Pipeline([
    ("preprocess", preprocess),
    ("model", model),
])

pipe.fit(X_train, y_train)
print("✅ Model trained!")

# Evaluate
y_pred_log = pipe.predict(X_test)
y_true = np.expm1(y_test)
y_pred = np.expm1(y_pred_log)

mae = mean_absolute_error(y_true, y_pred)
mse = mean_squared_error(y_true, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_true, y_pred)

print(f"MAE : {mae:,.0f} SEK")
print(f"RMSE: {rmse:,.0f} SEK")
print(f"R²  : {r2:.3f}")


# In[9]:


resid = y_true - y_pred
plt.figure(figsize=(6,4))
sns.histplot(resid, bins=50, kde=True)
plt.title("Residuals (SEK)")
plt.xlabel("Actual - Predicted")
plt.show()

plt.figure(figsize=(6,4))
sns.scatterplot(x=y_true, y=y_pred, alpha=0.4)
plt.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--')
plt.xlabel("Actual (SEK)")
plt.ylabel("Predicted (SEK)")
plt.title("Actual vs Predicted")
plt.show()

