#!venv\Scripts\python
import os
from  analytics import *
from flask.ext.script import Manager, Shell, Server

manager = Manager(app)

def make_shell_context():
	return dict(app=app)

manager.add_command("shell",Shell(make_context=make_shell_context))
manager.add_command("runserver", Server(host="0.0.0.0", port=5002))

if __name__ == '__main__':
	database.create_tables([PageView], safe=True)
	manager.run()
	database.close()