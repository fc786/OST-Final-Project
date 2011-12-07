import cgi
import datetime
import urllib
import wsgiref.handlers
import os
from google.appengine.ext.webapp import template

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
class Vote(db.Model):
	voter=db.UserProperty(auto_current_user_add=True)
	answer=db.StringProperty()

class Question(db.Model):
	content = db.StringProperty()
	answers = db.StringListProperty()
	index = db.IntegerProperty()

class Survey(db.Model):
	title = db.StringProperty()
	author = db.UserProperty(auto_current_user_add=True)
	date = db.DateTimeProperty(auto_now_add=True)

class MainPage(webapp.RequestHandler):
	def get(self):
		if users.get_current_user():
			surveys = Survey.all()
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'

			template_values = {
				'surveys': surveys,
				'url': url,
				'url_linktext': url_linktext,
			}
			path = os.path.join(os.path.dirname(__file__), 'index.html')
			self.response.out.write(template.render(path, template_values))
		else:
			self.redirect(users.create_login_url(self.request.uri))
	def post(self):
		#creates survey
		#goes to survey page
		if users.get_current_user():
			survey = Survey()
			survey.author = users.get_current_user()
			survey.title = self.request.get('survey_name')
			survey.put()
			self.redirect('/'+str(survey.key().id()),permanent=True)
		else:
			self.redirect(users.create_login_url(self.request.uri))


class SurveyHandler(webapp.RequestHandler):
	#returns survey page
	def get(self,survey_id):
		user = users.get_current_user()
		if user:			
			survey = Survey.get_by_id(int(survey_id))
			if survey:
				owner = user==survey.author
				questions = db.Query(Question).ancestor(survey)
				question_count = questions.count()
				template_values = {
					'survey_id': survey_id,	
					'survey': survey,
					'questions': questions,
					'owner':owner,
					'question_count':question_count,
				}
				path = os.path.join(os.path.dirname(__file__), 'survey.html')
				self.response.out.write(template.render(path, template_values))				
			else:
				self.redirect("/")
		else:
			self.redirect(users.create_login_url(self.request.uri))

	#posts new question
	def post(self,survey_id):
		user = users.get_current_user()
		if user:			
			survey = Survey.get_by_id(int(survey_id))
			if survey:
				question=Question(parent=survey)
				question.content = self.request.get('survey_question')
				question.index = int(self.request.get('question_number'))+1
				question.answers = []
				for i in range(1, 5):
					answer=self.request.get('survey_answer_'+str(i)).rstrip()
					if answer != "":
						question.answers.append(answer)
				question.put()
				self.redirect("/"+survey_id+"/"+str(question.index),permanent=True)
			else:
				self.redirect("/")
		else:
			self.redirect(users.create_login_url(self.request.uri))

class SurveyDeleteHandler(webapp.RequestHandler):
	#deletes survey, goes back to main page
	def post(self,survey_id):
		survey = Survey.get_by_id(int(survey_id))
		if survey:
			descendants = db.query_descendants(survey)
			for descendant in descendants:
				descendant.delete()
			survey.delete()
			self.redirect('/')
		else:
			self.redirect(users.create_login_url(self.request.uri))


class QuestionHandler(webapp.RequestHandler):
	#returns question page
	def get(self,survey_id,question_id):
		if users.get_current_user():
			path = os.path.join(os.path.dirname(__file__), 'index.html')	
		else:
			self.redirect(users.create_login_url(self.request.uri))

	#adds a vote, goes to nex question
	def post(self,survey_id,question_id):
		if users.get_current_user():
			path = os.path.join(os.path.dirname(__file__), 'index.html')	
		else:
			self.redirect(users.create_login_url(self.request.uri))

class QuestionDeleteHandler(webapp.RequestHandler):
	#deletes survey, goes back to main page
	def post(self,survey_id,question_id):
		survey = Survey.get_by_id(int(survey_id))
		if survey:
			question = db.Query(Question).ancestor(survey).filter('index = ', int(question_id)).get()
			greater_questions = db.Query(Question).ancestor(survey).filter('index > ', int(question_id))
			descendants = db.query_descendants(question)
			for descendant in descendants:
				descendant.delete()
			question.delete()
			for greater_question in greater_questions:
				greater_question.index = greater_question.index - 1
				greater_question.put()
			self.redirect('/'+survey_id)
		else:
			self.redirect(users.create_login_url(self.request.uri))

class ResultsHandler(webapp.RequestHandler):
	#returns results page
	def get(self,survey_id):
		path = os.path.join(os.path.dirname(__file__), 'results.html')
		self.response.out.write(template.render(path, template_values))

application = webapp.WSGIApplication([
  ('/', MainPage),
  (r'/([0-9]*)', SurveyHandler),
  (r'/([0-9]*)/delete', SurveyDeleteHandler),
  (r'/([0-9]*)/results', ResultsHandler),
  (r'/([0-9]*)/([0-9]*)', QuestionHandler),
  (r'/([0-9]*)/([0-9]*)/delete', QuestionDeleteHandler),
], debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()

