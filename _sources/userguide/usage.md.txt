# Using ISOSIMpy

## Using the Executable

In general, using the executable is stricter and less versatile than using the package it is built on. Specifically, the app assumes a certain structure of time series data.

The app is structured into different **Tabs**. Those **Tabs** represent the typical workflow and should be considered in their present order:
1. Tab **Input**: select CSVs for input and target time series (two columns: date, value). Choose monthly or yearly; choose tracer (Tritium / C-14).
2. Tab **Model Design**: check EPM/PM.
3. Tab **Parameters**: edit bounds, initial values, fixed flags, and unit mixes; steady state and warmup.
4. Tab **Simulation**: run simulation or calibration, view plot and results.
