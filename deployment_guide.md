
# Deployment Guide: Hugging Face Spaces (Recommended)

Since your application uses `sentence-transformers` and `faiss`, it requires more RAM than most standard free tiers (like Render/Vercel) provide. **Hugging Face Spaces** offers 16GB RAM for free, which is perfect for this.

## Step 1: Create a Hugging Face Space
1.  Go to [huggingface.co/spaces](https://huggingface.co/spaces) and create a new Space.
2.  **Space Name**: `shl-assessment-api` (or similar).
3.  **License**: MIT (or whatever you prefer).
4.  **SDK**: Select **Docker**.
5.  **Visibility**: Public.

## Step 2: Upload Files
You can upload files directly via the browser or use git.
The easiest way if you have the code locally is to just upload these specific files:
1.  `Dockerfile` (I just created this for you)
2.  `requirements.txt`
3.  `shl_recommender/` (The whole folder)
4.  `submission.csv` (Optional, but good to have)

## Step 3: Set Secrets (Environment Variables)
1.  Go to the **Settings** tab of your Space.
2.  Scroll to **Variables and secrets**.
3.  Click **New Secret**.
4.  Name: `GOOGLE_API_KEY`
5.  Value: (Paste your Gemini API Key from your `.env` file)

## Step 4: Access Your API
Once the space builds (it takes a few minutes), your API will be live!
- **API URL**: `https://<your-username>-<space-name>.hf.space/recommend`
- **Swagger UI**: `https://<your-username>-<space-name>.hf.space/docs`

## Alternative: Render.com (Might be tight on RAM)
1.  Push your code to GitHub.
2.  Create a new **Web Service** on Render.
3.  Connect your repo.
4.  Runtime: **Docker**.
5.  Add Environment Variable `GOOGLE_API_KEY`.
6.  *Note: Render's free tier has 512MB RAM. If your app crashes with "Out of Memory", switch to Hugging Face.*
