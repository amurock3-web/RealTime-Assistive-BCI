import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os

# Configuration
DATA_FOLDER = 'dataset/'
EDA_FOLDER = 'eda_reports/'

# Ensure the EDA output folder exists
if not os.path.exists(EDA_FOLDER):
    os.makedirs(EDA_FOLDER)

ACTION_MAP = {
    "==== RELAX ====": "RELAX",
    "==== RELAX YOUR FACE (Gathering Baseline) ====": "RELAX",
    "==== RELAX UNTIL FINISHED ====": "RELAX",
    "==== [ CLENCH JAW ] ====": "JAW_CLENCH",
    "==== [ WINK LEFT EYE ] ====": "LEFT_WINK",
    "==== [ WINK RIGHT EYE ] ====": "RIGHT_WINK",
    "==== [ SQUEEZE BOTH EYES SHUT (Double Blink) ] ====": "DOUBLE_BLINK"
}

def main():
    print("========================================")
    print("    BCI EXPLORATORY DATA ANALYSIS (EDA) ")
    print("========================================\n")
    
    all_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
    if not all_files:
        print("Error: No CSV files found in the 'dataset' folder!")
        return

    print(f"Loading {len(all_files)} files for analysis...")
    df_list = []
    for file in all_files:
        temp_df = pd.read_csv(file)
        temp_df['Source_File'] = os.path.basename(file) # Track which file it came from
        df_list.append(temp_df)
        
    df = pd.concat(df_list, ignore_index=True)
    df['Clean_Action'] = df['Action'].map(ACTION_MAP)
    df = df.dropna(subset=['Clean_Action'])

    print(f"Total Data Points: {len(df)}")
    
    # Set the visual style for the graphs
    sns.set_theme(style="whitegrid", palette="muted")

    # ==========================================
    # GRAPH 1: Data Balance (Class Distribution)
    # ==========================================
    print("Generating Class Distribution Graph...")
    plt.figure(figsize=(10, 6))
    sns.countplot(data=df, y='Clean_Action', order=df['Clean_Action'].value_counts().index, palette="viridis")
    plt.title("Distribution of Recorded Actions (Data Balance)")
    plt.xlabel("Number of Data Points (Rows)")
    plt.ylabel("Action Class")
    plt.tight_layout()
    plt.savefig(f'{EDA_FOLDER}1_class_distribution.png', dpi=300)
    plt.close()

    # ==========================================
    # GRAPH 2: Signal Amplitude by Action (Boxplot)
    # ==========================================
    print("Generating Signal Amplitude Boxplots...")
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    sns.boxplot(data=df, x='Clean_Action', y='Channel_1_Left', ax=axes[0], palette="Blues")
    axes[0].set_title("Channel 1 (Left) Voltage Spread per Action")
    axes[0].tick_params(axis='x', rotation=45)
    
    sns.boxplot(data=df, x='Clean_Action', y='Channel_2_Right', ax=axes[1], palette="Oranges")
    axes[1].set_title("Channel 2 (Right) Voltage Spread per Action")
    axes[1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(f'{EDA_FOLDER}2_signal_amplitude_boxplots.png', dpi=300)
    plt.close()

    # ==========================================
    # GRAPH 3: Baseline vs Action Density (KDE Plot)
    # ==========================================
    print("Generating Baseline vs Action Density (KDE)...")
    plt.figure(figsize=(12, 6))
    
    # Filter for just RELAX and JAW_CLENCH to show the stark difference
    subset = df[df['Clean_Action'].isin(['RELAX', 'JAW_CLENCH'])]
    
    sns.kdeplot(data=subset, x='Channel_1_Left', hue='Clean_Action', fill=True, common_norm=False, palette="Set1", alpha=0.5)
    plt.title("Density of Electrical Signals: RELAX vs JAW_CLENCH (Channel 1)")
    plt.xlabel("Electrical Signal Value")
    plt.ylabel("Density")
    plt.xlim(0, 1023) # Arduino Analog limits
    plt.tight_layout()
    plt.savefig(f'{EDA_FOLDER}3_relax_vs_clench_density.png', dpi=300)
    plt.close()

    # ==========================================
    # GRAPH 4: Time-Series of a Single Trial
    # ==========================================
    print("Generating Time-Series plot for a single trial...")
    sample_file = df['Source_File'].iloc[0] # Grab the first file
    sample_df = df[df['Source_File'] == sample_file]
    
    plt.figure(figsize=(14, 6))
    plt.plot(sample_df['Timestamp'], sample_df['Channel_1_Left'], label='Left Channel', color='blue', alpha=0.8)
    plt.plot(sample_df['Timestamp'], sample_df['Channel_2_Right'], label='Right Channel', color='orange', alpha=0.8)
    
    # Add simple background highlights for different actions
    for action in sample_df['Clean_Action'].unique():
        if action != 'RELAX':
            action_times = sample_df[sample_df['Clean_Action'] == action]['Timestamp']
            if not action_times.empty:
                plt.axvspan(action_times.min(), action_times.max(), color='red', alpha=0.1, label=action if action not in plt.gca().get_legend_handles_labels()[1] else "")

    plt.title(f"Raw Electrical Time-Series: {sample_file}")
    plt.xlabel("Time (Seconds)")
    plt.ylabel("Voltage Reading")
    # Simplify legend
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys(), loc='upper right')
    plt.tight_layout()
    plt.savefig(f'{EDA_FOLDER}4_single_trial_timeseries.png', dpi=300)
    plt.close()

    print(f"\nSUCCESS! 4 Professional EDA graphs have been saved to the '{EDA_FOLDER}' folder.")

if __name__ == '__main__':
    main()