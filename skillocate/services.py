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
            return {"user" : self.serialize(user)}
    
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
        query = ("MATCH (c:Customer) "
                 "OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (c) "
                 "WHERE ID(c) = {0} "
                 "RETURN c, ID(c) AS id, collect(t) AS tags").format(id)
        customer = graph.data(query)
        print(customer)
        if not customer:
            return None
        else:
            return {"customer" : self.serialize(customer[0])}
    
    def get_all(self):
        query = ("MATCH (c:Customer)"
                "OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (c)"
                "RETURN c, ID(c) AS id, collect(t) AS tags")
        customers = graph.data(query)

        return {"customers" : [self.serialize(customer) for customer in customers]}

    def create(self, request):
        query = ("CREATE (c:Customer {0}) "
                 "RETURN c, ID(c) AS id").format(parse_request(request))
        customer = graph.data(query)
        return {"customer" : self.serialize(customer[0])}
     
    def serialize(self, customer):
        data = merge_two_dicts(
            customer['c'],
            {"id": customer['id']}
        )
        data = merge_two_dicts(
            data,
            {"tags" : customer['tags'] if ('tags' in customer and customer['tags']) else []}
        )
        data = merge_two_dicts(
            data,
            {"projects" : customer['projects'] if ('projects' in customer and customer['projects']) else []}
        )
        return data

class ProjectService:
    def get(self, id):
        query = ("MATCH (p:Project) "
                 "OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (p) "
                 "WHERE ID(p) = {0} "
                 "RETURN p, ID(p) AS id, collect(t) AS tags").format(id)
        project = graph.data(query)
        print(project)
        if not project:
            return None
        else:
            return {"project" : self.serialize(project[0])}
    
    def get_all(self):
        query = ("MATCH (p:Project)"
                "OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (p)"
                "RETURN p, ID(p) AS id, collect(t) AS tags")
        projects = graph.data(query)

        return {"projects" : [self.serialize(project) for project in projects]}

    def create(self, request):
        query = ("CREATE (p:Project {0}) "
                 "RETURN p, ID(p) AS id").format(parse_request(request))
        project = graph.data(query)
        return {"project" : self.serialize(project[0])}
    
    def add_tags(self, id, request):
        project = Project.select(graph, int(id)).first()

        tags = [tag['name'] for tag in request.json['tags']]

        for name in tags:
            tag = Tag(name)
            project.tags.add(tag)
        
        graph.push(project)

        return {"project" : self.serialize(project)}
    
    def serialize(self, project):
        data = merge_two_dicts(
            project['p'],
            {"id": project['id']}
        )
        data = merge_two_dicts(
            data,
            {"tags" : project['tags'] if ('tags' in project and project['tags']) else []}
        )
        data = merge_two_dicts(
            data,
            {"customers" : project['customers'] if ('projects' in project and project['projects']) else []}
        )
        return data

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

def merge_two_dicts(x, y):
    """Given two dicts, merge them into a new dict as a shallow copy."""
    z = x.copy()
    z.update(y)
    return z