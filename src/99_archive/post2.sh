cd /home/claude/work
while [ ! -f postdone.txt ]; do sleep 20; done
python3 extra.py > log_extra.txt 2>&1
echo DONE2 > post2done.txt
