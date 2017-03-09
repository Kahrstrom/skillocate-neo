from .errorhandler import InvalidUsage
from .models import User, Project, Customer, Tag
from flask import Flask, request, session, redirect, jsonify, abort
from .services import CustomerService, ProjectService, UserService, graph

# Initialize app...
app = Flask(__name__)

# Setup services...
customerService = CustomerService()
projectService = ProjectService()
userService = UserService()

@app.route('/api/v1/hello')
def hello():
    result = graph.data("MATCH (n:Customer) RETURN n, ID(n) AS id")
    for record in result:
        print(record)
    return jsonify(data=result)

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route('/api/v1/user/register', methods=['POST'])
def register_user():
    if not userService.register(request):
        raise InvalidUsage('User already exists', status_code=409)
    else:
        return jsonify(data='success')

@app.route('/api/v1/user/login', methods=['POST'])
def login_user():
    # TODO: Bygg denna metoden.
    if userService.verify_password(request):
        return jsonify(data='success')
    else:
        raise InvalidUsage('Invalid password', status_code=401)

@app.route('/api/v1/user/<username>/projects', methods=['GET'])
def get_user_projects(username):
    projects = userService.get_projects(username)

    if projects:
        return jsonify(data=projects)
    else:
        raise InvalidUsage('No such user', status_code=404)

@app.route('/api/v1/user/<username>/project/<id>', methods=['POST'])
def assign_user_project(username, id):
    raise InvalidUsage('Not yet implemented', status_code=501)

@app.route('/api/v1/customer', methods=['POST'])
def create_customer():
    return jsonify(data=customerService.create(request))

@app.route('/api/v1/customer/<id>', methods=['GET'])
def get_customer(id):
    customer = customerService.get(id)
    if not customer:
        raise InvalidUsage('No such customer exists', status_code=404)
    else:
        return jsonify(data=customer)

@app.route('/api/v1/customers', methods=['GET'])
def get_customers():
    return jsonify(data=customerService.get_all())

@app.route('/api/v1/project', methods=['POST'])
def create_project():
    return jsonify(data=projectService.create(request))

@app.route('/api/v1/project/<id>', methods=['GET'])
def get_project(id):
    project = projectService.get(id)
    if not project:
        raise InvalidUsage('No such project exists', status_code=404)
    else:
        return jsonify(data=project)

@app.route('/api/v1/project/<id>/tag', methods=['POST'])
def tag_project(id):
    return jsonify(data=projectService.add_tags(id=id, request=request))