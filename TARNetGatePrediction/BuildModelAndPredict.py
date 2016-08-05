#coding: utf-8
'''
   预测半小时的数据
'''

import numpy as np
from GetDateFromFile import getNetGateData

def divideData(DataArr, r, d, n0):
    '''
       给定门限值日， 延迟误差d 以及 n0的情况下，把数据分为第一类和第二类,用序号表示数据
       返回类型：
              [
                [x(1)1，x(1)2, ... ]
                [x(2)1, x(2)2, ... ]
              ]
    '''
    RetIndex = []
    FirstClass = []
    SecondClass = []

    for index in range(1, len(DataArr) - n0 + 1):
        if DataArr[n0 + index - d - 1] <= r:
            FirstClass.append(n0 + index - 1)
        else:
            SecondClass.append(n0 + index  - 1)

    RetIndex.append(FirstClass)
    RetIndex.append(SecondClass)

    return RetIndex

def calcThetaVectorAndSigma(DataArr, ClassDataIndex, P):
    '''

    :param DataArr:         原始数据数组
    :param ClassDataIndex:  当前计算的类的数据下标
    :param P:               阶数
    :return:                [
                               [...] -- 回归系数向量
                               Sigma -- 白噪声方差
                            ]
    '''

    #构造目标矩阵
    TargetMat = []
    for index in ClassDataIndex:
        TargetMat.append(DataArr[index])

    #构造A矩阵
    FeatureMat = []

    for index in ClassDataIndex:
        tempmat = [1.0]
        for index2 in range(1, int(P + 1)):
            tempmat.append( DataArr[ index - index2 ] )
        FeatureMat.append(tempmat)

    AMat = np.mat(FeatureMat)
    XMat = np.mat(TargetMat).T

    ATAMat = AMat.T * AMat
    if 0.0 == np.linalg.det(ATAMat):
        return None

    RetArr = ATAMat.I * ( AMat.T * XMat )[:,0]

    RetSigma = ( XMat - AMat * RetArr ).T * ( XMat - AMat * RetArr ) / len(ClassDataIndex)

    return [ RetArr, RetSigma ]

def calcAIC(DataArr, FirstClassDataIndex, SecondClassDataIndex , L):
    '''
    :param DataArr:                  原始数据数组
    :param FirstClassDataIndex:      第一类数据下标
    :param SecondClassDataIndex:     第二类数据下标
    :param r:                        指定门限值
    :param d:                        指定延迟参数
    :param L:                        最高阶
    :return:                         [AIC(r,d), p1, p2]
    '''
    FirstMinAIC = np.inf
    FirstP = -1
    SecondMinAIC = np.inf
    SecondP = -1

    for p in range(1,L+1):
        #计算第一个P的最小值
        tempFirstRes = calcThetaVectorAndSigma(DataArr,FirstClassDataIndex,p)
        if None == tempFirstRes:
            continue
        tempFirstAIC = len(FirstClassDataIndex) * np.log(tempFirstRes[1]) + 2 * (p + 2)
        #计算第二个P的最小值
        tempSecondRes = calcThetaVectorAndSigma(DataArr, SecondClassDataIndex, p)
        if None == tempSecondRes:
            continue
        tempSecondAIC = len(SecondClassDataIndex) * np.log(tempSecondRes[1]) + 2 * (p + 2)
        if FirstMinAIC > tempFirstAIC:
            FirstMinAIC = tempFirstAIC
            FirstP = p
        if SecondMinAIC > tempSecondAIC:
            SecondMinAIC = tempSecondAIC
            SecondP = p

    #如果找不到合适的P
    if -1 == FirstP or -1 == SecondP:
        return None

    AICRes = FirstMinAIC + SecondMinAIC

    return [AICRes, FirstP, SecondP]

def confirmRAndDAndP(D, L, DataArr):
    '''

    :param D:         最大的延迟参数
    :param L:         最大的阶数
    :param DataArr:   数据数组
    :return:          [r,d,p1,p2, [...], [...]]
    '''

    #获取r的候选值
    TempDataArr = DataArr[:]
    list.sort(TempDataArr)
    RList = []
    for index in range(5):
        RList.append( TempDataArr[int((0.3 + index * 0.1) * len(TempDataArr)) - 1] )


    #确定最佳的r, d
    Bestd = -1
    Bestr = -1
    BestAICRes = None
    BestDataClass = None
    MinAIC = np.inf
    MinNAIC = np.inf
    for r in RList: #对于每个R
        for d in range(1,D+1): #对于每个d
            n0 = d if d >= L else L
            DataClass = divideData(DataArr,r, d, n0) #根据门限值划分原始数据
            AICRes = calcAIC(DataArr,DataClass[0], DataClass[1], L)
            if None == AICRes:
                continue
            if AICRes[0] < MinAIC and AICRes[0] / (len(DataClass[0]) + len(DataClass[1])) < MinNAIC: #找AIC(t,d)的最小值
                BestDataClass = DataClass
                BestAICRes = AICRes
                Bestr = r
                MinAIC = AICRes[0]
                Bestd = d
                MinNAIC = AICRes[0] / (len(DataClass[0]) + len(DataClass[1]))


    if None == BestAICRes:
        return None

    #根据p1/p2找到回归系数矩阵
    Vector1 = calcThetaVectorAndSigma(DataArr, BestDataClass[0], BestAICRes[1])
    Vector2 = calcThetaVectorAndSigma(DataArr, BestDataClass[1], BestAICRes[2])


    return [Bestr, Bestd, BestAICRes[1], BestAICRes[2], Vector1[0], Vector2[0]]

def calcPredValue(DataArr, p, Vector):
    '''
    根据d,p和之前算出的回归系数矩阵预测值
    :param DataArr:   原始数据
    :param p:         阶数
    :param Vector:    回归系数向量
    :return:          预测值
    '''
    FeatureMat = [1.0]
    Size = len(DataArr)
    for index in range(Size - p, Size):
        FeatureMat.append(DataArr[index])
    xMat = np.mat(FeatureMat)
    yMat = np.mat(Vector)

    return (xMat * yMat)[0,0]

def predict( DataMat, Days, D, L):
    '''

    :param DataMat: 数据
    :param Days:    要预测的天数
    :param D:       最高延迟参数
    :param L:       最高阶
    :return:
    '''

    N = len(DataMat)

    PredResult = []
    for index in range(1, Days+1):
        Coeff = confirmRAndDAndP(D, L, DataMat)
        if None == Coeff:
            return None
        n0 = Coeff[1] if Coeff[1] > L else L
        if DataMat[index + N - Coeff[1] - 1] > Coeff[0]:#待预测值属于第一类数据
            P = Coeff[2]
            Vector = Coeff[4]

        else:    #待预测值属于第二类数据
            P = Coeff[3]
            Vector = Coeff[5]

        PredValue = calcPredValue(DataMat,  P, Vector)
        PredResult.append(PredValue)
        DataMat.append(PredValue)

    return PredResult