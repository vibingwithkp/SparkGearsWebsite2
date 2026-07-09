# Spark Gears Initiative Website

This is a self-contained static website for rapid GitHub Pages deployment.

## Files

- `index.html` contains the full HTML, CSS, and vanilla JavaScript experience.
- `assets/` contains local brand, team, and outreach images.
- `SparkGearsWebsite-package.zip` is the downloadable deployment package.

## Preview Locally

Open `index.html` directly in a browser, or run a small local server from this folder:

```sh
python3 -m http.server 4173
```

Then visit:

```text
http://localhost:4173
```

## Push To GitHub

1. Create a new GitHub repository, or open the repository you want to use.
2. Put `index.html`, `README.md`, and the full `assets/` folder at the repository root.
3. From this folder, run:

```sh
git init
git add index.html README.md assets
git commit -m "Launch redesigned Spark Gears website"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git push -u origin main
```

4. In GitHub, open **Settings > Pages**.
5. Set **Build and deployment** to **Deploy from a branch**.
6. Choose `main` and `/root`, then save.

GitHub Pages will publish the site after the first build finishes.

## Notes

The member roster and images were refreshed from the current team source. The community programs section includes hackathons and free outreach events including Code Crush, Code Crush Hackathon 2, library STEM stations, kickoff events, bootcamps, camps, and robotics courses.
