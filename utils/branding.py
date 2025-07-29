def add_logo_to_fig(fig, logo_path, position="top right"):
    """
    Add image to Plotly figure layout.
    """
    fig.add_layout_image(
        dict(
            source="data:image/png;base64," + encode_image_to_base64(logo_path),
            xref="paper", yref="paper",
            x=1, y=1,  # top right
            sizex=0.18, sizey=0.18,  # adjust size as needed
            xanchor="right", yanchor="top",
            layer="above"
        )
    )

def encode_image_to_base64(image_path):
    import base64
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()
