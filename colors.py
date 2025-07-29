import matplotlib.pyplot as plt

CATEGORY_OPTIONS = [
    "Anfahren",
    "Reinigen",
    "Process Breakdown",
    "Technical Break Down",
    "Problem",
    "Lösung",
    "Bemerkung",
    "Verbesserungsvorschlag",
    "Versuchsablauf",
]

CATEGORY_COLOR_MAP = {
    "Anfahren": "#B0B0B0",  # grey for neutral
    "Reinigen": "#3498DB",  # blue for cleaning
    "Process Breakdown": "#F39C12",  # orange for process problem
    "Technical Break Down": "#C0392B",  # red for technical problem
    "Problem": "#C0392B",
    "Bemerkung": "#8E44AD",
    "Verbesserungsvorschlag": "#2ECC71",
    "Lösung": "#27AE60",
    "Versuchsablauf": "#16A085",
    # ...add more if needed...
}

def assign_colors(categories):
    palette = plt.cm.tab10.colors
    unique = list(dict.fromkeys(categories))
    return {cat: f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}' 
            for cat, (r, g, b) in zip(unique, palette * (len(unique)//len(palette)+1))}

def get_color(category, color_map):
    return color_map.get(category, "#888888")
