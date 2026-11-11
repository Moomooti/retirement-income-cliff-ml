cd /home/claude/work
while [ ! -f alldone.txt ]; do sleep 20; done
python3 build_common.py > log_build2.txt 2>&1 || exit 1
python3 run_models.py KReIS > log_KReIS.txt 2>&1 || exit 2
python3 run_gbm3.py > log_gbm3.txt 2>&1 || exit 3
echo CHAIN_A_DONE
