import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random, math

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def pagenate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  count = math.ceil((len(selection) / QUESTIONS_PER_PAGE))
  if page > count:
    page = count
  start = (page -1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  quesitons = [question.format() for question in selection]
  current_questions = quesitons[start:end]

  return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  CORS(app)

  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, true')
    response.headers.add('Access-Control-Allow-Methods', 'GET, PATCH, DELETE, POST, OPTIONS')
    response.headers['Access-Control-Allow-Origin'] = ' * '
    
    return response
  
  @app.route('/categories', methods=['GET'])
  def retrieve_categories():
    data = Category.query.order_by(Category.id).all()
    categories = {Category.id: Category.type for Category in data}

    if len(data) == 0:
      abort(404)

    return jsonify({
      'success':True,
      'categories':categories,
      'num_categories': len(data)
    })
 
  @app.route('/questions', methods=['GET'])
  def retrieve_questions():
    data = Question.query.order_by(Question.id).all()
    questions = pagenate_questions(request, data)
    categories = Category.query.order_by(Category.id).all()
    category_dic = {}
    for category in categories:
      category_dic[category.id] = category.type

    if len(questions) == 0 or len(categories) == 0:
      abort(404)

    return jsonify({
      "success": True,
      "questions": questions,
      "total_questions": len(data),
      "categories":category_dic,
      "current_category": None
    })
  
  @app.route('/questions/<int:question_id>', methods = ['DELETE'])
  def delete_question(question_id):
    question = Question.query.get(question_id)
    try:
      if question is None:
        abort(404)

      question.delete()

      return jsonify({
        "success": True,
        "deleted_id":question_id
      })

    except:
      abort(422)

  @app.route('/questions', methods=['POST'])
  def create_search_question():
    body = request.get_json()
    question_value = {}
    question_value['question'] = body.get('question', "")
    question_value['answer'] = body.get('answer', "")
    question_value['difficulty'] = body.get('difficulty', "")
    question_value['category'] = body.get('category', "")
    search = body.get('searchTerm')

    try:
      if search:

        data = Question.query.order_by(Question.id).filter(Question.question.ilike('%{}%'.format(search))).all()
        questions = pagenate_questions(request, data)
        
        return jsonify({
          'success': True,
          'questions': questions,
          'total_questions': len(data),
          'current_category': None
        })
      else:
        keys = question_value.keys()
        for key in keys:
          if question_value[key] == "":
            abort(422)
        question = Question(**question_value)
        question.insert()

        return jsonify({
          'success': True,
          'created_id': question.id
        })

    except:
      abort(422)

  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def retrieve_questions_by_category(category_id):
    category_id = str(category_id)
    data = Question.query.filter(Question.category == category_id).all()
    questions = pagenate_questions(request, data)
    categories = Category.query.all()
    categories = [c.format() for c in categories]

    if len(data) == 0:
      abort(404)

    return jsonify({
      "success": True,
      "questions": questions,
      "total_questions": len(data),
      "categories": categories,
      "current_category": category_id
    })

  @app.route('/quizzes', methods = ['POST'])
  def return_question():
    try:
      body = request.get_json()

      previous_questions = body.get('previous_questions')
      quiz_category = body.get('quiz_category')['id']

      if quiz_category == 0:
        questions = Question.query.filter(Question.id.notin_(previous_questions)).all()
      else:
        questions = Question.query.filter(Question.category == quiz_category, Question.id.notin_(previous_questions)).all()

      if len(questions) == 0:
        question = None 
      else:
        question = questions[random.randint(0, len(questions)-1)].format()

      return jsonify({
        "success": True,
        "question": question
      })
    except:
      abort(500)
  
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False,
      "error": 404,
      "message":"resource not found"
    }), 404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      "success": False,
      "error": 422,
      "message": "unprocessable"
    }), 422

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      "success": False,
      "error": 400,
      "message": "bad request" 
    }), 400
    
  @app.errorhandler(405)
  def   method_not_allowed(error):
    return jsonify({
      "success": False,
      "error": 405,
      "message": "method not allowed"
    }), 405
    
  @app.errorhandler(500)
  def internal_server_error(error):
    return jsonify({
      "success": False,
      "error": 500,
      "message": "internal server error"
    }), 500
  return app
    