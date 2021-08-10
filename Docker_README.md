# Intro
This Docker container allows a user to run PixPlot to create outputs and then visualize them. It creates an API end point to send commands to `pixplot` as well as to browse your application folder where output PixPlots have been created and view them.

# Install w/ Docker

1. Install [Docker](https://docs.docker.com/get-docker/)

2. Clone [PixPlot Repo](https://github.com/YaleDHLab/pix-plot)

3. In repo directory, run ` docker build -t pix_plot .`

4. Start and connect to container `docker container run --publish 4000:4000 --name pix_plot -it pix_plot`
 - `--name pix_plot` will allow you to start the container again later with `docker start pix_plot`
 - `--publish 4000:4000` allows container to publish outside of container (i.e., your localhost)
 - Ctl+c will close and stop the container

5. Afterwards you can start the docker container in the background with `docker start pix_plot`. You will need to use `docker stop pix_plot` to stop it from running.
  - `docker start -a pix_plot` will allow you to connect interactively and view output similar to run, however you will need to run `docker stop pix_plot` to end it as opposed to Ctl+c
  - `docker exec -it pix_plot /bin/bash` will allow you connect to the container via command prompt to run commands as you wish

# Usage of PixPlot container

### Uploading and viewing images
- A simple web interface will start with the container by default on localhost
    - http://localhost:4000/upload/ will allow you to upload images
    - http://localhost:4000/uploads/ will allow you to browse uploaded images
      - Uploaded images will be located at `/usr/src/app/data/uploads/user_defined_folder_name/`
    - http://localhost:4000/plots/ will allow you to navigate to a created PixPlot

- You can also use docker to copy any image files with  `docker cp path/to/name_of_folder pix_plot:/usr/src/app/name_of_folder`
  - Run this from host machine, not inside docker container

### Using API to create PixPlots

- Post via curl or python requests commands to pixplot
  - pixplot commands found at [PixPlot's github](https://github.com/YaleDHLab/pix-plot)
  - API requests can be sent like so:
```
# This is equivalent to "python pixplot/pixplot.py --images "path/to/images/*.jpg" --metadata "path/to/metadata.csv"
import requests
data = {"args" : ['--images', "/usr/src/app/data/uploads/user_defined_folder_name/*.jpg", '--metadata', "/usr/src/app/data/uploads/user_defined_folder_name/metadata.csv"]}
resp = requests.post("http://localhost:4000/api/pixplot", json=data)
```
  - You can check the status of your command like so:
```
result = requests.get(resp.json()['result_url'])
print(result.json())
```
- It is also possible to run commands directly while the docker container is running via `docker exec -it docker_container_id "/bin/bash"`

- Navigate your browser to http://localhost:4000/plots/ to view your output PixPlots
  - Navigate to output directory (default output directory name is `output` and can be changed with the arg `--out_dir /usr/src/app/data/plots/whatever_you_want`)
  - Click on index.html
