import pandas as pd
import numpy as np
import glob
import os
import joblib
from collections import Counter
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from imblearn.over_sampling import SMOTE

DATA_FOLDER = 'dataset/'

ACTION_MAP = {
    "==== RELAX ====": "RELAX",
    "==== RELAX YOUR FACE (Gathering Baseline) ====": "RELAX",
    "==== RELAX UNTIL FINISHED ====": "RELAX",
    "==== [ CLENCH JAW ] ====": "JAW_CLENCH",
    "==== [ WINK LEFT EYE ] ====": "LEFT_WINK",
    "==== [ WINK RIGHT EYE ] ====": "RIGHT_WINK",
    "==== [ DOUBLE BLINK ] ====": "DOUBLE_BLINK",
    "==== [ SQUEEZE BOTH EYES SHUT (Double Blink) ] ====": "DOUBLE_BLINK"
}

def extract_features(window_data):
    """Extracts 14 exact features from a 30-sample window."""
    ch1, ch2 = window_data[:, 0], window_data[:, 1]

    def get_stats(ch):
        return [
            np.sqrt(np.mean(ch**2)),        # 1: RMS
            np.mean(np.abs(np.diff(ch))),   # 2: MAV Diff
            np.var(ch),                     # 3: Variance
            np.max(ch) - np.min(ch),        # 4: Peak-to-Peak
            np.std(ch),                     # 5: Std Dev
            ((ch[:-1] * ch[1:]) < 0).sum()  # 6: Zero Crossings
        ]

    f1 = get_stats(ch1)
    f2 = get_stats(ch2)
    diff_rms = abs(f1[0] - f2[0])           # 13: Difference in RMS
    diff_p2p = abs(f1[3] - f2[3])           # 14: Difference in P2P

    return f1 + f2 + [diff_rms, diff_p2p]

def main():
    print("========================================")
    print("   BCI MASTER TRAINING SCRIPT           ")
    print("========================================\n")

    pilot_name = input("Who is this model for? (e.g., pralhad): ").strip().lower()

    all_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
    if not all_files:
        print("❌ No data files found!"); return

    print(f"📂 Found {len(all_files)} files. Merging and extracting features...")
    
    X, y = [], []
    for file in all_files:
        df = pd.read_csv(file)
        df['Clean_Action'] = df['Action'].map(ACTION_MAP)
        df = df.dropna(subset=['Clean_Action'])

        for action, group in df.groupby('Clean_Action'):
            for i in range(0, len(group) - 30, 5): # Window size 30, step 5
                window = group.iloc[i:i+30][['Channel_1_Left', 'Channel_2_Right']].values
                X.append(extract_features(window))
                y.append(action)

    X, y = np.array(X), np.array(y)
    
    # 1. Scale the data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 2. Balance the data using SMOTE (Fixes the Wink problem)
    print("⚖️ Balancing Data with SMOTE...")
    smote = SMOTE(random_state=42)
    X_resampled, y_resampled = smote.fit_resample(X_scaled, y)

    # 3. Split and Train Random Forest
    X_train, X_test, y_train, y_test = train_test_split(X_resampled, y_resampled, test_size=0.2, random_state=42)
    
    print("🚀 Training Random Forest...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    acc = accuracy_score(y_test, model.predict(X_test)) * 100
    print(f"\n🏆 TRAINING COMPLETE! Accuracy: {acc:.2f}%")

    # 4. Save specifically for this pilot
    joblib.dump(model, f"{pilot_name}_model.pkl")
    joblib.dump(scaler, f"{pilot_name}_scaler.pkl")
    print(f"💾 Saved as '{pilot_name}_model.pkl' and '{pilot_name}_scaler.pkl'")

if __name__ == '__main__':
    main()