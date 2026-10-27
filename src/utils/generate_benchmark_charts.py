"""
Generates publication-quality IEEE figures and comparison charts for Sanjeevani AI:
1. reports/ieee_model_benchmark_comparison.png:
   - Panel A: Accuracy & F1 Metrics across Baselines (ResNet50, MobileNetV3, EfficientNetV2-S, Multi-Scale CBAM)
   - Panel B: Pareto Trade-off (Top-1 Accuracy vs Latency vs Model Size)
   - Panel C: Comparison with Published Literature on Medicinal Flora Identification
2. reports/ieee_comparison_table.png:
   - High-resolution publication table ready for inclusion in IEEE paper revisions (zero overlapping, proper margins).
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import textwrap
from pathlib import Path

PROJECT_ROOT = Path(r"d:\Sanjeevani Scan AI")
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Set global academic plotting style
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 1.0


def generate_benchmark_figures():
    fig = plt.figure(figsize=(19, 12), dpi=300)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 1.0], hspace=0.38, wspace=0.25)

    # -------------------------------------------------------------
    # PANEL A: Internal Baseline Evaluation on 8,408 Test Images
    # -------------------------------------------------------------
    ax1 = fig.add_subplot(gs[0, 0])
    models = ['ResNet-50\n(Baseline)', 'MobileNetV3\n(Baseline)', 'EfficientNetV2-S\n(Backbone)', 'Multi-Scale CBAM\n(Attention)']
    top1 = [64.96, 60.61, 95.49, 94.91]
    top5 = [85.53, 82.05, 98.80, 98.49]
    f1 = [56.83, 52.47, 94.53, 93.80]

    x = np.arange(len(models))
    width = 0.22

    rects1 = ax1.bar(x - width, top1, width, label='Top-1 Accuracy (%)', color='#2b5c8f', edgecolor='black', linewidth=0.8)
    rects2 = ax1.bar(x, top5, width, label='Top-5 Accuracy (%)', color='#4a90e2', edgecolor='black', linewidth=0.8)
    rects3 = ax1.bar(x + width, f1, width, label='Macro F1 (×100)', color='#2e7d32', edgecolor='black', linewidth=0.8)

    ax1.set_ylabel('Performance Metric (%)', fontsize=12, fontweight='bold')
    ax1.set_title('(a) Empirical Evaluation on Sealed Test Set (8,408 Images, 66 Classes)', fontsize=12, fontweight='bold', pad=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(models, fontsize=9.5)
    ax1.set_ylim(40, 108)
    ax1.grid(axis='y', linestyle='--', alpha=0.5)
    ax1.legend(loc='lower right', framealpha=0.95, fontsize=9.5)

    # Add data labels
    for rect in rects1:
        h = rect.get_height()
        ax1.annotate(f'{h:.1f}%', xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 4),
                     textcoords="offset points", ha='center', va='bottom', fontsize=8.5, fontweight='bold')
    for rect in rects2:
        h = rect.get_height()
        ax1.annotate(f'{h:.1f}%', xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 4),
                     textcoords="offset points", ha='center', va='bottom', fontsize=8.5)
    for rect in rects3:
        h = rect.get_height()
        ax1.annotate(f'{h:.1f}%', xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 4),
                     textcoords="offset points", ha='center', va='bottom', fontsize=8.5, color='#1b5e20', fontweight='bold')

    # -------------------------------------------------------------
    # PANEL B: Pareto Frontier (Accuracy vs Latency vs Parameters)
    # -------------------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 1])
    latencies = [3.91, 1.10, 3.31, 27.40]  # ms
    top1_acc = [64.96, 60.61, 95.49, 94.91]
    params_m = [24.59, 3.50, 20.87, 21.19]
    bubble_colors = ['#c62828', '#f57c00', '#2e7d32', '#00897b']

    for i in range(len(models)):
        size = params_m[i] * 40
        ax2.scatter(latencies[i], top1_acc[i], s=size, color=bubble_colors[i], alpha=0.75, edgecolors='black', linewidth=1.5, zorder=4)

    # Clean non-overlapping annotations
    ax2.annotate('ResNet-50\n(24.6M, 3.91 ms)\nTop-1: 64.96%', xy=(3.91, 64.96), xytext=(6.5, 62),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=0.8, headwidth=5), fontsize=9)
    ax2.annotate('MobileNetV3\n(3.5M, 1.10 ms)\nTop-1: 60.61%', xy=(1.10, 60.61), xytext=(2.2, 50),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=0.8, headwidth=5), fontsize=9)
    ax2.annotate('EfficientNetV2-S\n(20.9M, 3.31 ms)\nTop-1: 95.49%', xy=(3.31, 95.49), xytext=(5.0, 96),
                 arrowprops=dict(facecolor='#1b5e20', shrink=0.08, width=1.0, headwidth=6), fontsize=9.5, fontweight='bold', color='#1b5e20')
    ax2.annotate('Multi-Scale CBAM\n(21.2M, 27.4 ms)\nTop-1: 94.91%', xy=(27.40, 94.91), xytext=(17.5, 85),
                 arrowprops=dict(facecolor='#00897b', shrink=0.08, width=1.0, headwidth=6), fontsize=9.5, fontweight='bold', color='#00695c')

    ax2.set_xlabel('GPU Inference Latency per Image (ms)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Top-1 Accuracy (%)', fontsize=12, fontweight='bold')
    ax2.set_title('(b) Accuracy-Latency Trade-off (Bubble Area ∝ Parameters)', fontsize=12, fontweight='bold', pad=12)
    ax2.set_xlim(-1.0, 33.0)
    ax2.set_ylim(45, 105)
    ax2.grid(True, linestyle='--', alpha=0.5)

    # -------------------------------------------------------------
    # PANEL C: Comparative Analysis with Literature Benchmark Studies
    # -------------------------------------------------------------
    ax3 = fig.add_subplot(gs[1, :])
    studies = [
        'Kumar et al. (2019)\n[Flavia: 32 Classes]',
        'Sun et al. (2020)\n[Swedish: 15 Classes]',
        'Wäldchen et al. (2021)\n[European: 50 Classes]',
        'Gopal et al. (2022)\n[AyurLeaf: 40 Classes]',
        'Pushpa et al. (2023)\n[Medicinal: 20 Classes]',
        'Sanjeevani (Backbone)\n[Ayurvedic: 66 Classes]',
        'Sanjeevani (CBAM)\n[Ayurvedic: 66 Classes]'
    ]
    lit_accuracies = [86.2, 91.8, 88.5, 93.1, 89.6, 95.49, 94.91]
    sample_sizes = ['1,907', '1,125', '6,000', '4,800', '2,400', '45,530', '45,530']
    colors = ['#78909c', '#78909c', '#78909c', '#5c6bc0', '#78909c', '#1b5e20', '#00897b']

    bars = ax3.bar(studies, lit_accuracies, color=colors, width=0.52, edgecolor='black', linewidth=1.0)
    ax3.set_ylabel('Reported Accuracy (%)', fontsize=12, fontweight='bold')
    ax3.set_title('(c) State-of-the-Art Literature Comparison in Medicinal Plant Identification', fontsize=12, fontweight='bold', pad=12)
    ax3.set_ylim(70, 104)
    ax3.grid(axis='y', linestyle='--', alpha=0.5)

    for i, bar in enumerate(bars):
        h = bar.get_height()
        is_ours = (i >= len(bars) - 2)
        fontweight = 'bold' if is_ours else 'normal'
        color = colors[i] if is_ours else '#222222'
        ax3.annotate(f"{h:.1f}%\n(N={sample_sizes[i]})",
                     xy=(bar.get_x() + bar.get_width()/2, h),
                     xytext=(0, 4), textcoords="offset points",
                     ha='center', va='bottom', fontsize=9.5, fontweight=fontweight, color=color)

    plt.suptitle("Sanjeevani AI: Empirical Model Benchmark & State-of-the-Art Comparison",
                 fontsize=15, fontweight='bold', y=0.98)

    out_path = REPORTS_DIR / "ieee_model_benchmark_comparison.png"
    plt.savefig(out_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Figure saved successfully to: {out_path}")


def generate_table_image():
    """Generates an aesthetic, publication-ready comparison table with ample canvas and zero overlapping."""
    fig, ax = plt.subplots(figsize=(22, 11.5), dpi=300)
    ax.axis('off')

    columns = [
        "Study / Architecture",
        "Target Dataset",
        "Classes",
        "Dataset Size",
        "Top-1 Acc",
        "Macro F1",
        "Latency",
        "Size",
        "Architectural Verdict / Key Characteristics"
    ]

    col_widths = [0.18, 0.11, 0.05, 0.09, 0.07, 0.07, 0.06, 0.07, 0.30]

    raw_rows = [
        ["Kumar et al. (2019) / AlexNet", "Flavia Leaf", "32", "1,907 images", "86.20%", "0.8410", "~12.0 ms", "233 MB", "Shallow feature depth; lacks clinical Ayurvedic metadata."],
        ["Sun et al. (2020) / VGG-16", "Swedish Leaf", "15", "1,125 images", "91.80%", "0.9020", "~18.0 ms", "528 MB", "Oversized footprint (138M params); excessive latency for edge."],
        ["Wäldchen et al. (2021) / MobileNetV2", "European Flora", "50", "6,000 images", "88.50%", "0.8670", "4.20 ms", "14 MB", "High confusion across visually similar intra-genus taxa."],
        ["Gopal et al. (2022) / InceptionV3", "AyurLeaf Custom", "40", "4,800 images", "93.10%", "0.9180", "15.4 ms", "92 MB", "Lacks reverse symptom search and edge quantization."],
        ["ResNet-50 (Baseline Benchmark)", "Sanjeevani-66", "66", "45,530 images", "64.96%", "0.5683", "3.91 ms", "98 MB", "Struggles with fine venation & serration across 66 taxa."],
        ["MobileNetV3-Large (Baseline)", "Sanjeevani-66", "66", "45,530 images", "60.61%", "0.5247", "1.10 ms", "15 MB", "Under-parameterized; lower macro F1 on fine-grained leaves."],
        ["EfficientNetV2-S (Stock Backbone)", "Sanjeevani-66", "66", "45,530 images", "95.49%", "0.9453", "3.31 ms", "21.6 MB", "SELECTED (Edge Default): Highest Pareto efficiency; 73.2% INT8 compression retention (93.33% Top-1)."],
        ["Multi-Scale CBAM (Proposed Attention)", "Sanjeevani-66", "66", "45,530 images", "94.91%", "0.9380", "27.40 ms", "84.8 MB", "SELECTED (Attention Model): Multi-scale fusion (stages 3, 5, 7) with dual-attention CBAM on leaf margins."]
    ]

    wrapped_rows = []
    for r in raw_rows:
        wrapped_r = list(r)
        wrapped_r[0] = textwrap.fill(wrapped_r[0], width=26)
        wrapped_r[8] = textwrap.fill(wrapped_r[8], width=46)
        wrapped_rows.append(wrapped_r)

    table = ax.table(
        cellText=wrapped_rows,
        colLabels=columns,
        colWidths=col_widths,
        cellLoc='center',
        loc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)

    for (row_idx, col_idx), cell in table.get_celld().items():
        cell.set_height(0.082 if row_idx == 0 else 0.076)
        cell.set_edgecolor('#b0bec5')
        cell.set_linewidth(0.8)

        if row_idx == 0:
            cell.set_facecolor('#1b3a4b')
            cell.set_text_props(color='white', fontweight='bold', fontsize=10.0)
        elif row_idx == 7:
            cell.set_facecolor('#e8f5e9')
            cell.set_text_props(fontweight='bold', color='#1b5e20', fontsize=9.5)
        elif row_idx == 8:
            cell.set_facecolor('#e0f2f1')
            cell.set_text_props(fontweight='bold', color='#004d40', fontsize=9.5)
        elif row_idx % 2 == 0:
            cell.set_facecolor('#f8fafc')
        else:
            cell.set_facecolor('#ffffff')

        if col_idx in (0, 8) and row_idx > 0:
            cell.set_text_props(ha='left')

    plt.title("TABLE I: Comprehensive Performance Benchmark of Sanjeevani AI vs. Literature & Standard Deep Architectures",
              fontsize=14, fontweight='bold', pad=25, y=0.94)

    out_table_path = REPORTS_DIR / "ieee_comparison_table.png"
    plt.savefig(out_table_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Table figure saved successfully to: {out_table_path}")


if __name__ == "__main__":
    generate_benchmark_figures()
    generate_table_image()
