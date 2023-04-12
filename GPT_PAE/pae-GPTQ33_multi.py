import argparse
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import re
import glob
import numpy as np

def draw_heatmap(file_path, cmap='bwr', output_prefix=None, threshold=None):

    # Get the output prefix based on input file name if not provided
    #if output_prefix is None:
    #    rank_number = int(re.search(r'rank_(\d+)_', file_path).group(1))
    #    output_prefix = f"rank_{rank_number:04d}"

    try:
        # テキストファイルからデータをデータフレームに読み込みます。
        df = pd.read_csv(file_path, delimiter='\t')
        print("Dataframe loaded:")
        print(df.head())
        maxi=df['i'].max()+1

        if threshold is not None:
            filtered_df = df[(df['i'] <= threshold) & (df['j'] > threshold)]
            avg_pae_ij = filtered_df['pae_ij'].mean()
            avg_pae_ji = filtered_df['pae_ji'].mean()
            sum_p_cbcb = filtered_df['p(cbcb<8)'].sum()
            sum_p_cbcb_div_threshold = sum_p_cbcb / threshold
            sum_p_cbcb_div_i_max_minus_threshold = sum_p_cbcb / (maxi-threshold)

            print(f"Average pae_ij for i < {threshold} and j > {threshold}: {avg_pae_ij}")
            print(f"Average pae_ji for i < {threshold} and j > {threshold}: {avg_pae_ji}")
            print(f"Sum p(cbcb<8) / threshold for i < {threshold} and j > {threshold}: {sum_p_cbcb_div_threshold}")
            print(f"Sum p(cbcb<8) / (i_max - threshold) for i < {threshold} and j > {threshold}: {sum_p_cbcb_div_i_max_minus_threshold}")
            print(maxi)

        if threshold is not None:
            filtered_df = df[(df['i'] <= threshold) & (df['j'] > threshold)]
            i_mean_values = filtered_df.groupby('i')['p(cbcb<8)'].sum()
            j_mean_values = filtered_df.groupby('j')['p(cbcb<8)'].sum()

            suffix_i = f"{int(sum_p_cbcb_div_threshold * 100):03d}"
            suffix_j = f"{int(sum_p_cbcb_div_i_max_minus_threshold * 100):03d}"
            
            plt.figure(figsize=(10, 6))
            i_mean_values.plot(kind='bar')
            plt.xlabel('i')
            plt.ylabel('Sum p(cbcb<8)')
            plt.title('Sum p(cbcb<8) for i < threshold and j > threshold (Grouped by i)')
            plt.xticks(range(0, len(i_mean_values), 10), i_mean_values.index[::10])
            plt.savefig(f'{output_prefix}_i_sum_bar_{suffix_i}.png')

            plt.figure(figsize=(10, 6))
            j_mean_values.plot(kind='bar')
            plt.xlabel('j')
            plt.ylabel('Sum p(cbcb<8)')
            plt.title('Sum p(cbcb<8) for i < threshold and j > threshold (Grouped by j)')
            plt.xticks(range(0, len(j_mean_values), 10), j_mean_values.index[::10])
            plt.savefig(f'{output_prefix}_j_sum_bar_{suffix_j}.png')


        # iとjの軸でピボットし、pae_ijとpae_jiを値とするヒートマップ用のデータフレームを作成します。
        heatmap_df_ij = df.pivot(index="i", columns="j", values="pae_ij")
        heatmap_df_ji = df.pivot(index="j", columns="i", values="pae_ji")

        # NaNを0に置き換えます。
        heatmap_df_ij.fillna(0, inplace=True)
        heatmap_df_ji.fillna(0, inplace=True)

        # インデックスと列を1から始めるように調整します。
        index_range = range(1, heatmap_df_ij.index.max()+1)
        column_range = range(1, heatmap_df_ij.columns.max()+1)
        heatmap_df_ij = heatmap_df_ij.reindex(index=index_range, columns=column_range, fill_value=0)
        index_range = range(1, heatmap_df_ji.index.max()+1)
        column_range = range(1, heatmap_df_ji.columns.max()+1)
        heatmap_df_ji = heatmap_df_ji.reindex(index=index_range, columns=column_range, fill_value=0)

        combined_heatmap_df = heatmap_df_ij.add(heatmap_df_ji)

        # Save combined heatmap dataframe to CSV
        combined_heatmap_df.to_csv(f"{output_prefix}_combined_heatmap.csv")
        print(f"Combined heatmap dataframe saved to {output_prefix}_combined_heatmap.csv")
        
        print("Adjusted heatmap dataframe:")
        print(heatmap_df_ij.head())
        print(heatmap_df_ji.head())
        print(combined_heatmap_df.head())

        # ヒートマップを描画します。
        plt.figure(figsize=(10, 8))
        sns.heatmap(combined_heatmap_df, annot=False, fmt='.3f', cmap=cmap, linewidths=0, square=True, vmin=0, vmax=31)
        plt.axhline(y=threshold, color='black', linewidth=1)  # Add a horizontal line at the threshold
        plt.axvline(x=threshold, color='black', linewidth=1)  # Add a vertical line at the threshold
        plt.title('2D Heatmap of pae_ij')
        plt.savefig(f"{output_prefix}_2D_heatmap.png")
    except Exception as e:
        print(f"An error occurred: {e}")

    return {
        "rank": rank_number,
        "avg_pae_ij": avg_pae_ij,
        "avg_pae_ji": avg_pae_ji,
        "sum_p_cbcb_div_threshold": sum_p_cbcb_div_threshold,
        "sum_p_cbcb_div_i_max_minus_threshold": sum_p_cbcb_div_i_max_minus_threshold
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Draw a 2D heatmap from a text file.')
    parser.add_argument('file_pattern', type=str, nargs='?', default="rank_*_model_*_ptm_seed_*.raw.txt", help='File pattern to match input text files (e.g., "rank_*_model_*_ptm_seed_*.raw.txt")')
    parser.add_argument('--cmap', type=str, default='bwr', help='Color map for the heatmap (default: bwr)')
    parser.add_argument('--threshold', type=int, help='Threshold value for calculating average values')

    args = parser.parse_args()

    # Get the list of input files matching the specified pattern
    input_files = glob.glob(args.file_pattern)

    # Check if there are any matching files
    if not input_files:
        print("No matching input files found.")
        exit(1)

    if args.threshold is None:
        # Read the fasta file and calculate the threshold
        fasta_file_path = os.path.join(os.path.dirname(args.file_pattern), "fasta.txt")
        if os.path.exists(fasta_file_path):
            with open(fasta_file_path, "r") as f:
                content = f.read()
                sequences = content.split(">")[1:]
                first_sequence = sequences[0].split("\n", 1)[1].replace("\n", "")
                args.threshold = len(first_sequence)

    metrics_df = pd.DataFrame(columns=["rank", "avg_pae_ij", "avg_pae_ji", "sum_p_cbcb_div_threshold", "sum_p_cbcb_div_i_max_minus_threshold"])

    # Process each input file
    for file_path in input_files:
        # Get the output prefix based on input file name
        rank_number = int(re.search(r'rank_(\d+)_', file_path).group(1))
        output_prefix = f"rank_{rank_number:04d}"

        metrics = draw_heatmap(file_path, args.cmap, output_prefix, args.threshold)
        metrics_df = pd.concat([metrics_df, pd.DataFrame([metrics])], ignore_index=True)

    # Sort the DataFrame by rank
    metrics_df.sort_values("rank", inplace=True)

    # Create a figure and the first axis (left Y axis)
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot the metrics on the first axis (left Y axis)
    ax1.plot(metrics_df["rank"], metrics_df["avg_pae_ij"], label="Average pae_ij")
    ax1.plot(metrics_df["rank"], metrics_df["avg_pae_ji"], label="Average pae_ji")

    # Set limits and labels for the first axis (left Y axis)
    ax1.set_ylim(0, 31)
    ax1.set_xlabel("Rank")
    ax1.set_ylabel("Average pae")
    ax1.legend(loc="upper left")

    # Create the second axis (right Y axis) with a shared X axis
    ax2 = ax1.twinx()

    # Plot the metrics on the second axis (right Y axis)
    ax2.plot(metrics_df["rank"], metrics_df["sum_p_cbcb_div_threshold"], label="Sum p(cbcb<8) / threshold", linestyle="--", color="tab:orange")
    ax2.plot(metrics_df["rank"], metrics_df["sum_p_cbcb_div_i_max_minus_threshold"], label="Sum p(cbcb<8) / (i_max - threshold)", linestyle="--", color="tab:green")

    # Set limits and labels for the second axis (right Y axis)
    ax2.set_ylim(0, 1)
    ax2.set_ylabel("Sum p(cbcb<8)")
    ax2.legend(loc="upper right")

    # Set the title for the plot
    plt.title("Metrics by Rank")

    # Save the plot to a file
    plt.savefig(f"rank_{rank_number:04d}_metrics_by_rank.png")

