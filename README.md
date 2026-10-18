# Spark Gears Initiative Website

This is a self-contained static website for rapid GitHub Pages deployment.

## Files

- `index.html`, `for-teams.html`, `impact.html`, `about.html`, and `donate.html` are the five pages. `programs.html` and `get-involved.html` only redirect to `impact.html` and `for-teams.html` so old links keep working.
- `styles.css` holds all shared styles; `site.js` holds the interactions (breadboard hero, menu, impact rail, galleries, lightbox, filters, tabs).
- `assets/` contains local brand, team, and outreach images. `assets/web/` has resized copies of the big photos that the pages actually load; resize new photos to ~1400px wide before adding them.
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

<<<<<<< HEAD
The site focuses on helping FTC teams (especially rookie teams) run outreach events, and on the partnerships Spark Gears has built in the U.S. and India. Placeholders the owner still needs to fill in are marked `[TODO: ...]` with a matching `<!-- TODO -->` comment.
=======
The site focuses on helping FTC teams (especially rookie teams) run outreach events, and on the partnerships Spark Gears has built in the U.S., India, and Pakistan. Placeholders the owner still needs to fill in are marked `[TODO: ...]` with a matching `<!-- TODO -->` comment.
>>>>>>> 3b6b7ae1383f3d6551069a74070a55c515411292
