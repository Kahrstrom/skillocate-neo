from .models import UserModel, ProjectModel, EducationModel, TagModel
from py2neo import Graph, authenticate
from passlib.hash import bcrypt
import os
import uuid

url = os.environ.get('GRAPHENEDB_BOLT_URL')
username = os.environ.get('GRAPHENEDB_BOLT_USER')
password = os.environ.get('GRAPHENEDB_BOLT_PASSWORD')
http_url = os.environ.get('GRAPHENEDB_URL')

graph = Graph(http_url, username=username, password=password, bolt = False)
#graph = Graph(url, username=username, password=password, bolt = True, secure = True, http_port = 24789, https_port = 24780)

userModel = UserModel()
projectModel = ProjectModel()
educationModel = EducationModel()
tagModel = TagModel()

class UserService:
    def get(self, username):
        query = """MATCH (n:User)
                   WHERE n.username = '{0}'
                   OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
                   RETURN n, COLLECT(t) AS tags""".format(username)
        user = graph.data(query)

        if not user:
            return None
        else:
            return {"user" : serialize(user[0], userModel.slimRelations, userModel.properties)}

    def get_all(self):
        query = """MATCH (n:User)
                   OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
                   RETURN n, COLLECT(DISTINCT t) AS tags"""
        users = graph.data(query)

        return {"users" : [serialize(user, userModel.slimRelations, userModel.properties) for user in users]}

    def get_complete(self, username):
        query = """MATCH (n:User)
                   WHERE n.username = '{0}'
                   OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
                   OPTIONAL MATCH (p:Project) <- [:ASSIGNED] - (n)
                   OPTIONAL MATCH (e:Education) <- [:ATTENDED] - (n)
                   RETURN n, COLLECT(DISTINCT t) AS tags, COLLECT(DISTINCT p) AS projects,
                   COLLECT(DISTINCT e) AS educations""".format(username)
        user = graph.data(query)

        if not user:
            return None
        else:
            return {"user" : serialize(user[0], userModel.relations, userModel.properties)}

    def update(self, username, request):
        query = """MATCH (n:User)
                   WHERE n.username = '{0}'
                   OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
                   SET {1}
                   RETURN n, COLLECT(DISTINCT t) AS tags
                """.format(request.json.get('username',''), parse_node_update('n', request.json, userModel.updateProperties))
        user = graph.data(query)
        if not user:
            return None
        else:
            return {"user" : serialize(user[0], userModel.slimRelations, userModel.properties)}

    def get_projects(self, username):
        query = """MATCH (u:User)
                   WHERE u.username = '{0}' 
                   MATCH (n:Projects) <- [:ASSIGNED] -> (u)
                   RETURN n""".format(username)
        projects = graph.data(query)

        if not projects:
            return None
        else:
            return {"projects" : [serialize(project, projectModel.slimRelations, projectModel.properties) for project in projects]}

    def get_educations(self, username):
        query = """MATCH (u:User)
                   WHERE u.username = '{0}' 
                   MATCH (n:Education) <- [:ATTENDED] - (u)
                   RETURN COLLECT(DISTINCT n) AS n""".format(username)
        educations = graph.data(query)

        if not educations:
            return None
        else:
            return {"educations" : [serialize(education, educationModel.slimRelations, educationModel.properties) for education in educations]}

    def get_certificates(self, username):
        query = """MATCH (n:User)
                   WHERE n.username = '{0}' 
                   MATCH (c:Certificate) <- [:CERTIFIED] - (n)
                   RETURN COLLECT(DISTINCT c) AS certificates""".format(username)
        certificates = graph.data(query)

        if not certificates:
            return None
        else:
            return {"certificates" : [serialize(certificate, [], []) for certificate in certificates]}

    def register(self, request):

        query = """MATCH (n:User)
                   WHERE n.username = '{0}'
                   RETURN n""".format(request.json.get('username',{}))

        user = graph.data(query)
        if not user:
            json = request.json
            json['password'] = bcrypt.encrypt(json.get('password'))

            query = """CREATE (n:User {0})
                       RETURN n""".format(parse_request(json, userModel.properties))

            user = graph.data(query)
            return True
        else:
            return False

    def verify_password(self, request):
        user = User.select(graph, primary_value = request.json['username']).first()

        if user:
            return bcrypt.verify(request.json['password'], user.password)
        else:
            return False

    def assign_project(self, username, id):
        query = """MATCH (u:User), (p:Project)
                   WHERE u.username = '{0}'AND p.id = '{1}'
                   CREATE (u) - [:ASSIGNED] -> (p)
                   RETURN p """.format(username, id)
        
        project = graph.data(query)
        if not project:
            return False
        else:
            return True

    def create_education(self, username, request):
        query = """MATCH (u:User)
                   WHERE u.username = '{0}'
                   CREATE (n:Education {1}) <- [:ATTENDED] - (u)
                   RETURN n
                """.format(username, parse_request(add_id(request.json), educationModel.properties))

        education = graph.data(query)
        return {"education" : serialize(education[0],[])}

    def set_tags(self, username, request):
        return set_tags_to_label("username", username, "User", request.json)

