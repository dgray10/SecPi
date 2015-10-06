# web framework
import cherrypy


# our stuff
from tools.db import objects
from tools import config
from base_webpage import BaseWebPage



class ParamsPage(BaseWebPage):
	
	def __init__(self):
		super(ParamsPage, self).__init__(objects.Param)
		self.fields['id'] = {'name':'ID', 'visible':['list']}
		self.fields['object_id'] = {'name':'Object ID', 'visible':['list', 'add', 'update']}
		self.fields['object_type'] = {'name':'Type', 'visible':['list', 'add', 'update']}
		self.fields['key'] = {'name':'Key', 'visible':['list', 'add', 'update']}
		self.fields['value'] = {'name':'Value', 'visible':['list', 'add', 'update']}
		self.fields['description'] = {'name':'Description', 'visible':['list', 'add', 'update']}





