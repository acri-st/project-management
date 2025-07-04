TAG_PROJECTS = "Project routes"
TAG_APPLICATIONS = "Application routes"
TAG_PROFILES = "Profile routes"
TAG_OPERATINGSYSTEMS = "Operating System routes"
TAG_FLAVORS = "Flavor routes"
TAG_REPOSITORIES = "Repository routes"

tags_metadata = [
    {
        "name": TAG_PROJECTS,
        "description": "Routes to get and modify the projects",
    },
    {
        "name": TAG_APPLICATIONS,
        "description": "Routes to get and modify the applications to be installed on the user's environment",
    },
    {
        "name": TAG_PROFILES,
        "description": "Routes to get and modify the local user profiles for the sandbox",
    },
    {
        "name": TAG_OPERATINGSYSTEMS,
        "description": "Routes to get and modify the operating systems to be run on the OVH VMs",
    },
    {
        "name": TAG_FLAVORS,
        "description": "Routes to get and modify the flavors to be allocated on the OVH VMs",
    },
    {
        "name": TAG_REPOSITORIES,
        "description": "Routes to get and modify the gitlab repositories linked to the project",
    },
]

api_description_text = """
This is the Project Management API, it is made to serve as an intermediary between the OVH public cloud sandbox and the collaborative services. 
"""
