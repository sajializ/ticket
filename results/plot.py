import matplotlib.pyplot as plt
import string

# ─────────────────────────────────────────────────────────────────────────────
# Replace these lists with your real simulation results
payment_sizes     = [1, 2, 3, 4, 5]
balance_splits    = [0.5, 0.6, 0.7, 0.8, 0.9]
shutdown_percents = [10, 20, 30, 40, 50]

# Success rate data
success_dc = [ [100.0, 100.0, 98.21, 91.2, 67.84],
         [100.0, 100.0, 100.0, 99.92, 23.61],
         [84.84, 70.66, 58.77, 47.07, 36.02],
         [95.69, 90.68, 85.9, 80.06, 74.38]]

success_sp = [ [97.53, 96.97, 79.99, 75.05, 41.78],
         [96.25, 93.97, 90.49, 84.63, 16.15],
         [73.05, 58.75, 47.53, 34.76, 24.58],
         [92.33, 83.33, 74.56, 70.12, 66.74]]

success_bfs = [ [98.83, 97.55, 87.71, 77.37, 53.2],
         [97.57, 97.46, 97.2, 96.23, 13.89],
         [70.12, 50.24, 35.92, 24.71, 16.41],
         [89.76, 82.35, 76.01, 68.2, 61.0]]

hops_dc = [ [3.49578, 3.4931, 3.4785867019651766, 3.2047278628130345, 2.8945522080066035],
         [3.49336, 3.4959, 3.496479859194368, 3.4861294583883753, 3.09395120298204],
         [3.4559662439300363, 3.431175521526225, 3.384618002382168, 3.3305009134554107, 3.3017212659633537],
         [3.4820775420629113, 3.4717026907807673, 3.469545983701979, 3.4467787464714847, 3.429070767907077]]

hops_sp = [ [3.99196177743146, 3.9764463236052388, 3.8400010001500227, 3.511565314715131, 3.0925411719647644],
         [3.9736306208960186, 3.9598808130254337, 3.9363879495170524, 3.873171538625139, 3.2606811145510837],
         [3.8765161678942035, 3.8662468085106383, 3.773522975929978, 3.674664825363945, 3.590853608918545],
         [3.9672255437137163, 3.918180727229089, 3.856541216234341, 3.839494551885447, 3.8552635521860297]]

hops_bfs = [ [3.7973571847744703, 3.7863703460718385, 3.746146479387085, 3.539988626376467, 3.2712304048719973],
         [3.7862662703699907, 3.788701469260445, 3.787444186094364, 3.772533615977721, 3.2265591242978537],
         [3.712370575315896, 3.658810414841946, 3.5785400077955343, 3.4917024204646645, 3.4202827888834713],
         [3.7657412771266876, 3.740703859325286, 3.7238403451995685, 3.7008797653958942, 3.6629397685170004]]

delay_dc = [ [218.0288, 219.02246, 218.2655941350168, 185.98600938555327, 162.975826896999],
         [219.01918, 219.2002, 218.78921156846275, 218.772967455266, 200.8613181972213],
         [214.6391259252275, 212.7457046618925, 209.61905734218138, 205.31329396269703, 203.76407551360356],
         [218.97916187689412, 218.4416850463167, 219.21727590221187, 218.34395843221503, 217.08383523338352]]

delay_sp = [ [290.52830807718334, 290.02384242549243, 282.54440666099913, 251.19525129243723, 224.82410953657603],
         [289.891426315352, 288.48428221772906, 285.80582631567313, 280.28062008176386, 247.087306501548],
         [274.63321742463654, 274.8641021276596, 267.5045446894462, 258.6573450716382, 250.81617706892342],
         [290.7983926869422, 283.6810272410896, 280.4999329381153, 278.8776028295967, 285.38506487668934]]

delay_bfs = [ [245.9804723071008, 246.22480318189272, 241.18998540678584, 214.226800392907, 193.44584790045488],
         [246.17603771651122, 246.36509890831488, 246.3126813308916, 245.7599185319118, 218.4001152239666],
         [237.2283008642574, 231.19300899753165, 228.19060081296286, 226.04525216546588, 223.04278400780106],
         [245.1407022859944, 244.8821314939402, 243.64053990054464, 243.1417302052786, 240.6488081576445]]

fee_dc = [ [2993558.23156, 3693407.34958, 3494983.081498829, 7643738.010306565, 236261079.76463652],
         [3667543.5829, 3602906.78772, 3523015.7100484017, 3730881.7813137984, 3536501.005760759],
         [3504606.4102824004, 3717002.7167765857, 2990250.221337417, 3380033.3722224585, 3308872.772348695],
         [3153745.1381544573, 3548862.8226731364, 3682726.9186495924, 3737449.878344283, 3186861.07783932]]

fee_sp = [ [2340597.7854081653, 2205856.9343302054, 3918714.4267140073, 30495627.663300112, 106887093.63103217],
         [2237204.0231277533, 2125308.331701607, 2211480.646243618, 2805763.7181510977, 2021900.9946749227],
         [2386809.984667196, 2275838.9063489363, 2070063.7408264603, 2742911.67909546, 4161012.1664903574],
         [2396800.0474828873, 2722555.25400216, 2360663.1459534857, 3155204.022847852, 3581191.618950586]]

