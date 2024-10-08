# datavis-group24

A project for the course "Data Visualization" at Aarhus University.

Group 24
- Eric Huber
- Md Sadik Hasan Khan
- Benno Kossatz
- Andreas William Randrup Madsen

## Setup
1. Create a new virtual environment
2. Install other requirements using `pip install -r requirements.txt`
3. Add data files to `/data/...`

## Run


## Git Workflow
Trunk based development: New features are developed on short-lived feature branches that are merged into the main branch frequently. Feature branches should not exist longer than one week before being merged into the main branch.

Example of implementing a new feature:
1. Create new branch with descriptive name (e.g. 'implement-mse-lossfunction')
2. Implement the feature, commit frequently with descriptive commit messages.
3. When implementation is finished:
    - Merge main branch into feature branch to bring it up to the current state of development.
    - Create pull request, assign other team members.
    - Wait for pull request to be confirmed.
    - Merge feature branch into main branch.
    - Delete feature branch.