# Historical feature band dictionary

This table preserves previously recorded feature descriptions. The authorized feature raster is absent from this checkout, so the tags were not freshly read or authenticated in this review. The canonical local filename defined by `src/gems55/io55.py` is `data/gems-geodawn-numerical-features.tif`; the former `data/training_features.tif` reference was incorrect and the generator is retired. Verify against the authorized DrivenData file before relying on these descriptions.

| band | description (from tag) | category | short name |
|---|---|---|---|
| 1 | Magnetic anomaly - deviation from expected Earth's magnetic field | magnetic_data | `mag_anom - Magnetic anomaly - deviation from expected Earth's magnetic field` |
| 2 | Reduced to pole magnetic data - magnetic anomaly corrected for latitude effects | magnetic_data | `rtp - Reduced to pole magnetic data - magnetic anomaly corrected for latitude effects` |
| 3 | Total magnetic intensity horizontal gradient - rate of change in horizontal direction | magnetic_data | `tmi_hg - Total magnetic intensity horizontal gradient - rate of change in horizontal direction` |
| 4 | Geodetic second invariant - measure of strain rate tensor magnitude | geodetic_strain | `geod_2ndinv - Geodetic second invariant - measure of strain rate tensor magnitude` |
| 5 | Isostatic gravity anomaly slope - gradient of gravity after isostatic correction | gravity_data | `iso_grav_anom_slope - Isostatic gravity anomaly slope - gradient of gravity after isostatic correction` |
| 6 | Tilt angle or total curvature - magnetic field derivative for edge detection | magnetic_data | `tc - Tilt angle or total curvature - magnetic field derivative for edge detection` |
| 7 | Geodetic shear rate - rate of angular deformation from GPS/InSAR | geodetic_strain | `geod_shearrate - Geodetic shear rate - rate of angular deformation from GPS/InSAR` |
| 8 | Geodetic dilatation rate - rate of volumetric strain (expansion/contraction) | geodetic_strain | `geod_dilaterate - Geodetic dilatation rate - rate of volumetric strain (expansion/contraction)` |
| 9 | Total magnetic intensity vertical gradient - rate of change in vertical direction | magnetic_data | `tmi_vg - Total magnetic intensity vertical gradient - rate of change in vertical direction` |
| 10 | Distance to earthquake (n=100km radius, a=15° azimuth parameters) | seismic | `deq_n100a15 - Distance to earthquake (n=100km radius, a=15° azimuth parameters)` |
| 11 | Isostatic gravity anomaly vertical gradient - vertical rate of change | gravity_data | `iso_grav_anom_vg - Isostatic gravity anomaly vertical gradient - vertical rate of change` |
| 12 | Detrended elevation - topography with regional trends removed | topographic | `det_elev - Detrended elevation - topography with regional trends removed` |
| 13 | Isostatic gravity anomaly - gravity after compensating for topographic mass | gravity_data | `iso_grav_anom - Isostatic gravity anomaly - gravity after compensating for topographic mass` |
| 14 | Total magnetic intensity - total strength of magnetic field | magnetic_data | `tmi - Total magnetic intensity - total strength of magnetic field` |
| 15 | Depth to basement surface - thickness of sedimentary cover | subsurface | `depth_to_base_surf - Depth to basement surface - thickness of sedimentary cover` |
| 16 | Earthquake intensity or density (n=100km radius, a=15° parameters) | seismic | `ieq_n100a15 - Earthquake intensity or density (n=100km radius, a=15° parameters)` |
| 17 | Conductivity surface - electrical conductivity of subsurface | subsurface | `cond_surf - Conductivity surface - electrical conductivity of subsurface` |
| 18 | Isostatic gravity anomaly horizontal gradient - horizontal rate of change | gravity_data | `iso_grav_anom_hg - Isostatic gravity anomaly horizontal gradient - horizontal rate of change` |
| 19 | Detrended elevation slope - gradient of elevation after detrending | topographic | `det_elev_slope - Detrended elevation slope - gradient of elevation after detrending` |
