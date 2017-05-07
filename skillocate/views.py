from .errorhandler import InvalidUsage
from flask import Flask, request, session, redirect, jsonify, abort, url_for
from flask_cors import CORS
from .services import CustomerService, ProjectService, UserService, EducationService, WorkExperienceService, CertificateService, graph
from urllib.parse import unquote
import itertools
from operator import itemgetter

# Initialize app...
app = Flask(__name__)
CORS(app)

# Setup services...
customerService = CustomerService()
projectService = ProjectService()
userService = UserService()
educationService = EducationService()
workExperienceService = WorkExperienceService()
certificateService = CertificateService()

# Test route
@app.route('/api/v1/hello/')
def hello():
    query = "MATCH (node)<-[r]-(related) RETURN node, COLLECT(DISTINCT related) as relations"
    return jsonify(data=graph.data(query))

# Handle invalid requests
@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

###  USER  ###

# Registers a new user
@app.route('/api/v1/user/register/', methods=['POST'])
def register_user():
    if not userService.register(request):
        raise InvalidUsage('User already exists', status_code=409)
    else:
        return jsonify(data='success')

# Updates a user
@app.route('/api/v1/user/<username>/', methods=['PUT'])
def update_user(username):
    user = userService.update(username, request)
    if user:
        return jsonify(data=user)
    else:
        raise InvalidUsage('No such user', status_code=401)

# Handles a login request
@app.route('/api/v1/user/login/', methods=['POST'])
def login_user():
    # TODO: Bygg denna metoden.
    if userService.verify_password(request):
        return jsonify(data='success')
    else:
        raise InvalidUsage('Invalid password', status_code=401)

# Gets user data
@app.route('/api/v1/user/<username>/', methods=['GET'])
def get_user(username):
    user = userService.get_complete(username)
    if user:
        return jsonify(data=user)
    else:
        raise InvalidUsage('No such user', status_code=401)

@app.route('/api/v1/user/', methods=['GET'])
def get_all_users():
    return jsonify(data=userService.get_all())

# Get all user's projects
@app.route('/api/v1/user/<username>/project/', methods=['GET'])
def get_user_projects(username):
    projects = userService.get_projects(username)

    if projects:
        return jsonify(data=projects)
    else:
        raise InvalidUsage('No such user', status_code=404)

# Get all user's educations
@app.route('/api/v1/user/<username>/education/', methods=['GET'])
def get_user_educations(username):
    educations = userService.get_educations(username)

    if educations:
        return jsonify(data=educations)
    else:
        raise InvalidUsage('No such user', status_code=404)

# Get all user's workexperience
@app.route('/api/v1/user/<username>/workexperience/', methods=['GET'])
def get_user_workexperience(username):
    raise InvalidUsage('Not yet implemented', status_code=501)

# Get all user's certificates
@app.route('/api/v1/user/<username>/certificate/', methods=['GET'])
def get_user_certificates(username):
    raise InvalidUsage('Not yet implemented', status_code=501)

# Assigns a user to a specific project
@app.route('/api/v1/user/<username>/project/<id>/', methods=['POST'])
def assign_project(username,id):
    return jsonify(data=userService.assign_project(username, id))

# Unassigns a user from a specific project
@app.route('/api/v1/user/<username>/project/<id>/', methods=['DELETE'])
def unassign_project(username, id):
    raise InvalidUsage('Not yet implemented', status_code=501)

# Creates a workexperience and relates it to a user
@app.route('/api/v1/user/<username>/workexperience/', methods=['POST'])
def add_user_workexperience(username):
    raise InvalidUsage('Not yet implemented', status_code=501)

# Creates a certificate and relates it to a user
@app.route('/api/v1/user/<username>/certificate/', methods=['POST'])
def add_user_certificate(username):
    raise InvalidUsage('Not yet implemented', status_code=501)

# Creates an education and relates it to a user
@app.route('/api/v1/user/<username>/education/', methods=['POST'])
def add_user_education(username):
    education = userService.create_education(username, request)
    if education:
        return jsonify(data=education)
    else:
        raise InvalidUsage('No such user', status_code=404)

# Sets tags for a specific user. Replaces all current tags.
@app.route('/api/v1/user/<username>/tag/', methods=['POST'])
def tag_user(username):
    return jsonify(data=userService.set_tags(username=username, request=request))

##############################################################
###########################  /USER  ###########################
###############################################################


###############################################################
########################  EDUCATION  ##########################
###############################################################

# Gets data from a specific education
@app.route('/api/v1/education/<id>/', methods=['GET'])
def get_education(id):
    education = educationService.get(id)
    if not education:
        raise InvalidUsage('No such education exists', status_code=404)
    else:
        return jsonify(data=education)

# Gets data for all educations
@app.route('/api/v1/education/', methods=['GET'])
def get_all_educations():
    return jsonify(data=educationService.get_all())

# Updates an education
@app.route('/api/v1/education/<id>/', methods=['PUT'])
def update_education(id):
    raise InvalidUsage('Not yet implemented', status_code=501)

# Deletes an education
@app.route('/api/v1/education/<id>/', methods=['DELETE'])
def delete_education(id):
    raise InvalidUsage('Not yet implemented', status_code=501)


# Sets tags for a specific education. Replaces all current tags.
@app.route('/api/v1/education/<id>/tag/', methods=['POST'])
def tag_education(id):
    return jsonify(data=educationService.set_tags(id=id, request=request))

###############################################################
########################  /EDUCATION  #########################
###############################################################



###############################################################
######################  WORKEXPERIENCE  #######################
###############################################################

