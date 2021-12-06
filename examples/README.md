# LCLS Orbit Display

This folder contains a Bokeh-based orbit display to be used as an alternative to the existing Operator Tool’s Orbit Display with an enhanced feature set. The browser-based display will use Bokeh for serving a plotting application showing both X and Y orbit values along the Z axis, with expanded tooling including subregion zoom, axis manipulation, and hover based inspection of values.

To launch, create an environment using the packaged environment.yml.

```
$ conda env create -f examples/lcls_orbit_display/environment.yml
```

Then, activate the environment:

```
$ conda activate lcls-orbit
```

Now serve the application:

```
$ bokeh serve examples/lcls_orbit_display --show
```
