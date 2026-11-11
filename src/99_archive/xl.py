import openpyxl
from openpyxl.worksheet.properties import WorksheetProperties
_o=WorksheetProperties.__init__
def _n(self,*a,**k):
    k.pop('synchVertical',None); k.pop('synchHorizontal',None); return _o(self,*a,**k)
WorksheetProperties.__init__=_n