class CustomerService:    
    def get(self, id):
        query = """MATCH (n:Customer)
                   WHERE n.id = '{0}'
                   OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
                   OPTIONAL MATCH (p:Project) <- [:REQUESTED] - (n)
                   RETURN n, COLLECT(DISTINCT t) AS tags, COLLECT(DISTINCT p) AS projects
                """.format(id)
        customer = graph.data(query)

        if not customer:
            return None
        else:
            return {"customer" : serialize(customer[0], ['tags', 'projects'])}
    
    def get_all(self):
        query = """MATCH (n:Customer)
                   OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
                   OPTIONAL MATCH (p:Project) <- [:REQUESTED] - (n)
                   RETURN n, COLLECT(DISTINCT t) AS tags, COLLECT(DISTINCT p) AS projects"""
        customers = graph.data(query)

        return {"customers" : [serialize(customer, ['tags', 'projects']) for customer in customers]}

    def create_project(self, id, request):
        query = """MATCH (c:Customer)
                   WHERE c.id = '{0}'
                   CREATE (n:Project {1}) <- [:REQUESTED] - (c)
                   RETURN n
                """.format(id, parse_request(add_id(request.json)))

        project = graph.data(query)
        return {"project" : serialize(project[0],[])}

    def create(self, request):
        query = """CREATE (n:Customer {0})
                   RETURN n""".format(parse_request(add_id(request.json), userModel.properties))
        customer = graph.data(query)
        return {"customer" : serialize(customer[0], ['tags', 'projects'])}

    def set_tags(self, id, request):
        return set_tags_to_label("id", id, "Customer", request.json)

class ProjectService:
    def get(self, id):
        query = """MATCH (n:Project)
                   WHERE n.id = '{0}'
                   OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
                   RETURN n, COLLECT(DISTINCT t) AS tags""".format(id)
        project = graph.data(query)

        
        if not project:
            return None
        else:
            return {"project" : serialize(project[0], projectModel.relations, projectModel.properties)}
    
    def get_all(self):
        query = """MATCH (n:Project)
                   OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
                   RETURN n, COLLECT(DISTINCT t) AS tags"""
        projects = graph.data(query)

        return {"projects" : [serialize(project, projectModel.relations, projectModel.properties) for project in projects]}

    def create(self, id, request):
        query = """CREATE (n:Project {0})
                   RETURN n""".format(parse_request(add_id(request.json), projectModel.properties))
        project = graph.data(query)
        return {"project" : serialize(project[0], projectModel.relations, projectModel.properties)}
    
    def set_tags(self, id, request):
        return set_tags_to_label("id", id, "Project", request.json)

class EducationService:
    def get(self, id):
        query = """MATCH (n:Education)
                   WHERE n.id = '{0}'
                   OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
                   RETURN n, COLLECT(DISTINCT t) AS tags""".format(id)
        education = graph.data(query)

        if not education:
            return None
        else:
            return {"education" : serialize(education[0], educationModel.relations, educationModel.properties)}
    
    def get_all(self):
        query = """MATCH (n:Education)
                   OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
                   RETURN n, COLLECT(DISTINCT t) AS tags"""
        educations = graph.data(query)

        return {"educations" : [serialize(education, ['tags']) for education in educations]}

    def create(self, id, request):
        query = """CREATE (n:Education {0})
                   RETURN n""".format(parse_request(add_id(request.json), educationModel.properties))
        education = graph.data(query)
        return {"education" : serialize(education[0], ['tags'])}
    
    def set_tags(self, id, request):
        return set_tags_to_label("id", id, "Education", request.json)

