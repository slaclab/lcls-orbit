


ORBIT_BOKEH_URL=8080
ORBIT_FLASK_PORT= 


bokeh serve --port $ORBIT_BOKEH_PORT --allow-websocket-origin $ORBIT_FLASK_ADDR --allow-websocket-origin $ORBIT_FLASK_ADDR client.py