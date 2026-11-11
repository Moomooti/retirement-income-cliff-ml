import xl, openpyxl, pandas as pd, sys
f=sys.argv[1]
wb=openpyxl.load_workbook(f,read_only=True); ws=wb.worksheets[0]
it=ws.iter_rows(values_only=True); h=next(it)
df=pd.DataFrame(list(it),columns=h)
df.to_pickle('/home/claude/work/klosa_'+f.split('/')[-1].replace('.xlsx','.pkl'))
print(f,df.shape)
