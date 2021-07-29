# Intro
This Docker container allows a user to run PixPlot to create outputs and then visualize them. It creates an API end point to send commands to `pixplot` as well as to browse your application folder where output PixPlots have been created and view them.

# How to use w/ Docker

1. Install [Docker](https://docs.docker.com/get-docker/)

2. Clone [PixPlot Repo](https://github.com/YaleDHLab/pix-plot)

3. In repo directory, run ` docker build -t pix_plot .`

4. Start and connect to container `docker container run --publish 4000:4000 --name pix_plot -it pix_plot`
 - `--name pixplot` will allow you to start the container again later with `docker start pix_plot`
 - `--publish 4000:4000` allows container to publish outside of container (i.e., your localhost)

5. Copy any image files with  `docker cp path/to/name_of_folder docker_container_id:/usr/src/app/name_of_folder`
  - Run this from host machine, not inside docker container
  - Run `docker container ls` to find docker_container_id
  - TODO: look at running on files outside container

6. Post via curl or python requests commands to pixplot
  - pixplot commands found at [PixPlot's github](https://github.com/YaleDHLab/pix-plot)
  - API requests can be sent like so:
```
# This is equivalent to "python pixplot/pixplot.py --images "path/to/images/*.jpg" --metadata "path/to/metadata.csv"
import requests
data = {"args" : ['--images', "/usr/src/app/image_folder/*.jpg", '--metadata', "/usr/src/app/image_folder/metadata.csv"]}
resp = requests.post("http://localhost:4000/api/pixplot", json=data)
```
  - It is also possible to run commands directly while the docker container is running via `docker exec -it docker_container_id "/bin/bash"`

7. Navigate your browser to http://localhost:4000 to view your output PixPlot
  - Navigate to output directory (default output directory name is `output` and can be changed with the arg `--out_dir whatever_you_want`)
  - Click on index.html
