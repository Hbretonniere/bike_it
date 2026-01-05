#!/bin/bash

#conda activate bikeit_env.yml
cd ~/bike_it
python generate_stats.py
python app_graph.py
