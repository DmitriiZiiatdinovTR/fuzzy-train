import requests
import subprocess, shlex
import os

gitlab_key = '<your gitlab key>' # your gitlab key
gitlab_base_url = 'https://git.sami.int.thomsonreuters.com/api/v4/'

github_key = '<github key with SSO enabled>' # github key with SSO enabled
github_base_url = 'https://api.github.com/'
github_org_repos_url = github_base_url + 'orgs/tr/repos'
#N.B. in order to push data to github secure ssh key should be added to github with SSO enabled

def grabAllRepos(groupName):
    url = gitlab_base_url + 'groups/' + groupName + '?private_token=' + gitlab_key
    print('\n\nRetrieving from ' + url)
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

        print(f'cloning: {project_path}/{project_name} from {project_url}')
        cmd = shlex.split(f'git clone {project_url} {project_path}/{project_name}')
        subprocess.run(cmd)

    return projectDescriptions

def generateNewRepo(repoName, repoDescription):
    print(f'Creating new github repo {repoName} ({repoDescription})')    
    url = github_org_repos_url + '?access_token=' + github_key
    payload = {
        "name": repoName,
        "description": repoDescription,
        "visibility": "internal",
        "private": True
    }
    print(url)
    response = requests.post(url, json = payload, headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'DmitriiZiiatdinovTR'
        }, verify = False)
    print(response)
    print(response.text)

def generateNewRepos(groupPath, descriptions):
    curdir = os.getcwd()
    for project in os.listdir(groupPath):
        newProjectName = f"{groupPath}_{project}"
        print(f"generate new github repo: {newProjectName}")
        generateNewRepo(newProjectName, descriptions.get(project, ''))

def updateAndPush(groupPath):
    curdir = os.getcwd()
    for project in os.listdir(groupPath):
        print('Updating and pushing ' + project)
        full_project_path = curdir + os.path.sep + groupPath + os.path.sep + project
        print("update and push: " + full_project_path)
        os.chdir(full_project_path)        
        subprocess.run('git fetch origin')        
        subprocess.run('git pull origin')
        newRepoName = groupPath + '_' + project
        cmd = shlex.split(f'git remote add github org-47003210@github.com:tr/{newRepoName}.git')        
        subprocess.run(cmd)
        subprocess.run('git push github --mirror')

print('Starting getrepos process..')
descriptions = grabAllRepos('modern-ellis')
generateNewRepos('modern-ellis', descriptions)
updateAndPush('modern-ellis')
print('\nDone')