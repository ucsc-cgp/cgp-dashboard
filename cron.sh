#!/bin/bash
echo "The date is:"
date
echo "Writing environmental file"
env > /root/env.txt 
echo "Setting cron job in the foreground"
cron -f -L 15
