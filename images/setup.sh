#!/usr/local/bin/python
import docker
import glob

images = docker.from_env().images
dockerfile_list = glob.glob('images/*/Dockerfile')
for dockerfile_name in dockerfile_list:
    tagname = 'web-ide/' + dockerfile_name.split('/')[1]
    try:
        images.get(tagname)
        # print(f'{tagname} already exists.')
    except:
        # image not exists.
        print(f'{tagname} not exists.')
        with open(dockerfile_name, 'rb') as f:
            images.build(path='.', tag=tagname, fileobj=f)
            print(f'{tagname} built.')

print('Docker Images Ready.')