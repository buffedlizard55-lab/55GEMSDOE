"""55GEMSDOE — tensor-dimensionality lane for the DOE GEMS Prize Challenge.

Modules
-------
io55        grid contract and GeoTIFF I/O (every constant measured, not remembered)
tensor55    FFT gradient tensor, dimensionality index, strike
fields55    NaN fill, micro-levelling, survey-line diagnostics
lanes55     the lane: gated gradient-ridge surface
dti55       exact official distance-weighted Tversky evaluator
holdout55   hide-and-recover folds, emission, coverage-greedy placement
"""
__all__ = ["io55", "tensor55", "fields55", "lanes55", "dti55", "holdout55"]
