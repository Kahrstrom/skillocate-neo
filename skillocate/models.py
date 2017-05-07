from py2neo.ogm import GraphObject, Property, RelatedTo, RelatedFrom
from time import time

class UserModel():
    properties = [
        'id',
        'firstname',
        'lastname',
        'title',
        'name',
        'email',
        'address',
        'zipcode',
        'phone',
        'mobilephone',
        'birthdate',
        'employmentdate',
        'username',
        'office',
        'city',
        "about"
    ]

    updateProperties = [
        'firstname',
        'lastname',
        'name',
        'title',
        'email',
        'address',
        'zipcode',
        'phone',
        'mobilephone',
        'birthdate',
        'employmentdate',
        'city',
        'office',
        "about"
    ]

    slimRelations = [
        'tags'
    ]

    relations = [
        'tags',
        'projects',
        'educations',
        'certifications',
        'workexperience'
    ]

class ProjectModel():
    properties = [
        'id',
        'title',
        'hours',
        'startdate',
        'enddate'
    ]

    slimRelations = [
        'tags'
    ]

    relations = [
        'tags'
    ]

class EducationModel():
    properties = [
        'id',
        'education',
        'school',
        'startdate',
        'enddate',
        'scope'
    ]

    slimRelations = [
        'tags'
    ]

    relations = [
        'tags'
    ]

class TagModel():
    properties = [
        'name'
    ]

    slimRelations = [

    ]

    relations = [

    ]

    