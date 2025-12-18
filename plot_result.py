import os
import itertools
from bokeh.plotting import figure, save, output_file
from bokeh.models import ColumnDataSource, Slider, CustomJS, HoverTool, Toggle
from bokeh.layouts import column, row
from bokeh.palettes import Turbo256, Category10_10
from bokeh.events import Reset

# --- 1. DATA LOADING (Your original logic) ---
print("Loading data...")

all_signals = [] # We will store tuples: (name, data_values, color, line_style)

# A. Load input_data.txt
if os.path.exists("input_data.txt"):
    try:
        with open("input_data.txt", 'r') as f:
            # hex string -> int
            data = [int(line.strip(), 16) for line in f if line.strip()] 
            all_signals.append(("Raw Input (noisy)", data, "black", "dashed"))
    except Exception as e:
        print(f"Error reading input_data.txt: {e}")

# B. Load input_clean.txt
if os.path.exists("input_clean.txt"):
    try:
        with open("input_clean.txt", 'r') as f:
             # hex string -> int
            data = [int(line.strip(), 16) for line in f if line.strip()]
            all_signals.append(("Clean Input", data, "orange", "dashed"))
    except Exception as e:
        print(f"Error reading input_clean.txt: {e}")

# C. Load files from 'files_in' directory
output_dir = "files_in"
if os.path.exists(output_dir):
    files = sorted(os.listdir(output_dir))

    # Create a color iterator for the dynamic files
    # Use Turbo256 if you have many files, or Category10 for fewer
    color_cycle = itertools.cycle(Category10_10) 

    for filename in files:
        filepath = os.path.join(output_dir, filename)
        if not os.path.isfile(filepath):
            continue

        current_signal = []
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    if line.strip():
                        # float string -> float
                        current_signal.append(float(line.strip())) 
        except ValueError:
            print(f"ERROR: converting float in {filepath}")
            continue

        name = (filepath.split('/')[1]).split('.')[0]
        if current_signal:
            # Add to our master list
            all_signals.append((name, current_signal, next(color_cycle), "solid"))
else:
    print(f"Warning: Directory '{output_dir}' does not exist.")

print(f"Loaded {len(all_signals)} signals total.")

# --- 2. BOKEH SETUP ---

# Initialize the figure
p = figure(
    title="FIR Filter Test - Interactive Comparison",
    # width=1200, height=700,
    sizing_mode="scale_both",
    tools="pan,wheel_zoom,reset,save",
    active_scroll="wheel_zoom",
    x_axis_label="Sample Index",
    y_axis_label="Value"
)

sources = {}       # To store references for the JS callback
source_names = []  # To keep track of the order

# Loop through all loaded signals and plot them
for i, (name, y_values, color, style) in enumerate(all_signals):

    # Create x-axis (0, 1, 2, ... N)
    x_values = list(range(len(y_values)))

    # Create a ColumnDataSource
    # y_orig holds the real data, y holds the display data (which moves)
    source = ColumnDataSource(data={
        'x': x_values,
        'y': y_values,
        'y_orig': y_values
    })

    # Unique ID for the source dictionary
    s_name = f"source_{i}"
    sources[s_name] = source
    source_names.append(s_name)

    # Plot the line
    line_renderer = p.line('x', 'y', source=source, 
           legend_label=name, 
           color=color, 
           line_dash=style, 
           line_width=2, 
           alpha=0.8)

    if "noisy" not in name.lower() and "clean input" not in name.lower():
        line_renderer.visible = False

# --- 3. INTERACTIVITY ---

# A. Legend Settings (Click to hide)
p.legend.click_policy = "hide"
p.legend.location = "bottom_right"
p.legend.label_text_font_size = "10pt"
p.legend.background_fill_alpha = 0.6  # 0.0 is invisible, 1.0 is opaque
p.legend.border_line_color = "black"  # Thin black border
p.legend.border_line_width = 1

toggle = Toggle(
    label="Toggle Legend",
    button_type="default",
    margin=(23, 20, 5, 20),
    active=True,
    width=100
)

toggle.js_on_change('active', CustomJS(args=dict(legend=p.legend[0]), code="""
    legend.visible = cb_obj.active;
"""))

# B. Hover Tool (See exact values)
hover = HoverTool(tooltips=[
    ("Signal", "$name"),  # This grabs the name from the legend/line
    ("Index", "@x"),
    ("Value", "@y_orig")  # Shows original value, not the shifted one
])
p.add_tools(hover)

# C. Vertical Stack Slider (The magic part)
callback = CustomJS(
    args=dict(sources=sources, source_names=source_names),
    code="""
        const offset = cb_obj.value;

        // Loop through all sources we stored
        for (let i = 0; i < source_names.length; i++) {
            const s_name = source_names[i];
            const source = sources[s_name];
            const data = source.data;
            const y = data['y'];
            const y_orig = data['y_orig'];

            // Shift the signal: New Y = Old Y + (Index * Offset)
            // 'i' is the index, so the first signal stays put, 
            // the second moves up by 1*offset, the third by 2*offset, etc.

            for (let j = 0; j < y.length; j++) {
                y[j] = y_orig[j] + (i * offset);
            }

            source.change.emit();
        }
    """
)

slider = Slider(
    start=-500, end=500,
    value=0,
    step=10,
    margin=(10, 0, 5, 40),
    title="Vertical Separation (Stack Signals)"
)
slider.js_on_change('value', callback)

reset_handler = CustomJS(args=dict(slider=slider), code="""
    slider.value = 0;
""")

p.js_on_event(Reset, reset_handler)

# --- 4. OUTPUT ---
controls = row(slider, toggle, sizing_mode="stretch_width")
layout = column(controls, p, sizing_mode="scale_both")
output_file("signal_dashboard.html", title="Signal Viewer")
save(layout)

print("Done! Open 'signal_dashboard.html' to view your presentation.")
