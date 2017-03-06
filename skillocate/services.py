from .models import User, Project, Customer, Tag
from py2neo import Graph
from passlib.hash import bcrypt
import os

url = os.environ.get('GRAPHENEDB_BOLT_URL')
username = os.environ.get('GRAPHENEDB_BOLT_USER')
password = os.environ.get('GRAPHENEDB_BOLT_PASSWORD')

graph = Graph(url, username=username, password=password, bolt = True, secure = True, http_port = 24789, https_port = 24780)

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
        customer = Customer.select(graph, primary_value = int(id)).first()
        
        if not customer:
            return None
        else:
            return {"customer" : self.serialize(customer)}
    
    def get_all(self):
        return {"customers" : [self.serialize(customer) for customer in Customer.select(graph)]}

    def create(self, request):
        name = request.json['name']
        city = request.json['city']

        customer = Customer(name, city)
        graph.create(customer)
        
        return {"customer" : self.serialize(customer)}
     
    def serialize(self, customer):
        tags = [tag.__ogm__.node.properties for tags in customer.tags]
        projects = [{"project" : serialize_simple(project)} for project in customer.projects]
        
        data = merge_two_dicts(
            customer.__ogm__.node.properties,
            {"id": customer.__primaryvalue__}
        )
        data = merge_two_dicts(
            data,
            {"tags" : tags}
        )
        data = merge_two_dicts(
            data,
            {"projects" : projects}
        )
        return data

class ProjectService:
    def get(self, id):
        project = Project.select(graph, int(id)).first()
        print(project)
        if not project:
            return None
        else:
            return self.serialize(project)
    
    def get_all(self):
        return {"projects" : [self.serialize(project) for project in Project.select(graph)]}

    def create(self, request):
        title = request.json['title']
        status = request.json['status']
        startdate = request.json['startdate']
        enddate = request.json['enddate']
        hours = request.json['hours']
        customer_id = int(request.json['customer'])
        tags = [tag['name'] for tag in request.json['tags']]

        project = Project(title, status, startdate, enddate, hours)
        customer = Customer.select(graph, customer_id).first()
        project.customer.add(customer)
        for name in tags:
            tag = Tag(name)
            project.tags.add(tag)

        graph.create(project)

        return {"project" : self.serialize(project)}
    
    def add_tags(self, id, request):
        project = Project.select(graph, int(id)).first()

        tags = [tag['name'] for tag in request.json['tags']]

        for name in tags:
            tag = Tag(name)
            project.tags.add(tag)
        
        graph.push(project)

        return {"project" : self.serialize(project)}
    
    def serialize(self, project):
        tags = [tag.__ogm__.node.properties for tag in project.tags]
        customers = [serialize_simple(customer) for customer in project.customer]
        data = merge_two_dicts(
            project.__ogm__.node.properties,
            {"tags" : tags}
        )
        data = merge_two_dicts(
            data,
            {"customer" : customers[0]}
        )
        data = merge_two_dicts(
            data,
            {"id": project.__primaryvalue__}
        )
        return data
    
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