from pathlib import Path
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# Resolve paths
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

csv_paths = [
    BASE_DIR / "task_time_data.csv",
    PROJECT_ROOT / "data" / "task_time_data.csv",
]

csv_file = None
for p in csv_paths:
    if p.exists():
        csv_file = p
        break

if not csv_file:
    raise FileNotFoundError(f"Could not find task_time_data.csv in {[str(p) for p in csv_paths]}")

print(f"Loading data from: {csv_file}")
df = pd.read_csv(csv_file)

# Standardize column names
df.columns = [
    col.strip()
    .lower()
    .replace(" ", "_")
    .replace("(", "")
    .replace(")", "")
    for col in df.columns
]

print(f"Dataset shape: {df.shape}")
print(f"Columns: {list(df.columns)}")

# Define feature columns and target
feature_cols = ["task_type", "weather", "operator_skill", "machine_age_yrs"]
target_col = "actual_time_min"

X = df[feature_cols]
y = df[target_col]

# Train / Test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Build unified preprocessing + regressor pipeline
categorical_features = ["task_type", "weather", "operator_skill"]
numeric_features = ["machine_age_yrs"]

preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features),
        ("num", "passthrough", numeric_features),
    ]
)

pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(n_estimators=100, random_state=42)),
    ]
)

# Train model
print("Training RandomForestRegressor pipeline...")
pipeline.fit(X_train, y_train)

# Evaluate on test set
y_pred = pipeline.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("=" * 60)
print("EVALUATION RESULTS (For your hackathon pitch):")
print(f"  Mean Absolute Error (MAE): {mae:.2f} minutes")
print(f"  R-squared (R²):           {r2:.4f} ({r2 * 100:.1f}% variance explained)")
print("=" * 60)

# Save the fitted pipeline
model_output_path = BASE_DIR / "model.pkl"
joblib.dump(pipeline, model_output_path)
print(f"Model successfully saved to: {model_output_path}")

# Sanity check test prediction matching CONTRACT.md example
test_input = pd.DataFrame([
    {
        "task_type": "Trenching",
        "weather": "Rainy",
        "operator_skill": "Intermediate",
        "machine_age_yrs": 4,
    }
])
sample_pred = pipeline.predict(test_input)[0]
print(f"Sample prediction [Trenching, Rainy, Intermediate, 4 yrs]: {sample_pred:.1f} minutes")