class WorkExperienceService:
    def get(self, id):
        query = """MATCH (n:WorkExperience)
                   WHERE n.id = '{0}'
                   OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
                   RETURN n, COLLECT(DISTINCT t) AS tags""".format(id)
        workexperience = graph.data(query)

        if not workexperience:
            return None
        else:
            return {"workexperience" : serialize(workexperience[0], ['tags'])}
    
    def get_all(self):
        query = """MATCH (n:WorkExperience)
                   OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
                   RETURN n, COLLECT(DISTINCT t) AS tags"""
        workexperience = graph.data(query)

        return {"workexperience" : [serialize(workexperience, ['tags']) for workexperience in workexperience]}

    def create(self, id, request):
        query = """CREATE (n:WorkExperience {0})
                   RETURN n""".format(parse_request(add_id(request.json))) # TODO: properties
        workexperience = graph.data(query)
        return {"workexperience" : serialize(workexperience[0], ['tags'])}
    
    def set_tags(self, id, request):
        return set_tags_to_label("id", id, "WorkExperience", request.json)

class CertificateService:
    def get(self, id):
        query = """MATCH (n:Certificate)
                   WHERE n.id = '{0}'
                   OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
                   RETURN n, COLLECT(DISTINCT t) AS tags""".format(id)
        certificate = graph.data(query)

        if not certificate:
            return None
        else:
            return {"certificate" : serialize(certificate[0], ['tags'])}
    
    def get_all(self):
        query = """MATCH (n:Certificate)
                   OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
                   RETURN n, COLLECT(DISTINCT t) AS tags"""
        certificate = graph.data(query)

        return {"certificates" : [serialize(certificate, ['tags']) for certificate in certificate]}

    def create(self, id, request):
        query = """CREATE (n:Certificate {0})
                   RETURN n""".format(parse_request(add_id(request.json))) # TODO: properties
        certificate = graph.data(query)
        return {"certificate" : serialize(certificate[0], ['tags'])}
    
    def set_tags(self, id, request):
        return set_tags_to_label("id", id, "Certificate", request.json)

def set_tags_to_label(idproperty, idvalue, label, request):
    query = """MATCH (t:Tag) - [rel:TAGGED] -> (n:{0})
               WHERE n.{1} = '{2}'
               DELETE rel""".format(label, idproperty, idvalue)
    graph.data(query)

    query = """MATCH (n:{0})
               WHERE n.{1} = '{2}'
               WITH n\n""".format(label, idproperty, idvalue)
    
    merges = ["""MERGE (t{0}:Tag {1})
                 MERGE (t{0}) - [:TAGGED] -> (n)""".format(index, "{name:'" + tag['name'] + "'}") for index, tag in enumerate(request['tags'])]
    merges = "\n".join(merges)

    query = """
            {0}
            {1}
            WITH n
            OPTIONAL MATCH (t:Tag) - [:TAGGED] -> (n)
            RETURN n, COLLECT(DISTINCT t) AS tags
            """.format(query, merges)
    
    print(query)
    node = graph.data(query)
    return {"{0}".format(label).lower() : serialize(node[0],['tags'])}

def parse_request(json, properties = []):
    values = ["{0} : '{1}'".format(key, json.get(key, '')) for key in properties]
    return "{" + ", ".join(values) + "}"

# TODO: Ta bort!
def serialize_simple(item):
    data = merge_two_dicts(
        item.__ogm__.node.properties,
        {"tags" : [tag.__ogm__.node.properties for tag in item.tags]}
    )
    return merge_two_dicts(
        data,
        {"id": item.__primaryvalue__}
    )

def serialize(node, relations, properties):
    data = {}
    for key in properties:
        data = merge_two_dicts(
            data,
            {key: node['n'].get(key,'')}
        )
    
    for relation in relations:
        data = merge_two_dicts(
            data,
            {relation : node[relation] if (relation in node and node[relation]) else []}
        )
    return data

def parse_node_update(node, json, properties):
    values = ["{0}.{1} = '{2}'".format(node, key, escape(json.get(key, ''))) for key in properties]
    return ", ".join(values)

def merge_two_dicts(x, y):
    """Given two dicts, merge them into a new dict as a shallow copy."""
    z = x.copy()
    z.update(y)
    return z

def escape(value):
    return str(value).replace("'",r"\'")

def add_id(json):
    id = str(uuid.uuid4())[:8]
    return merge_two_dicts(json, {'id' : id})
