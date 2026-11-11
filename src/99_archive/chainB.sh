cd /home/claude/work
python3 pooled.py > log_pooled.txt 2>&1 || exit 1
python3 stats_extra.py > log_stats.txt 2>&1 || exit 2
python3 analysis.py > log_analysis.txt 2>&1 || exit 3
python3 extra.py > log_extra.txt 2>&1 || exit 4
echo CHAIN_B_DONE
