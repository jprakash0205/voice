#!venv\Scripts\python

from analytics import *
database.create_tables([PageView], safe=True)
app.run(debug=True,port=PORT)