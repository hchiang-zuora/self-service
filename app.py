from flask import Flask, render_template, request, redirect, url_for, flash
from github import Github
from github import Auth
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

def github_pr(upn, eks, aws, orgs):
    #github token authentication
    GH_Token = ###CHANGE TOKEN
    auth = Auth.Token(GH_Token) 
    g = Github(auth=auth) 

    #getting the right repository
    repo = g.get_repo("hchiang-zuora/self-service") ###CHANGE REPOSITORY NAME
    sb = repo.get_branch(branch="master")
    new_branch = f'self-service-add-new-user-{upn}'

    #creates a new branch of name 'self-service-add-new-user-upn. 
    #will give error if a branch of the same name alrdy exists
    try: 
        repo.create_git_ref(ref='refs/heads/' + new_branch, sha=sb.commit.sha)  
    except:
        print("This user already exists")
        flash('This upn already exists', 'error')
        return 
    
    #retrieve csv file from the new branch that was created
    branch = repo.get_branch(branch=new_branch)
    file_content = repo.get_contents(path='/users.csv', ref=branch.name)

    organization = '&'.join(orgs)
    organiz = ', '.join(orgs)

    #updating the csv file
    new_file_content = file_content.decoded_content + bytes(f'{upn},{eks},{aws},{organization}\n', 'utf-8')
    repo.update_file(
        path='users.csv', 
        message="added new user", 
        content=new_file_content, 
        sha=file_content.sha,
        branch=branch.name
    )

    body = f'''Pull request to add user {upn} with the following roles:

    EKS role: {eks}
    AWS role: {aws}
    Github organization(s): {organiz}
    '''

    #creating the pull request
    flash('Form submitted successfully', 'success')
    repo.create_pull(title=f"PR to add user {upn}", body=body, head=branch.name, base="main")


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        input1 = request.form['input1']
        input2 = request.form['input2']
        input3 = request.form['input3']
        input4 = request.form.getlist('input4')
        
        github_pr(input1, input2, input3, input4)

        return redirect(url_for('home'))
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
