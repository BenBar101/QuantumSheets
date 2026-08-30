"""
brace.py
--------
Draws the left-edge bracket that groups the qubit staves into one
"system", the way an orchestral/ensemble score groups separate
instrument staves with a square bracket (a piano uses a curly brace
for ONE instrument with two staves; separate wires are more honestly
drawn as a bracketed group of separate staves).
"""


def draw_vertical_brace(ax, x, y_top, y_bottom, depth=0.32, lw=2.4, color="black", zorder=5):
    """
    Draws a '[' shaped bracket spanning from y_top down to y_bottom,
    with its spine at x - depth and small serifs pointing right at
    both ends.
    """
    spine_x = x - depth
    ax.plot([spine_x, spine_x], [y_top, y_bottom], color=color, lw=lw,
             solid_capstyle="round", zorder=zorder)
    ax.plot([spine_x, spine_x + depth], [y_top, y_top], color=color, lw=lw,
             solid_capstyle="round", zorder=zorder)
    ax.plot([spine_x, spine_x + depth], [y_bottom, y_bottom], color=color, lw=lw,
             solid_capstyle="round", zorder=zorder)