from .models import User, Project, Customer, Tag
from py2neo import Graph, authenticate
from passlib.hash import bcrypt
import os

url = os.environ.get('GRAPHENEDB_BOLT_URL')
username = os.environ.get('GRAPHENEDB_BOLT_USER')
password = os.environ.get('GRAPHENEDB_BOLT_PASSWORD')
http_url = os.environ.get('GRAPHENEDB_URL')

graph = Graph(http_url, username=username, password=password, bolt = False)
#graph = Graph(url, username=username, password=password, bolt = True, secure = True, http_port = 24789, https_port = 24780)

class UserService:
    def get(self, username):
        user = User.select(graph, primary_value = username).first()

        if not user:
            return None
        else:
            return {"user" : serialize(user)}
    
    def get_projects(self, username):
        user = User.select(graph, primary_value = username).first()

        if not user:
            return None
        else:
            return {"projects" : [serialize_simple(project) for project in user.projects]}

    def register(self, request):
        user = User.select(graph, primary_value = request.json['username']).first()

        if not user:
            user= User(username=request.json['username'], password=bcrypt.encrypt(request.json['password']))
            graph.create(user)
            return True
        else:
            return False

    def verify_password(self, request):
        user = User.select(graph, primary_value = request.json['username']).first()
        print(user.password)
        if user:
            return bcrypt.verify(request.json['password'], user.password)
        else:
            return False

class CustomerService:
    
    def get(self, id):
        query = """MATCH (n:Customer)
                   OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
                   WHERE ID(n) = {0}
                   RETURN n, ID(n) AS id, collect(t) AS tags""".format(id)
        customer = graph.data(query)
        print(customer)
        if not customer:
            return None
        else:
            return {"customer" : serialize(customer[0], ['tags', 'projects'])}
    
    def get_all(self):
        query = """MATCH (n:Customer)
                   OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
                   RETURN n, ID(n) AS id, collect(t) AS tags"""
        customers = graph.data(query)

        return {"customers" : [serialize(customer, ['tags', 'projects']) for customer in customers]}

    def create_project(self, id, request):
        return {"project" : ""}

    def create(self, request):
        query = """CREATE (n:Customer {0})
                   RETURN n, ID(n) AS id""".format(parse_request(request))
        customer = graph.data(query)
        return {"customer" : serialize(customer[0], ['tags', 'projects'])}

    def add_tags(self, id, request):
        return add_tags_to_label(id, "Customer", request.json)

class ProjectService:
    def get(self, id):
        query = ("MATCH (n:Project) "
                 "OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n) "
                 "WHERE ID(n) = {0} "
                 "RETURN n, ID(n) AS id, collect(t) AS tags").format(id)
        project = graph.data(query)
        print(project)
        if not project:
            return None
        else:
            return {"project" : serialize(project[0], ['tags','customers'])}
    
    def get_all(self):
        query = ("MATCH (n:Project)"
                 "OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)"
                 "RETURN n, ID(n) AS id, collect(t) AS tags")
        projects = graph.data(query)

        return {"projects" : [serialize(project, ['tags','customers']) for project in projects]}

    def create(self, request):
        query = ("CREATE (n:Project {0}) "
                 "RETURN n, ID(n) AS id").format(parse_request(request))
        project = graph.data(query)
        return {"project" : serialize(project[0], ['tags','customers'])}
    
    def add_tags(self, id, request):
        return add_tags_to_label(id, "Project", request.json)

def add_tags_to_label(id, label, request):
        query = """MATCH (n:{0})
                   WHERE ID(n) = {1}
                   WITH n\n""".format(label, id)
        
        merges = ["""MERGE (t{0}:Tag {1})
                     MERGE (t{0}) - [:TAGGED] -> (n)""".format(index, "{name:'" + tag['name'] + "'}") for index, tag in enumerate(request['tags'])]
        merges = "\n".join(merges)

        query = """
                {0}
                {1}
                WITH n
                OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
                RETURN n, ID(n) AS id, collect(t) AS tags
                """.format(query, merges)

        node = graph.data(query)
        return {"{0}".format(label).lower() : serialize(node[0],['tags'])}

def parse_request(request):
    values = ["{0} : '{1}'".format(key, request.json[key]) for key in request.json]
    return "{" + ", ".join(values) + "}"

def serialize_simple(item):
    data = merge_two_dicts(
        item.__ogm__.node.properties,
        {"tags" : [tag.__ogm__.node.properties for tag in item.tags]}
    )
    return merge_two_dicts(
        data,
        {"id": item.__primaryvalue__}
    )

def serialize(node, relations):
    data = merge_two_dicts(
        node['n'],
        {"id": node['id']}
    )
    for relation in relations:
        data = merge_two_dicts(
            data,
            {relation : node[relation] if (relation in node and node[relation]) else []}
        )
    return data

def merge_two_dicts(x, y):
    """Given two dicts, merge them into a new dict as a shallow copy."""
    z = x.copy()
    z.update(y)
    return z