# Gets data from a specific workexperience
@app.route('/api/v1/workexperience/<id>/', methods=['GET'])
def get_workexperience(id):
    workexperience = workExperienceService.get(id)
    if not workexperience:
        raise InvalidUsage('No such workexperience exists', status_code=404)
    else:
        return jsonify(data=workexperience)

# Gets data for all workexperience
@app.route('/api/v1/workexperience/', methods=['GET'])
def get_all_workexperience():
    return jsonify(data=workExperienceService.get_all())

# Updates a workexperience
@app.route('/api/v1/workexperience/<id>/', methods=['PUT'])
def update_workexperience(id):
    raise InvalidUsage('Not yet implemented', status_code=501)

# Deletes a workexperience
@app.route('/api/v1/workexperience/<id>/', methods=['DELETE'])
def delete_workexperience(id):
    raise InvalidUsage('Not yet implemented', status_code=501)

# Sets tags for a specific workexperience. Replaces all current tags.
@app.route('/api/v1/workexperience/<id>/tag/', methods=['POST'])
def tag_workexperience(id):
    raise InvalidUsage('Not yet implemented', status_code=501)

###############################################################
######################  /WORKEXPERIENCE  ######################
###############################################################



###############################################################
######################## CERTIFICATE  #########################
###############################################################

# Gets data from a specific certificate
@app.route('/api/v1/certificate/<id>/', methods=['GET'])
def get_certificate(id):
    certificate = certificateService.get(id)
    if not certificate:
        raise InvalidUsage('No such certificate exists', status_code=404)
    else:
        return jsonify(data=certificate)

# Gets data for all certificate
@app.route('/api/v1/certificate/', methods=['GET'])
def get_all_certificate():
    return jsonify(data=certificateService.get_all())

# Updates a certificate
@app.route('/api/v1/certificate/<id>/', methods=['PUT'])
def update_certificate(id):
    raise InvalidUsage('Not yet implemented', status_code=501)

# Deletes a certificate
@app.route('/api/v1/certificate/<id>/', methods=['DELETE'])
def delete_certificate(id):
    raise InvalidUsage('Not yet implemented', status_code=501)

# Sets tags for a specific certificate. Replaces all current tags.
@app.route('/api/v1/certificate/<id>/tag/', methods=['POST'])
def tag_certificate(id):
    raise InvalidUsage('Not yet implemented', status_code=501)

###############################################################
######################## /CERTIFICATE  ########################
###############################################################




###############################################################
########################## CUSTOMER  ##########################
###############################################################

# Creates a customer
@app.route('/api/v1/customer/', methods=['POST'])
def create_customer():
    return jsonify(data=customerService.create(request))

# Updates a customer
@app.route('/api/v1/customer/<id>/', methods=['PUT'])
def update_customer(id):
    raise InvalidUsage('Not yet implemented', status_code=501)

# Gets data for a specific customer
@app.route('/api/v1/customer/<id>/', methods=['GET'])
def get_customer(id):
    customer = customerService.get(id)
    if not customer:
        raise InvalidUsage('No such customer exists', status_code=404)
    else:
        return jsonify(data=customer)

# Gets all customer data
@app.route('/api/v1/customer/', methods=['GET'])
def get_customers():
    return jsonify(data=customerService.get_all())

# Creates a project and relates it to a customer.
@app.route('/api/v1/customer/<id>/project/', methods=['POST'])
def request_project(id):
    return jsonify(data=customerService.create_project(id, request))


# Sets tags for a specific customer. Replaces all current tags.
@app.route('/api/v1/customer/<id>/tag/', methods=['POST']) 
def tag_customer(id):
    return jsonify(data=customerService.set_tags(id=id, request=request))

###############################################################
######################### /CUSTOMER  ##########################
###############################################################




###############################################################
########################### PROJECT  ##########################
###############################################################
# REMOVED
# # Creates a project
# @app.route('/api/v1/project/', methods=['POST'])
# def create_project():
#     return jsonify(data=projectService.create(request))

# Updates a project
@app.route('/api/v1/project/<id>/', methods=['PUT'])
def update_project(id):
    project = projectService.get(id)
    if not project:
        raise InvalidUsage('No such project exists', status_code=404)
    else:
        return jsonify(data=project)

# Deletes a project
@app.route('/api/v1/project/<id>/', methods=['DELETE'])
def delete_project(id):
    raise InvalidUsage('Not yet implemented', status_code=501)

# Gets data for all projects
@app.route('/api/v1/project/', methods=['GET'])
def get_projects():
    return jsonify(data=projectService.get_all())

# Gets data for a specific project
@app.route('/api/v1/project/<id>/', methods=['GET'])
def get_project(id):
    project = projectService.get(id)
    if not project:
        raise InvalidUsage('No such project exists', status_code=404)
    else:
        return jsonify(data=project)

# Sets tags for a specific project. Replaces all current tags.
@app.route('/api/v1/project/<id>/tag/', methods=['POST'])
def tag_project(id):
    return jsonify(data=projectService.set_tags(id=id, request=request))

###############################################################
########################## /PROJECT  ##########################
###############################################################


@app.route('/api/v1/site-map')
def list_routes():
    output = []
    for rule in app.url_map.iter_rules():

        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)

        methods = ','.join(set(rule.methods) - set(['OPTIONS', 'HEAD']))
        url = url_for(rule.endpoint, **options)
        line = {'rule': unquote(rule.endpoint), 'methods': unquote(methods), 'url': unquote(url)}
        output.append(line)
    
    output.sort(key=itemgetter("url"))
    retval = []
    for key, group in itertools.groupby(output, lambda item: item["url"]):
        retval.append({'url': key, 'methods': ', '.join([item["methods"] for item in group])})

    return jsonify(data=retval)