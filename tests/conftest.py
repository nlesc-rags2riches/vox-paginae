import matplotlib

# macOS's default backend doubles fig.dpi on a Retina screen; Agg matches CI.
matplotlib.use("Agg")
