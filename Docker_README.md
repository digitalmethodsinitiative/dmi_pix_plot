# How to use w/ Docker

1. Install (Docker)[https://docs.docker.com/get-docker/]

2. Clone (PixPlot Repo)[https://github.com/YaleDHLab/pix-plot]

3. In repo directory, run ` docker build -t pix_plot .`

4. Start and connect to container `docker container run --publish 5000:5000 -it pix_plot`
 - `--publish 5000:5000` allows container to publish outside of container (i.e., your localhost)

5. Copy any image files and  `docker cp path/to/name_of_folder docker_container_id:/usr/src/app/name_of_folder`
  - Run this from host machine, not inside docker container
  - Run `docker container ls` to find docker_container_id
  - TODO: look at running on files outside container

6. Run pixplot on files `python pixplot/pixplot.py --images "path/to/images/*.jpg" --metadata "path/to/metadata.csv"`

7. Run `python -m http.server 5000`

8. Navigate your browser to http://localhost:5000
