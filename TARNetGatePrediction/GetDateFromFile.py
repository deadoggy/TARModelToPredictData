#coding: utf-8
'''
   从指定的文件中读取过去指定天数指定时段的网关流量
   返回类型：
     [
       [4.6, 5.0, ... ]    --19:30
       [5.1, 5.4, ... ]    --20:00
       ...
       ...
     ]
'''

import openpyxl as xl



def getNetGateData(FileName, SheetName,Time):
    '''

    :param FileName:    文件名
    :param SheetName:   页名
    :param TimeFrom:    预留：开始时间
    :param TimeTo:      预留：结束时间
    :param DateFrom:    预留：开始日期
    :param DateTo:      预留：结束日期
    :return:
    '''
    Ret = []
    WorkBook = xl.load_workbook(FileName)
    WorkSheet = WorkBook.get_sheet_by_name(WorkBook.get_sheet_names()[6])

    for index2 in range(6,81):
        Ret.append(WorkSheet.cell(row= index2, column = Time).value)


    return Ret

