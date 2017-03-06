from py2neo.ogm import GraphObject, Property, RelatedTo, RelatedFrom
from time import time

class User(GraphObject):
    __primarykey__ = "username"

    username = Property()
    password = Property()
    firstname = Property()
    lastname = Property()
    mobilephone = Property()
    email = Property()
    address = Property()
    city = Property()
    zipcode = Property()

    projects = RelatedTo("Project", "ASSIGNED")
    educations = RelatedTo("Education", "ATTENDED")
    workexperience = RelatedTo("WorkExperience", "EMPLOYED")
    certificates = RelatedTo("Certificate", "CERTIFIED")
    tags = RelatedFrom("Tag","TAGGED")

    def __init__(self, 
            username,
            password,
            firstname='',
            lastname='',
            mobilephone='',
            email='',
            address='',
            city='',
            zipcode=''
            ):
        self.username = username
        self.password = password
        self.firstname = firstname
        self.lastname = lastname
        self.mobilephone = mobilephone
        self.email = email
        self.address = address
        self.city = city
        self.zipcode = zipcode

class Customer(GraphObject):
    id = Property()
    name = Property()
    city = Property()

    tags = RelatedFrom("Tag", "TAGGED")
    projects = RelatedTo("Project", "REQUESTED")

    def __init__(self, name, city):
        self.name = name
        self.city = city

    def __lt__(self, other):
        return self.name < other.name
            

class Project(GraphObject):
    title = Property()
    status = Property()
    startdate = Property()
    enddate = Property()
    hours = Property()

    user = RelatedFrom("User", "ASSIGNED")
    customer = RelatedFrom("Customer", "REQUESTED")
    tags = RelatedFrom("Tag", "TAGGED")

    def __init__(self, title, status, startdate, enddate, hours):
        self.title = title
        self.status = status
        self.startdate = startdate
        self.enddate = enddate
        self.hours = hours

    def __lt__(self, other):
        return self.startdate < other.enddate

class Education(GraphObject):
    title = Property()
    education = Property()
    school = Property()
    scope = Property()
    description = Property()
    startdate = Property()
    enddate = Property()

    user = RelatedFrom("User", "ATTENDED")
    tags = RelatedFrom("Tag", "TAGGED")

    def __init__(self, 
            title,
            education, 
            school, 
            scope, 
            description, 
            startdate, 
            enddate):
        self.title = title
        self.education = education
        self.school = school
        self.scope = scope
        self.description = description
        self.startdate = startdate
        self.enddate = enddate

    def __lt__(self, other):
        return self.startdate < other.startdate

class WorkExperience(GraphObject):
    title = Property()
    employer = Property()
    description = Property()
    startdate = Property()
    enddate = Property()

    user = RelatedFrom("User", "EMPLOYED")
    tags = RelatedFrom("Tag", "TAGGED")

    def __init__(self,
            title,
            employer,
            description,
            startdate,
            enddate):
        self.title = title
        self.employer = employer
        self.description = description
        self.startdate = startdate
        self.enddate = enddate
    
    def __lt__(self, other):
        return self.startdate < other.startdate

class Certificate(GraphObject):
    title = Property()
    type = Property()
    school = Property()
    description = Property()
    date = Property()

    user = RelatedFrom("User", "CERTIFIED")
    tags = RelatedFrom("Tag", "TAGGED")

    def __init__(self,
            type,
            school,
            description,
            date):
        self.title = title
        self.type = type
        self.school = school
        self.description = description
        self.date = date
    
    def __lt__(self, other):
        return self.date < other.date

class Tag(GraphObject):
    __primarykey__ = "name"

    name = Property()

    def __init__(self, name):
        self.name = name

    def __lt__(self, other):
        return self.name < other.name
