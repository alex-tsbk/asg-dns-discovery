# ASG DNS Discovery
Terraform module providing rich functionality and flexible configuration for synchronizing EC2 instances IPs
launched through AWS Auto Scaling groups with DNS records.

## Functionality
* Multiple ASGs public/private IPs to multiple DNS records synchronization
* Distributed locking to prevent DNS record corruption
* On-demand HTTP/TCP health checking
    * Before adding EC2 instance to DNS record will run provided health check. Low-level tuning settings available.
* On-demand EC2 readiness checking
    * Will perform readiness check by matching your `tag_key:tag_value` pair to one that is on EC2 instance. Will also wait for specified amount of time for EC2 to reach 'ready' state. This is useful when you're deploying to EC2 upon launch. It's your application code responsibility to update tag on itself to desired value.
* On-demand reconciliation daemon
    * Will watch for  EC2 state changes that are not propagated through lifecycle hooks (manual EC2 termination, putting EC2 into 'Standby' state, etc)


## Who is this module for?
If answer to any or all of the below is "Yes", then this module might help you:

* Have a few ASGs running applications that talk to each other?
* Applications themselves are somewhat stable and don't crash often?
* Maybe they are also dealing with hight volume of traffic (producing a lot of egress internet traffic)?
* You don't want to set up ELBs just for the purpose of service discovery, and you don't want to setup tools like Consul - as it's just too much overhead?


## Technical Details
Package is composed of applications:
1. Firs application augments your ASGs with [lifecycle hooks](https://docs.aws.amazon.com/autoscaling/ec2/userguide/lifecycle-hooks.html) and listens for ASG Lifecycle events. As EC2 instances transition to/from `InService` states changes are handled and DNS records updated according to configuration specified.
1. Second application is 'reconciliation' service. It uses the same codebase, but runs at specified cadence and reconciles state of your ASGs with DNS records. If any drift is found - updates DNS records accordingly.

The following DNS providers supported:
* Route53

The following DNS providers are in development:
* Cloudflare

## Integration Examples

Below is a an integration example with HAProxy:
TBD

## What this module is NOT
This module is not a service discovery, neither it is a substitute for one. Service discover is way more advanced concern with way lower latency and more feature-rich functionality. If you're looking for true service discovery, it's suggested you look into AWS-native [App Mesh](https://aws.amazon.com/app-mesh/) or [Hashicorp Consul](https://www.consul.io/).

## Development Setup

To get started with local development you will need to 2 applications:
* [Docker](https://www.docker.com/get-started/)
* [Visual Studio Code](https://code.visualstudio.com/)

This repository utilizes [devcontainer](https://code.visualstudio.com/docs/devcontainers/containers) for bootstrapping local development environments.
To get started - in command palette (F1) type in `Dev Containers: Open Folder in Container`.

Once

### Bootstrapping local environment
1. Have Docker installed and running
1. Open project in VS Code

`devcontainer.json` is pre-configured to bootstrap local environment and get it ready for development.

Once everything is done, open new bash terminal, and type in `make format`. If you see something similar to `All done! ✨ 🍰 ✨` in the output - then everything has been bootstrapped successfully.

### Consideration about using 3rd party packages

Please note, that at the moment of writing this documentation, only the following PIP packages are available at runtime:

```
Package         Version
--------------- -------
awslambdaric    2.0.10
boto3           1.34.42
botocore        1.34.42
jmespath        1.0.1
pip             23.2.1
python-dateutil 2.8.2
s3transfer      0.10.0
simplejson      3.17.2
six             1.16.0
urllib3         1.26.18
```

This code doesn't use anything except what's available out of the box for Python 3.12 AWS Lambda runtime.

You can always re-confirm what are the latest available packages by exploring `public.ecr.aws/lambda/python:3.12` docker image:

```sh
# Start docker container locally
docker run -it --entrypoint /bin/bash public.ecr.aws/lambda/python:3.12
# Once inside container, run:
python -m pip list
```

You can read more information about runtime in [Python 3.12 runtime now available in AWS Lambda](https://aws.amazon.com/blogs/compute/python-3-12-runtime-now-available-in-aws-lambda/).

### Building on top
My personal preference when developing this package was to keep external dependencies to a bare minimum.

However, if you're thinking to build on top of this module, I suggest you look into using base layer from [Powertools for AWS Lambda](https://docs.powertools.aws.dev/lambda/python/latest/). This already includes ton of useful packages.

#### Known Issues
* There looks like some kind of glitch when using [indent-rainbow](https://marketplace.visualstudio.com/items?itemName=oderwat.indent-rainbow) extension. If it doesn't show up on first load - disabling extension, reloading window and re-enabling extension again should fix the missing indentation highlight.
