import requests
import subprocess, shlex
import os

gitlab_key = '<SECRET>' # your gitlab key
gitlab_base_url = 'https://git.sami.int.thomsonreuters.com/api/v4'

github_key = '<SECRET>' # github key with SSO enabled
github_base_url = 'https://api.github.com'
github_org_repos_url = 'https://api.github.com/orgs/tr/repos'
#N.B. in order to push data to github secure ssh key should be added to github with SSO enabled

def grabAllRepos(groupName):
    url = f'gitlab_base_url/groups/{groupName}??private_token={gitlab_key}'    
    print('\n\nRetrieving projects from ' + url)
    response = requests.get(url, verify = False)
    if not response:
        print("Error requesting repositories from the gitlab")
        print(response)
        print(response.text)

    projects = response.json()["projects"]

    projectDescriptions = {}

    for project in projects:        
        project_name = project['name']
        project_path = project['namespace']['full_path']
        project_url = project['ssh_url_to_repo']

        projectDescriptions[project_name] = project['description']

        if not os.path.exists(f"{project_path}/{project_name}"):
            print(f'cloning: {project_path}/{project_name} from {project_url}')
            cmd = shlex.split(f'git clone {project_url} {project_path}/{project_name}')
            subprocess.run(cmd)
        else:
            print (project_name + " was already cloned, skipping")

    return projectDescriptions

def checkRepoExists(repoName):
    print(f'Checking if github repo {repoName} already exists')
    url = f'{github_base_url}/repos/tr/{repoName}?access_token={github_key}'    
    response = requests.get(url, verify = False)
    foundRepositoryId = response.json().get("id", -1)
    result = foundRepositoryId > 0
    if not result:
        print(response)
        print(response.text)
    return result

def generateNewRepo(repoName, repoDescription):
    print(f'Creating new github repo {repoName} ({repoDescription})')
    url = f'{github_base_url}/orgs/tr/repos?access_token={github_key}'    
    payload = {
        "name": repoName,
        "description": repoDescription,
        "visibility": "internal",
        "private": True
    }
    #print(url)
    response = requests.post(url, json = payload, verify = False)    
    print(response)
    print(response.text)

SOLT_TEAM_ID = 3458474
def grantAdminPermissionToSOLT(repoName):
    print("Granting admin permission for the team to " + repoName)
    url = f"https://api.github.com/teams/{SOLT_TEAM_ID}/repos/tr/{repoName}?access_token={github_key}"
    payload = {
        "permission": "admin"
    }
    response = requests.put(url, json=payload, verify = False)
    print(response) #<Response [204]> is good

def generateNewRepos(groupPath, descriptions):
    curdir = os.getcwd()
    for project in os.listdir(groupPath):
        newProjectName = f"{groupPath}_{project}"
        if checkRepoExists(newProjectName):
            print('Github repo already exists, skipping')
        else:
            print('repo does not exist, creting new')
            print(f"generate new github repo: {newProjectName}")
            generateNewRepo(newProjectName, descriptions.get(project, ''))
            grantAdminPermissionToSOLT(newProjectName)

def updateAndPush(groupPath):
    curdir = os.getcwd()
    for project in os.listdir(groupPath):
        newRepoName = groupPath + '_' + project
        
        #this is required only if projects were created with the wrong permission:        
        #grantAdminPermissionToSOLT(newRepoName)
        
        print('Updating and pushing ' + project)
        full_project_path = curdir + os.path.sep + groupPath + os.path.sep + project
                
        os.chdir(full_project_path)        
        print('git fetch')
        subprocess.run('git fetch origin')
        print('git pull')
        subprocess.run('git pull origin')
        
        print('adding remote branch')
        cmd = shlex.split(f'git remote add github org-47003210@github.com:tr/{newRepoName}.git')
        subprocess.run(cmd)
        
        print('git push github')
        subprocess.run('git push github --mirror')

print('Starting getrepos process..')
descriptions = grabAllRepos('modern-ellis')
generateNewRepos('modern-ellis', descriptions)
updateAndPush('modern-ellis')
print('\nDone')
