# lcls-orbit

This repository contains orbit-specific GUI tooling for LCLS.

## Demo

The demo can be run using a port forwarding to the lcls network with `lcls-live` or on the dev network with the proper prod-on-dev EPICS script sourced.


### First, create the `lcls-orbit` conda environment:
An environment file is packaged in examples. This may be used to create an appropriate environment:

```
$ conda env create -f examples/environment.yml
```

Now, activate this environment:
```
$ conda activate lcls-orbit
```

### Configure Remote EPICS access (optional)

The `lcls-live` utility functions allow configuring remote access to EPICS variables. In order to do this, the following environment variables must be set:

| Variable             | Description                          |
|----------------------|--------------------------------------|
| CA_NAME_SERVER_PORT  | Port for forwarding                  |
| LCLS_PROD_HOST       | Production host of process variables |
| SLAC_MACHINE         | Public SLAC machine for forwarding   |
| SLAC_USERNAME        | Username passed to ssh               |
| EPICS_CA_NAME_SERVERS| localhost:$CA_NAME_SERVER_PORT       |

Once evironment variables are set, remote EPICS access may be configured in the bridge shell using the command:

```
$ configure-epics-remote
```

### Launch client
```
$ bokeh serve examples/lcls_orbit_display --port 5006 --show 
```

### Running on mcc-simul

If running on mcc-simul, no remote EPICS configuration is needed. Instead:

Start client process:
```
$ bokeh serve examples/lcls_orbit_display --port 5006 --num-proc 3 &
```

Open port forwarding:
```
$ ssh -fNL 5006:localhost:5006 mcc-simul
```

Using local browser, navigate to http://localhost:5006





# TODO
- [x] Table variable/monitor
- [x] Sample widget
- [x] Example (with lcls-live)
- [ ] Passable labels for z areas
- [ ] Documentation
- [x] dynamic width for markers
- [ ] LUME-EPICS improvement projects. Scalable controller service etc.
- [ ] yaml parsing for table variables
- [x] Hover device names
- [ ] Accelerator layout rendered
- [x] Linked horizontal scaling
- [x] Color maps
- [x] Toggle hard/soft

- [ ] Move beamline toggle into widget

- [x] Functionality to show difference to reference, button to collect reference
- [x] 0 reference button, collect 500
- [ ] Tracked collections
- [ ] Collection status reflected by button
- [x] Plot difference of pv value to the reference
- Toggle referenced view on/off
- [ ] Improve rendering
- [x] Colormap on side
- [ ] Legend for color map
- [ ] (maybe, tbd) Bar showing RMS fluctuations
- [ ] Check out device attributes and report back
- [x] Add more ticks to z
- [ ] Add area fill in for reference collections