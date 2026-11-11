cd /home/claude/work
for p in KReIS KLoSA KHP NaSTaB KOWEPS KLIPS; do python3 run_models.py $p > log_$p.txt 2>&1; done
echo ALLDONE > alldone.txt
