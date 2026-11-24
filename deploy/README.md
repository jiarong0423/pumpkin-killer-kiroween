# Static host image

From the repository root, build the image:

```sh
docker build -f deploy/Dockerfile -t pumpkin-killer .
```

Run it on port 8080:

```sh
docker run --rm -p 8080:80 pumpkin-killer
```

Open `http://localhost:8080/`. The image copies only `index.html`, `css/`, `js/`,
`assets/`, and `shared/` into the nginx web root.
