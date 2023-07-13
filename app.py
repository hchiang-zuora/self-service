from flask import Flask, render_template, request, redirect, url_for, flash
from github import Github
from github import Auth
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

users_list = []

@app.route('/github_pr', methods=['GET', 'POST'])
def github_pr():
    #verify that at least one new user has been added
    if len(users_list) == 0:
        flash('Enter at least one new user', 'error')
        return redirect(url_for('home'))

    #creating the github body message + new branch name
    body = "Adding the following upn(s):\n\n"
    new_branch = "add-user"
    for user in users_list:
        upn, eks, aws, orgs = user.split(',')
        body += f'User: {upn}\nEKS role: {eks}\nAWS role: {aws}\nGH Org(s): {orgs}\n\n'
        new_branch += f'-{upn}'

    #github token authentication
    GH_Token = ###CHANGE TOKEN
    auth = Auth.Token(GH_Token) 
    g = Github(auth=auth) 

    #getting the right repository
    repo = g.get_repo("hchiang-zuora/self-service") ###CHANGE REPOSITORY NAME
    sb = repo.get_branch(branch="master")

    #creates a new branch of name 'self-service-add-new-user-upn. 
    #will give error if a branch of the same name alrdy exists
    try: 
        repo.create_git_ref(ref='refs/heads/' + new_branch, sha=sb.commit.sha)  
    except:
        flash('This upn already exists', 'error')
        return redirect(url_for('home'))
    
    #retrieve csv file from the new branch that was created
    branch = repo.get_branch(branch=new_branch)
    file_content = repo.get_contents(path='/users.csv', ref=branch.name)

    #updating the csv file
    new_file_content = file_content.decoded_content
    for user in users_list:
        new_file_content += bytes(user + '\n', 'utf-8')

    repo.update_file(
        path='users.csv', 
        message="added new user", 
        content=new_file_content, 
        sha=file_content.sha,
        branch=branch.name
    )

    #creating the pull request
    flash('Form submitted successfully', 'success')
    repo.create_pull(title=f"PR to add new dev(s)", body=body, head=branch.name, base="main")

    return redirect(url_for('delete_all_users'))

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        input1 = request.form['input1']
        input2 = request.form['input2']
        input3 = request.form['input3']
        input4 = request.form.getlist('input4')

        #maximum of 5 users at a time
        if len(users_list) >= 5:
            flash('Max 5 users', 'error')
            return redirect(url_for('home'))
        
        users_list.append(input1 + ',' + input2 + ',' + input3 + ',' + '&'.join(input4))

        return redirect(url_for('home'))
    
    return render_template('index.html', users_list=users_list)

#responds to the delete button (X) and deletes a user
@app.route('/delete_user', methods=['GET'])
def delete_user():
    user = request.args.get('user')
    if user in users_list:
        users_list.remove(user)
    
    return redirect(url_for('home'))

#after hitting "submit" (making a pull request), clear all users from the list
@app.route('/delete_all_users', methods=['GET'])
def delete_all_users():
    users_list.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
