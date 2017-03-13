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
        query = """MATCH (n:User)
                   WHERE n.username = '{0}'
                   OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
                   RETURN n, ID(n) AS id, COLLECT(t) AS tags""".format(username)
        user = graph.data(query)

        if not user:
            return None
        else:
            return {"user" : serialize(user[0], ['tags'])}
    
    def get_projects(self, username):
        query = """MATCH (n:User {username: {0}})
                   MATCH (p:Projects) - [:TAGGED] -> (n)
                   RETURN COLLECT(p) AS projects""".format(username)
        projects = graph.data(query)

        if not user:
            return None
        else:
            return {"projects" : [serialize(project) for project in projects]}

    def register(self, request):
        print(request.json.get('username',{}))
        query = """MATCH (n:User)
                   WHERE n.username = '{0}'
                   RETURN n""".format(request.json.get('username',{}))

        user = graph.data(query)
        if not user:
            json = request.json
            json['password'] = bcrypt.encrypt(json.get('password'))
            print(json)
            query = """CREATE (n:User {0})
                       RETURN n, ID(n) AS id""".format(parse_request(json))
            print(query)
            user = graph.data(query)
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
                   WHERE ID(n) = {0}
                   OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
                   OPTIONAL MATCH (p:Project) <- [:REQUESTED] - (n)
                   RETURN n, ID(n) AS id, COLLECT(DISTINCT t) AS tags, COLLECT(DISTINCT p) AS projects
                """.format(id)
        customer = graph.data(query)

        print(customer)
        if not customer:
            return None
        else:
            return {"customer" : serialize(customer[0], ['tags', 'projects'])}
    
    def get_all(self):
        query = """MATCH (n:Customer)
                   OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
                   RETURN n, ID(n) AS id, COLLECT(t) AS tags"""
        customers = graph.data(query)

        return {"customers" : [serialize(customer, ['tags', 'projects']) for customer in customers]}

    def create_project(self, id, request):
        query = """MATCH (c:Customer)
                   WHERE ID(c) = {0}
                   CREATE (n:Project {1}) <- [:REQUESTED] - (c)
                   RETURN n, ID(n) AS id
                """.format(id, parse_request(request.json))
        project = graph.data(query)
        return {"project" : serialize(project[0],[])}

    def create(self, request):
        query = """CREATE (n:Customer {0})
                   RETURN n, ID(n) AS id""".format(parse_request(request.json))
        customer = graph.data(query)
        return {"customer" : serialize(customer[0], ['tags', 'projects'])}

    def set_tags(self, id, request):
        return set_tags_to_label(id, "Customer", request.json)

class ProjectService:
    def get(self, id):
        query = ("MATCH (n:Project) "
                 "OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n) "
                 "WHERE ID(n) = {0} "
                 "RETURN n, ID(n) AS id, COLLECT(DISTINCT t) AS tags").format(id)
        project = graph.data(query)
        print(project)
        if not project:
            return None
        else:
            return {"project" : serialize(project[0], ['tags'])}
    
    def get_all(self):
        query = ("MATCH (n:Project)"
                 "OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)"
                 "RETURN n, ID(n) AS id, COLLECT(DISTINCT t) AS tags")
        projects = graph.data(query)

        return {"projects" : [serialize(project, ['tags','customers']) for project in projects]}

    def create(self, id, request):
        query = """CREATE (n:Project {0})
                   RETURN n, ID(n) AS id""".format(parse_request(request.json))
        project = graph.data(query)
        return {"project" : serialize(project[0], ['tags','customers'])}
    
    def set_tags(self, id, request):
        return set_tags_to_label(id, "Project", request.json)

def set_tags_to_label(id, label, request):
    query = """MATCH (t:Tag) - [rel:TAGGED] -> (n:{0})
               WHERE ID(n) = {1}
               DELETE rel""".format(label,id)
    graph.data(query)

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
            RETURN n, ID(n) AS id, COLLECT(DISTINCT t) AS tags
            """.format(query, merges)

    node = graph.data(query)
    return {"{0}".format(label).lower() : serialize(node[0],['tags'])}

def parse_request(json):
    values = ["{0} : '{1}'".format(key, json[key]) for key in json]
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