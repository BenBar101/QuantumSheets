import numpy as np
from matplotlib.path import Path
import matplotlib.patches as patches

def draw_vertical_brace(ax, x, y_top, y_bottom, depth=0.8, lw=2.5, color="black", zorder=5):
    """
    Draws a classical curly brace '{' spanning from y_top down to y_bottom,
    with the points extending to the left.
    """
    y_mid = (y_top + y_bottom) / 2.0
    h = y_top - y_bottom
    w = depth
    
    # Outer curve (left edge)
    verts_outer = [
        (x, y_top),
        (x - w*0.9, y_top - h*0.01),
        (x - w*0.2, y_mid + h*0.1),
        (x - w, y_mid),
        (x - w*0.2, y_mid - h*0.1),
        (x - w*0.9, y_bottom + h*0.01),
        (x, y_bottom)
    ]
    
    # Inner curve (right edge) - slightly shifted right to create thickness
    t = 0.25 # thickness at the bulges
    verts_inner = [
        (x, y_bottom),
        (x - w*0.9 + t, y_bottom + h*0.01),
        (x - w*0.2 + t, y_mid - h*0.1),
        (x - w + t/2, y_mid),
        (x - w*0.2 + t, y_mid + h*0.1),
        (x - w*0.9 + t, y_top - h*0.01),
        (x, y_top)
    ]
    
    verts = verts_outer + verts_inner
    codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CURVE4]
    codes += [Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CURVE4]
    
    path = Path(verts, codes)
    patch = patches.PathPatch(path, facecolor=color, edgecolor='none', zorder=zorder)
    ax.add_patch(patch)