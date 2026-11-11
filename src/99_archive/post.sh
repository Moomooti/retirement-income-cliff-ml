cd /home/claude/work
while [ ! -f alldone.txt ]; do sleep 20; done
python3 build_common.py > log_build2.txt 2>&1
python3 run_models.py KReIS > log_KReIS.txt 2>&1
python3 run_gbm3.py > log_gbm3.txt 2>&1
python3 pooled.py > log_pooled.txt 2>&1
python3 stats_extra.py > log_stats.txt 2>&1
python3 analysis.py > log_analysis.txt 2>&1
echo POSTDONE > postdone.txt
