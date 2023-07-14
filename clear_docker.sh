#!/bin/bash

# This script sets up a new environment for a project by performing the following steps:

# 1. Stop and remove all running Docker containers with their volumes and orphaned containers.
# 2. Prune Docker system to remove unused data.
# 3. Stop Docker service.
# 4. Remove Docker data directory and its contents.
# 5. Clean up unnecessary packages and dependencies.

# Remove all unused Docker resources
sudo docker system prune

# Stop Docker service
sudo service docker stop

# Remove Docker data directory
sudo rm /var/lib/docker -rf

# Remove Docker configuration directory for current user
sudo rm -rf ~/.docker

# Remove Docker configuration directory for root user
sudo rm -rf /root/.docker

# Start Docker service
sudo service docker start

# Clean up apt-get cache
sudo apt-get clean
sudo apt-get autoclean
sudo apt-get autoremove

# Print message indicating script has finished
echo "Docker clear is finished."