# coding: utf-8

import io
import pandas as pd
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from typing import TYPE_CHECKING
from matplotlib.ticker import FuncFormatter

if TYPE_CHECKING:
    from lib.structs.discord.context import GitBotContext

def _friendly_number_ff(num: int, _) -> str:
    if num >= 1_000_000:
        return f'{num / 1_000_000:.1f}M'
    elif num >= 1_000:
        return f'{num / 1_000:.1f}K'
    else:
        return f'{int(num)}'


def gen_downloads_chart_inmemory(ctx: 'GitBotContext', raw_download_data: list) -> io.BytesIO:
    df = pd.DataFrame({
        'date': pd.to_datetime([item['date'] for item in raw_download_data]),
        'downloads': [item['downloads'] for item in raw_download_data]
    })

    fig = Figure(figsize=(8, 4), dpi=120, facecolor='#111111')
    ax = fig.add_subplot(111)
    ax.set_facecolor('#111111')

    ax.plot(df['date'], df['downloads'], color='#3572a5', linewidth=2)
    ax.set_xlabel(ctx.l.pypi.downloads.glossary[0], color='white')
    ax.set_ylabel(ctx.l.pypi.downloads.glossary[1], color='white')
    ax.tick_params(colors='white')

    for spine in ax.spines.values():
        spine.set_color('#444444')

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m'))

    ax.yaxis.set_major_formatter(FuncFormatter(_friendly_number_ff))

    fig.autofmt_xdate()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    buf.seek(0)
    return buf