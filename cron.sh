#!/bin/bash
echo "The date is:"
date
echo "Writing environmental file"
env > /root/env.txt 
echo "Initializing database"
python -c "import models; models.initialize_table()" && echo "Burndown table initialized!"
echo "Setting cron job in the foreground"
cron -f -L 15
