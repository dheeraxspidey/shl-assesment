
#!/bin/bash

# 1. Add Hugging Face Remote
# Check if remote exists
if git remote | grep -q "hf"; then
    echo "Remote 'hf' already exists."
else
    echo "Adding remote 'hf'..."
    git remote add hf https://huggingface.co/spaces/dheeraxspide/shl-rec
fi

# 2. Add Files
echo "Adding files..."
git add .gitignore
git add Dockerfile
git add requirements.txt
git add README.md
git add submission.csv
git add generate_submission.py
git add shl_recommender/
git add experiments/

# 3. Commit
echo "Committing..."
git commit -m "Deploy to Hugging Face Spaces"

# 4. Push
echo "Pushing to Hugging Face..."
echo "You may be asked for your Hugging Face username and token (password)."
git push hf main --force

echo "Done!"
