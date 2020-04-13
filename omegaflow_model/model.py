import common as c
import target_stats as t
import os
import sys
import os.path as osp
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from omegaflow_model.color_rotater import ColorRotater

data = {
    'F1': osp.join(c.env.get_stat_dir(), 'f1_base-full'),
    'OoO': osp.join(c.env.get_stat_dir(), 'ooo_4w-full'),
}


def get_tuples(arch: str, targets):
    path = data[arch]
    matrix = {}
    print(path)
    for d in os.listdir(path):
        stat_dir_path = osp.join(path, d)
        if not osp.isdir(stat_dir_path):
            continue
        f = c.find_stats_file(stat_dir_path)
        tup = c.get_stats(f, targets, re_targets=True)
        matrix[d] = tup
    df = pd.DataFrame.from_dict(matrix, orient='index')
    return df


def main():
    f1_matrix = get_tuples('F1', t.model_targets)
    ooo_matrix = get_tuples('OoO', t.ipc_target)
    ooo_matrix.columns = ['ideal_ipc']
    # print(ooo_matrix)
    matrix = pd.concat([f1_matrix, ooo_matrix], axis=1, sort=True)
    matrix['PPI'] = matrix['0.TotalPackets']/matrix['Insts']
    matrix.sort_values(['PPI'], inplace=True)

    matrix = matrix.iloc[::2, :]
    print(matrix)

    fig, ax = plt.subplots()
    fig.set_size_inches(7, 5)

    colors = ColorRotater()

    # vertical line
    for index, row in matrix.iterrows():
        ax.plot((row['PPI'], row['PPI']), (row['ipc'], row['ideal_ipc']),
                color='lightgrey',
                linestyle=':',
                zorder=1)

    # OoO
    ooo = ax.scatter(matrix['PPI'], matrix['ideal_ipc'],   marker='v', color=colors.get(),
                     zorder=3)

    # FF
    ff = ax.scatter(matrix['PPI'], matrix['ipc'],         marker='^', color=colors.get(),
                    zorder=3,
                    )
    objs = [ooo, ff]
    legends = ['IPC in Idealized OoO', 'IPC in Forwardflow']

    # add cycle
    def add_circle(coordinate, text, text_shift, color_inc=1):
        x, y = coordinate
        ax.plot(x, y, 'o', fillstyle='none', markersize=25, color=colors.get(color_inc))
        x_s, y_s = text_shift
        plt.text(x+x_s, y+y_s, text,
                 horizontalalignment='center',
                 verticalalignment='bottom',
                 fontsize=12,
                 color=colors.last()
                 )

    add_circle((matrix.loc['cactuBSSN_1']['PPI'], matrix.loc['cactuBSSN_1']['ipc']),
               text='cactuBSSB:\nlow PPI & low IPC',
               text_shift=(-0.1, +0.2),
               )

    bmk = 'imagick'
    add_circle((matrix.loc[f'{bmk}_0']['PPI'], matrix.loc[f'{bmk}_0']['ideal_ipc']),
               text=f'{bmk}:\nmedium PPI & high IPC',
               text_shift=(-0.42, -0.1),
               )

    bmk = 'bwaves'
    add_circle((matrix.loc[f'{bmk}_0']['PPI'] - 0.02, matrix.loc[f'{bmk}_0']['ideal_ipc'] + 0.05),
               text=f'{bmk}:\nhigh PPI & high IPC',
               text_shift=(+0.2, +0.25),
               color_inc=2
               )
    bmk = 'deepsjeng'
    add_circle((matrix.loc[f'{bmk}_1']['PPI'] + 0.02, matrix.loc[f'{bmk}_1']['ideal_ipc'] + 0.1),
               text=f'{bmk}:\nmedium PPI&medium IPC',
               text_shift=(+0.45, -0.05),
               color_inc=2
               )

    start = 1.0
    end = 3.0
    dots = np.arange(start, end, 0.01)

    def draw_model(rate: float, color, ls=None):
        obj, = ax.plot(dots, rate/dots, linestyle=ls, color=color)
        objs.append(obj)
        legends.append(f'IPC=$Rate$/PPI, $Rate$={rate}')
        for index, row in matrix.iterrows():
            if rate/row['PPI'] < row['ideal_ipc']:
                ax.scatter([row['PPI']], [rate/row['PPI']], marker='o', color=color, zorder=2)

    # draw_model(6.0, color=colors[6])
    # draw_model(5.0, color=colors[5])
    # draw_model(4.0, color=colors[4])
    # draw_model(3.5, color=colors[3])
    draw_model(3.1, color=colors.last())
    draw_model(6.0, color=colors.last(), ls='--')
    # draw_model(2.5, color=colors[7])

    ax.set_xlim([start, end])
    ax.set_ylim([0.0, 5.0])

    ax.set_ylabel('IPC', fontsize=14)
    ax.set_xlabel('PPI: pointers per instruction', fontsize=14)
    ax.legend(objs, legends, fontsize=12)
    # plt.plot()
    # plt.show()
    plt.savefig('./figures/model.pdf')


if __name__ == '__main__':
    main()


