# Intro
This Docker container allows a user to run PixPlot to create outputs and then visualize them. It creates an API end point to send commands to `pixplot` as well as to browse your application folder where output PixPlots have been created and view them.

# Install w/ Docker

1. Install [Docker](https://docs.docker.com/get-docker/)

2. Pull the latest docker image from [Docker Hub](https://hub.docker.com/repository/docker/digitalmethodsinitiative/dmi_pix_plot)
 - No AVX version: `docker pull digitalmethodsinitiative/dmi_pix_plot:no_AVX`  (for older hardware that Tensorflow doesn't like)

3. Start container for first time `sudo docker run --publish 127.0.0.1:4000:4000 --name pix_plot -d digitalmethodsinitiative/dmi_pix_plot:no_AVX`             `
 - `--name pix_plot` will allow you to start the container again later with `docker start pix_plot`
 - `--publish 127.0.0.1:4000:4000` tells Docker what host port connects to the container port <host port>:<container port> 
   - You can set the host port as you wish
   - `127.0.0.1:4000:4000` means that only localhost can access your container
   - `4000:4000` will expose your container to outside connections (via your_ip:4000)
 - `-d` starts the container in the background

4. You are now running! View pixplot at http://localhost:4000 in your browser

5. Afterwards you can stop and start your container as you wish
  - `docker stop pix_plot` stops the container
  - `docker start pix_plot` starts the container
    - `docker start -a pix_plot` will start the container and allow you to connect interactively (to view logs, change config.yml, etc.)
  - `docker exec -it pix_plot /bin/bash` will allow you connect to a running container via command prompt to run commands as you wish

# Usage of PixPlot container

### Uploading and viewing images
- A simple web interface will start with the container by default on localhost
    - http://localhost:4000/upload/ will allow you to upload images
    - http://localhost:4000/uploads/ will allow you to browse uploaded images
      - Uploaded images will be located at `/app/data/uploads/user_defined_folder_name/`
    - http://localhost:4000/create/ will allow you to use one of the folders to create a PixPlot
    - http://localhost:4000/plots/ will allow you to navigate to a created PixPlot

- You can also use docker to copy any image files with  `docker cp path/to/name_of_folder pix_plot:/app/name_of_folder`
  - Run this from host machine, not inside docker container

### Using API to create PixPlots

- Post via curl or python requests commands to pixplot
  - pixplot commands found at [PixPlot's github](https://github.com/YaleDHLab/pix-plot)
  - API requests can be sent like so:
```
# This is equivalent to "python pixplot/pixplot.py --images "path/to/images/*.jpg" --metadata "path/to/metadata.csv"
import requests
data = {"args" : ['--images', "/app/data/uploads/user_defined_folder_name/*.jpg", '--metadata', "/app/data/uploads/user_defined_folder_name/metadata.csv"]}
resp = requests.post("http://localhost:4000/api/pixplot", json=data)
```
  - You can check the status of your command like so:
```
result = requests.get(resp.json()['result_url'])
print(result.json())
```
- It is also possible to run commands directly while the docker container is running via `docker exec -it pix_plot "/bin/bash"`

- Navigate your browser to http://localhost:4000/plots/ to view your output PixPlots
  - Navigate to output directory (default output directory name is `output` and can be changed with the arg `--out_dir /app/data/plots/whatever_you_want`)
  - Click on index.html


# Advanced  Usage

## Build your own Docker image (say if you are developing)
1. Install [Docker](https://docs.docker.com/get-docker/)

2. Clone [DMI PixPlot Repo](https://github.com/digitalmethodsinitiative/dmi_pix_plot)

3. In repo directory, run ` docker build -t pix_plot .`

4. Start and connect to container `docker container run --publish 4000:4000 --name pix_plot -it pix_plot`
 - `--name pix_plot` will allow you to start the container again later with `docker start pix_plot`
 - `--publish 4000:4000` allows container to publish outside of container (i.e., your localhost)
 - Ctl+c will close and stop the container

5. Afterwards you can start the docker container in the background with `docker start pix_plot`. You will need to use `docker stop pix_plot` to stop it from running.
  - `docker start -a pix_plot` will allow you to connect interactively and view output similar to run, however you will need to run `docker stop pix_plot` to end it as opposed to Ctl+c
  - `docker exec -it pix_plot /bin/bash` will allow you connect to the container via command prompt to run commands as you wish
