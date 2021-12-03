from flask import Flask, render_template
from bokeh.client import pull_session
from bokeh.embed import server_session
import os 


ORBIT_BOKEH_URL = os.environ["ORBIT_BOKEH_URL"]
ORBIT_FLASK_PORT=os.environ["ORBIT_FLASK_PORT"]

app = Flask(__name__)

@app.route('/')
def bkapp_page():

    # pull a new session from aunning Bokeh server
    with pull_session(url=ORBIT_BOKEH_URL) as session:

        # generate a script to load the customized session
        script = server_session(session_id=session.id, url=ORBIT_BOKEH_URL)


        # use the script in the rendered page
        return render_template("embed.html", script=script, template="Flask")

if __name__ == '__main__':
    app.run(port=ORBIT_FLASK_PORT)