fee_bfs = [ [2409819.341238845, 2868218.5216704938, 4186370.90516691, 25449759.92689862, 261403210.8927108],
         [2828373.2095931126, 2867229.2695559384, 2846275.4492067737, 3293902.4692520313, 1682133.4685294542],
         [2584465.719929262, 3027419.9867823874, 1814174.3291385935, 2202456.27912248, 1259875.7737688932],
         [2587824.432378236, 2730321.2532242, 2575946.418133502, 3309316.565190616, 2892968.282960097]]
# ─────────────────────────────────────────────────────────────────────────────

# Combine sweeps and labels
sweeps_xs     = [payment_sizes, payment_sizes, payment_sizes, payment_sizes]
sweeps_labels = ['Payment Size (sats)', 'Balance Split', 'Channel Silent Disablement', 'Saturated Channels']

# Metrics and their corresponding data
metrics_data = [
    ('Success Rate', success_dc, success_sp, success_bfs),
    ('Average Number of Hops',        hops_dc,    hops_sp,    hops_bfs),
    # ('Average Delay (CLTV)',delay_dc,   delay_sp,   delay_bfs),
    # ('Average Fee (msat)',  fee_dc,     fee_sp,     fee_bfs)
]

# Create a 3×3 grid of subplots
fig, axes = plt.subplots(
    nrows=2, ncols=4,
    figsize=(20, 8),           # you may want a wider figure now
    sharey='row'
)

# Plot styling parameters
algorithms = ['T2R', 'SpeedyMurmurs']
markers    = ['s', 's', '^']
linestyles = ['-', '--', '-.']

# Custom labels for the payment-size bins
payment_labels = [
    '1-100',
    '100-1000',
    '1000-10000',
    '10000-100000',
    '100000-1000000',
]

split_labels = [
    '60%-40%',
    '70%-30%',
    '80%-20%',
    '90%-10%',
    '100%-0%',
]

shutdown_labels = [
    '10%',
    '20%',
    '30%',
    '40%',
    '50%',
]

power_labels = [f'$10^{i}$–$10^{i+1}$' for i in range(2, len(payment_sizes) + 1)]
power_labels.insert(0, '$10^0$–$10^2$')
print(power_labels)
# Generate subplot prefixes a, b, c, …
subplot_labels = list(string.ascii_lowercase[:26])
colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
colors = ['#512e5f', '#b7950b']

# … all your imports and data definitions up here …

# Combine sweeps and labels
sweeps_xs     = [payment_sizes, payment_sizes, payment_sizes, payment_sizes]
sweeps_labels = ['Payment Size (sats)', 'Balance Split (%)', 'Channel Silent Disablement (%)', 'Saturated Channels (%)']

# Metrics and their corresponding data
metrics_data = [
    ('Success Rate',          success_dc, success_sp, success_bfs),
    ('Average Number of Hops',hops_dc,    hops_sp,    hops_bfs),
    # add more metrics here if you like…
]

markers    = ['s', 's']
linestyles = ['-', '--']
colors     = ['#512e5f', '#b7950b']

for metric_label, dc_list, sp_list, bfs_list in metrics_data:
    # new figure for each metric
    fig, axes = plt.subplots(
        nrows=2, ncols=2,
        figsize=(12, 9),
        
    )
    axes = axes.flatten()
    for j, (xs, xs_label) in enumerate(zip(sweeps_xs, sweeps_labels)):
        ax = axes[j]
        # plot your two algorithms
        ax.plot(xs, dc_list[j],
                marker=markers[0], linestyle=linestyles[0],
                linewidth=3, markersize=8, color=colors[0],
                label='T2R')
        ax.plot(xs, sp_list[j],
                marker=markers[1], linestyle=linestyles[1],
                linewidth=3, markersize=8, color=colors[1],
                label='SpeedyMurmurs')
        # ax.set_ylim([1.93, 4.57])
        ax.set_ylim([0, 105])

        # set the proper xticks/labels per sweep
        if xs_label == 'Payment Size (sats)':
            ax.set_xticks(payment_sizes)
            ax.set_xticklabels(power_labels)
        elif xs_label == 'Balance Split (%)':
            ax.set_xticks(payment_sizes)
            ax.set_xticklabels(split_labels)
        elif xs_label == 'Channel Silent Disablement (%)':
            ax.set_xticks(payment_sizes)
            ax.set_xticklabels(shutdown_labels)
        elif xs_label == 'Saturated Channels (%)':
            ax.set_xticks(payment_sizes)
            ax.set_xticklabels(shutdown_labels)

        # title and axes labels
        ax.set_title(f'{chr(97 + j)}) {metric_label} vs {xs_label}', fontsize=14)
        ax.set_xlabel(xs_label, fontsize=14)
        ax.set_ylabel(metric_label, fontsize=14)
        ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

    # add a shared legend above the row
    handles, labels = axes[0].get_legend_handles_labels()
    # fig.legend(handles, ['Ticket', 'SpeedyMurmurs'],
    #            loc='upper center', ncol=2, frameon=False, fontsize=14)
    handles, labels = axes[0].get_legend_handles_labels()
    # fig.subplots_adjust(top=0.85)
    fig.legend(handles, labels,
               loc='upper center',
               ncol=2,
               bbox_to_anchor=(0.5, 1.0),
               frameon=False,
               fontsize=18)

    fig.tight_layout(rect=[0, 0, 1, 0.92])
    # fig.suptitle(metric_label, fontsize=16)
    for ax in axes.flatten():
        for spine in ax.spines.values():
            spine.set_linewidth(2.5)
    # for ax in axes.flat:
        # ax.label_outer()
    
    fig.savefig(f"{metric_label.replace(' ', '_').lower()}_lowres.png")
    plt.show()
