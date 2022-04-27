import os
import re
import random
from flask import Flask, request, abort, jsonify
from flask.globals import current_app
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from sqlalchemy.sql.expression import delete

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    

    start = (page - 1)*QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]

    current_questions = questions[start:end]

    return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  CORS(app)
  

  # '''
  # # @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  # # '''


  # '''
  # @TODO: Use the after_request decorator to set Access-Control-Allow
  # '''
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

  

  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories')
  def show_categories():
    categories = Category.query.order_by(Category.id).all()

    formatted_categories = {
            f"{category.id}": f"{category.type}" for category in categories
        }

    return jsonify({
      'success': True,
      'Category': formatted_categories
      })


  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''

  @app.route('/questions')
  def show_questions():
    selection = Question.query.order_by(Question.id).all()

    current_questions = paginate_questions(request, selection)

    if len(current_questions) == 0:
      abort(404)

    return jsonify({
      'success':True,
      "questions": current_questions,
      "total_questions": len(selection),
      "categories": show_categories().json["Category"],
      "current_category": None,
    })

  # @app.route("/questions")
  # def show_questions():
  #     """
  #     GET request to retrieve list of all questions.
  #     Returns: A json response with the following contents:
  #     - A list of 10 questions.
  #     - The total number of questions.
  #     - The categories available.
  #     - The current category (default = None).
  #     """
  #     questions = Question.query.order_by(Question.id).all()
  #     paginated_questions = paginate_questions(request ,questions)
  #     if len(paginated_questions) == 0:
  #         abort(404)

  #     return jsonify(
  #         {
  #             "questions": paginated_questions,
  #             "total_questions": len(questions),
  #             "categories": show_categories().json["categories"],
  #             "current_category": None,  # According to a mentor in https://knowledge.udacity.com/questions/82424.
  #         }
  #     )

  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''

  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    question = Question.query.filter(Question.id == question_id).one_or_none()

    if question is None:
      abort(404)
    
    question.delete()
    return jsonify({
      'success': True,
      'deleted_question_id': question_id,
      'total_questions': len(Question.query.all())
    })

  '''
  Done
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''

  @app.route('/questions', methods=['POST'])
  def new_questions():
    body = request.get_json()

    question = body.get('question', None)
    answer = body.get('answer', None)
    category = body.get('category', None)
    difficulty = body.get('difficulty', None)
    search = body.get('search', None)

    try:
      if search:
        selection = Question.query.order_by(Question.id).filter(Question.question.ilike('%{}%'.format(search)))
        current_question= paginate_questions(request, selection)
        if len(current_question) == 0:
          abort(404)

        return jsonify({
          'success': True,
          'Question': current_question,
          'total_question': len(selection.all())
        })
      else:
        new_question = Question(question=question, answer=answer, category=category, difficulty=difficulty)

        new_question.insert()

        return jsonify({
          'success': True,
          'question_ID': new_question.id,
          'total_questions': len(Question.query.all())
        })
    except:
      abort(404)


  '''
  Done
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  

  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''

  @app.route('/categories/<int:category_id>/questions')
  def questions_in_categories(category_id):
    selection = Question.query.order_by(Question.id).filter(Question.category == str(category_id)).all()

    current_questions = paginate_questions(request, selection)

    return jsonify({
      'success':True,
      "questions": current_questions,
      "total_questions": len(selection),
      "current_category": Category.query.get(category_id).type,
    })

  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''

  @app.route("/quizzes", methods=['POST'])
  def play():
    """
    POST request to play the trivia game.
    Returns:
        - A random question from a chosen category, or from all categories.
        - A list of previous questions ids, to ensure to repetition.
    """
    request_payload = request.get_json()
    category = request_payload["quiz_category"]
    previous_questions = request_payload["previous_questions"]
    if category["id"] == 0:  # From all categories.
        while True:
            # FIXME: Ensures no repeated questions, but the application freezes when the questions end.
            random_question = random.choice(Question.query.all())
            if random_question.id not in previous_questions:
                break
    else:
        while True:
            # FIXME: Ensures no repeated questions, but the application freezes when the questions end.
            random_question = random.choice(
                Question.query.filter(Question.category == category["id"]).all()
            )
            if random_question.id not in previous_questions:
                break
    previous_questions.append(random_question.id)
    return jsonify(
        {
            "question": random_question.format(),
            "previous_questions": previous_questions,
        }
    )



  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''


  @app.errorhandler(404)
  def not_found(error):
      return jsonify({
          "success": False, 
          "error": 404,
          "message": "Not found"
          }), 404


  @app.errorhandler(405)
  def method_not_allowed(error):
    return jsonify({
      'success': False,
      'error': 405,
      'message': 'Method Not Allowed'
    }),405

  @app.errorhandler(400)
  def bad_request(error):
      return jsonify({
        'success': False,
        "error": 400, 
        "message": "BAD REQUEST"
        }), 400

  @app.errorhandler(422)
  def unprocessable(error):
      return jsonify({
        'success': False,
        "error": 422, 
        "message": "UNPROCESSABLE ENTITY"
        }), 422
      
  
  @app.errorhandler(500)
  def server_error(error):
      return jsonify({
        'success': False,
        "error": 500, 
        "message": "SERVER ERROR"
        }), 500

  
  return app

    