# science/spectrometer python deps (pandas, scipy, matplotlib, numpy floors).
# pip, not apt: apt's matplotlib/scipy are built against the numpy 1.x ABI and
# fail to import ("numpy.core.multiarray failed to import") next to numpy 2.x.
pip3 install --no-cache-dir -r "$ROVERFLAKE_ROOT/src/rover_hmi_core/scripts/spectrometer/requirements.txt"
