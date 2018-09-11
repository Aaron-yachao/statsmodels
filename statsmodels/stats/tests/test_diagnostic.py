# -*- coding: utf-8 -*-
"""Tests for Regression Diagnostics and Specification Tests

Created on Thu Feb 09 13:19:47 2012

Author: Josef Perktold
License: BSD-3

currently all tests are against R

"""
import os

import numpy as np
import pandas as pd

from numpy.testing import (assert_, assert_almost_equal, assert_equal,
                           assert_allclose, assert_array_equal)
import pytest

from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant
from statsmodels.datasets import macrodata

import statsmodels.stats.sandwich_covariance as sw
import statsmodels.stats.diagnostic as smsdia
import json

import statsmodels.stats.outliers_influence as oi

cur_dir = os.path.abspath(os.path.dirname(__file__))


def compare_t_est(sp, sp_dict, decimal=(14, 14)):
    assert_allclose(sp[0], sp_dict['statistic'], atol=10 ** -decimal[0],
                    rtol=10 ** -decimal[0])
    assert_allclose(sp[1], sp_dict['pvalue'], atol=10 ** -decimal[1],
                    rtol=10 ** -decimal[0])


def notyet_atst():
    d = macrodata.load(as_pandas=False).data

    realinv = d['realinv']
    realgdp = d['realgdp']
    realint = d['realint']
    endog = realinv
    exog = add_constant(np.c_[realgdp, realint])
    res_ols1 = OLS(endog, exog).fit()

    #growth rates
    gs_l_realinv = 400 * np.diff(np.log(d['realinv']))
    gs_l_realgdp = 400 * np.diff(np.log(d['realgdp']))
    lint = d['realint'][:-1]
    tbilrate = d['tbilrate'][:-1]

    endogg = gs_l_realinv
    exogg = add_constant(np.c_[gs_l_realgdp, lint])
    exogg2 = add_constant(np.c_[gs_l_realgdp, tbilrate])

    res_ols = OLS(endogg, exogg).fit()
    res_ols2 = OLS(endogg, exogg2).fit()

    #the following were done accidentally with res_ols1 in R,
    #with original Greene data

    params = np.array([-272.3986041341653, 0.1779455206941112,
                       0.2149432424658157])
    cov_hac_4 = np.array([1321.569466333051, -0.2318836566017612,
                37.01280466875694, -0.2318836566017614, 4.602339488102263e-05,
                -0.0104687835998635, 37.012804668757, -0.0104687835998635,
                21.16037144168061]).reshape(3,3, order='F')
    cov_hac_10 = np.array([2027.356101193361, -0.3507514463299015,
        54.81079621448568, -0.350751446329901, 6.953380432635583e-05,
        -0.01268990195095196, 54.81079621448564, -0.01268990195095195,
        22.92512402151113]).reshape(3,3, order='F')

    #goldfeld-quandt
    het_gq_greater = dict(statistic=13.20512768685082, df1=99, df2=98,
                          pvalue=1.246141976112324e-30, distr='f')
    het_gq_less = dict(statistic=13.20512768685082, df1=99, df2=98, pvalue=1.)
    het_gq_2sided = dict(statistic=13.20512768685082, df1=99, df2=98,
                          pvalue=1.246141976112324e-30, distr='f')

    #goldfeld-quandt, fraction = 0.5
    het_gq_greater_2 = dict(statistic=87.1328934692124, df1=48, df2=47,
                          pvalue=2.154956842194898e-33, distr='f')

    gq = smsdia.het_goldfeldquandt(endog, exog, split=0.5)
    compare_t_est(gq, het_gq_greater, decimal=(13, 14))
    assert_equal(gq[-1], 'increasing')


    harvey_collier = dict(stat=2.28042114041313, df=199,
                          pvalue=0.02364236161988260, distr='t')
    #hc = harvtest(fm, order.by=ggdp , data = list())
    harvey_collier_2 = dict(stat=0.7516918462158783, df=199,
                          pvalue=0.4531244858006127, distr='t')



    ##################################



class TestDiagnosticG(object):

    @classmethod
    def setup_class(cls):
        d = macrodata.load_pandas().data
        #growth rates
        gs_l_realinv = 400 * np.diff(np.log(d['realinv'].values))
        gs_l_realgdp = 400 * np.diff(np.log(d['realgdp'].values))
        lint = d['realint'][:-1].values
        tbilrate = d['tbilrate'][:-1].values

        endogg = gs_l_realinv
        exogg = add_constant(np.c_[gs_l_realgdp, lint])
        exogg2 = add_constant(np.c_[gs_l_realgdp, tbilrate])
        exogg3 = add_constant(np.c_[gs_l_realgdp])

        res_ols = OLS(endogg, exogg).fit()
        res_ols2 = OLS(endogg, exogg2).fit()

        res_ols3 = OLS(endogg, exogg3).fit()

        cls.res = res_ols
        cls.res2 = res_ols2
        cls.res3 = res_ols3
        cls.endog = cls.res.model.endog
        cls.exog = cls.res.model.exog

    def test_basic(self):
        #mainly to check I got the right regression
        #> mkarray(fm$coefficients, "params")
        params = np.array([-9.48167277465485, 4.3742216647032,
                           -0.613996969478989])

        assert_almost_equal(self.res.params, params, decimal=12)

    def test_hac(self):
        res = self.res
        #> nw = NeweyWest(fm, lag = 4, prewhite = FALSE, verbose=TRUE)
        #> nw2 = NeweyWest(fm, lag=10, prewhite = FALSE, verbose=TRUE)

        #> mkarray(nw, "cov_hac_4")
        cov_hac_4 = np.array([1.385551290884014, -0.3133096102522685,
            -0.0597207976835705, -0.3133096102522685, 0.1081011690351306,
            0.000389440793564336, -0.0597207976835705, 0.000389440793564339,
            0.0862118527405036]).reshape(3,3, order='F')

        #> mkarray(nw2, "cov_hac_10")
        cov_hac_10 = np.array([1.257386180080192, -0.2871560199899846,
            -0.03958300024627573, -0.2871560199899845, 0.1049107028987101,
            0.0003896205316866944, -0.03958300024627578, 0.0003896205316866961,
            0.0985539340694839]).reshape(3,3, order='F')

        cov = sw.cov_hac_simple(res, nlags=4, use_correction=False)
        bse_hac = sw.se_cov(cov)
        assert_almost_equal(cov, cov_hac_4, decimal=14)
        assert_almost_equal(bse_hac, np.sqrt(np.diag(cov)), decimal=14)

        cov = sw.cov_hac_simple(res, nlags=10, use_correction=False)
        bse_hac = sw.se_cov(cov)
        assert_almost_equal(cov, cov_hac_10, decimal=14)
        assert_almost_equal(bse_hac, np.sqrt(np.diag(cov)), decimal=14)


    def test_het_goldfeldquandt(self):
        #TODO: test options missing

        #> gq = gqtest(fm, alternative='greater')
        #> mkhtest_f(gq, 'het_gq_greater', 'f')
        het_gq_greater = dict(statistic=0.5313259064778423,
                              pvalue=0.9990217851193723,
                              parameters=(98, 98), distr='f')

        #> gq = gqtest(fm, alternative='less')
        #> mkhtest_f(gq, 'het_gq_less', 'f')
        het_gq_less = dict(statistic=0.5313259064778423,
                           pvalue=0.000978214880627621,
                           parameters=(98, 98), distr='f')

        #> gq = gqtest(fm, alternative='two.sided')
        #> mkhtest_f(gq, 'het_gq_two_sided', 'f')
        het_gq_two_sided = dict(statistic=0.5313259064778423,
                                pvalue=0.001956429761255241,
                                parameters=(98, 98), distr='f')


        #> gq = gqtest(fm, fraction=0.1, alternative='two.sided')
        #> mkhtest_f(gq, 'het_gq_two_sided_01', 'f')
        het_gq_two_sided_01 = dict(statistic=0.5006976835928314,
                                   pvalue=0.001387126702579789,
                                   parameters=(88, 87), distr='f')

        #> gq = gqtest(fm, fraction=0.5, alternative='two.sided')
        #> mkhtest_f(gq, 'het_gq_two_sided_05', 'f')
        het_gq_two_sided_05 = dict(statistic=0.434815645134117,
                                   pvalue=0.004799321242905568,
                                   parameters=(48, 47), distr='f')

        endogg, exogg = self.endog, self.exog
        #tests
        gq = smsdia.het_goldfeldquandt(endogg, exogg, split=0.5)
        compare_t_est(gq, het_gq_greater, decimal=(14, 14))
        assert_equal(gq[-1], 'increasing')

        gq = smsdia.het_goldfeldquandt(endogg, exogg, split=0.5,
                                       alternative='decreasing')
        compare_t_est(gq, het_gq_less, decimal=(14, 14))
        assert_equal(gq[-1], 'decreasing')

        gq = smsdia.het_goldfeldquandt(endogg, exogg, split=0.5,
                                       alternative='two-sided')
        compare_t_est(gq, het_gq_two_sided, decimal=(14, 14))
        assert_equal(gq[-1], 'two-sided')

        #TODO: forcing the same split as R 202-90-90-1=21
        gq = smsdia.het_goldfeldquandt(endogg, exogg, split=90, drop=21,
                                       alternative='two-sided')
        compare_t_est(gq, het_gq_two_sided_01, decimal=(14, 14))
        assert_equal(gq[-1], 'two-sided')
        #TODO other options ???

    def test_het_breusch_pagan(self):
        res = self.res

        bptest = dict(statistic=0.709924388395087, pvalue=0.701199952134347,
                      parameters=(2,), distr='f')

        bp = smsdia.het_breuschpagan(res.resid, res.model.exog)
        compare_t_est(bp, bptest, decimal=(12, 12))



    def test_het_white(self):
        res = self.res

        #TODO: regressiontest, compare with Greene or Gretl or Stata
        hw = smsdia.het_white(res.resid, res.model.exog)
        hw_values = (33.503722896538441, 2.9887960597830259e-06,
                     7.7945101228430946, 1.0354575277704231e-06)
        assert_almost_equal(hw, hw_values)

    def test_het_arch(self):
        #test het_arch and indirectly het_lm against R
        #> library(FinTS)
        #> at = ArchTest(residuals(fm), lags=4)
        #> mkhtest(at, 'archtest_4', 'chi2')
        archtest_4 = dict(statistic=3.43473400836259,
                          pvalue=0.487871315392619, parameters=(4,),
                          distr='chi2')

        #> at = ArchTest(residuals(fm), lags=12)
        #> mkhtest(at, 'archtest_12', 'chi2')
        archtest_12 = dict(statistic=8.648320999014171,
                           pvalue=0.732638635007718, parameters=(12,),
                           distr='chi2')

        at4 = smsdia.het_arch(self.res.resid, maxlag=4)
        at12 = smsdia.het_arch(self.res.resid, maxlag=12)
        compare_t_est(at4[:2], archtest_4, decimal=(12, 13))
        compare_t_est(at12[:2], archtest_12, decimal=(12, 13))

    def test_het_arch2(self):
        #test autolag options, this also test het_lm
        #unfortunately optimal lag=1 for this data
        resid = self.res.resid

        res1 = smsdia.het_arch(resid, maxlag=1, autolag=None, store=True)
        rs1 = res1[-1]

        res2 = smsdia.het_arch(resid, maxlag=5, autolag='aic', store=True)
        rs2 = res2[-1]

        assert_almost_equal(rs2.resols.params, rs1.resols.params, decimal=13)
        assert_almost_equal(res2[:4], res1[:4], decimal=13)

        #test that smallest lag, maxlag=1 works
        res3 = smsdia.het_arch(resid, maxlag=1, autolag='aic')
        assert_almost_equal(res3[:4], res1[:4], decimal=13)

    def test_acorr_breusch_godfrey(self):
        res = self.res

        #bgf = bgtest(fm, order = 4, type="F")
        breuschgodfrey_f = dict(statistic=1.179280833676792,
                               pvalue=0.321197487261203,
                               parameters=(4,195,), distr='f')

        #> bgc = bgtest(fm, order = 4, type="Chisq")
        #> mkhtest(bgc, "breuschpagan_c", "chi2")
        breuschgodfrey_c = dict(statistic=4.771042651230007,
                               pvalue=0.3116067133066697,
                               parameters=(4,), distr='chi2')

        bg = smsdia.acorr_breusch_godfrey(res, nlags=4)
        bg_r = [breuschgodfrey_c['statistic'], breuschgodfrey_c['pvalue'],
                breuschgodfrey_f['statistic'], breuschgodfrey_f['pvalue']]
        assert_almost_equal(bg, bg_r, decimal=13)

        # check that lag choice works
        bg2 = smsdia.acorr_breusch_godfrey(res, nlags=None)
        bg3 = smsdia.acorr_breusch_godfrey(res, nlags=14)
        assert_almost_equal(bg2, bg3, decimal=13)

    def test_acorr_ljung_box(self):

        #unit-test which may be useful later
        #ddof correction for fitted parameters in ARMA(p,q) fitdf=p+q
        #> bt = Box.test(residuals(fm), lag=4, type = "Ljung-Box", fitdf=2)
        #> mkhtest(bt, "ljung_box_4df2", "chi2")
        # ljung_box_4df2 = dict(statistic=5.23587172795227,
        #                       pvalue=0.0729532930400377,
        #                       parameters=(2,), distr='chi2')

        #> bt = Box.test(residuals(fm), lag=4, type = "Box-Pierce", fitdf=2)
        #> mkhtest(bt, "ljung_box_bp_4df2", "chi2")
        # ljung_box_bp_4df2 = dict(statistic=5.12462932741681,
        #                          pvalue=0.0771260128929921,
        #                          parameters=(2,), distr='chi2')


        res = self.res

        #general test

        #> bt = Box.test(residuals(fm), lag=4, type = "Ljung-Box")
        #> mkhtest(bt, "ljung_box_4", "chi2")
        ljung_box_4 = dict(statistic=5.23587172795227, pvalue=0.263940335284713,
                           parameters=(4,), distr='chi2')

        #> bt = Box.test(residuals(fm), lag=4, type = "Box-Pierce")
        #> mkhtest(bt, "ljung_box_bp_4", "chi2")
        ljung_box_bp_4 = dict(statistic=5.12462932741681,
                              pvalue=0.2747471266820692,
                              parameters=(4,), distr='chi2')


        lb, lbpval, bp, bppval = smsdia.acorr_ljungbox(res.resid, 4,
                                                       boxpierce=True)
        compare_t_est([lb[-1], lbpval[-1]], ljung_box_4, decimal=(13, 13))
        compare_t_est([bp[-1], bppval[-1]], ljung_box_bp_4, decimal=(13, 13))

    def test_acorr_ljung_box_big_default(self):
        res = self.res
        #test with big dataset and default lag

        #> bt = Box.test(residuals(fm), type = "Ljung-Box")
        #> mkhtest(bt, "ljung_box_none", "chi2")
        ljung_box_none = dict(statistic=51.03724531797195, pvalue=0.11334744923390,
                              distr='chi2')

        #> bt = Box.test(residuals(fm), type = "Box-Pierce")
        #> mkhtest(bt, "ljung_box_bp_none", "chi2")
        ljung_box_bp_none = dict(statistic=45.12238537034000,
                              pvalue=0.26638168491464,
                              distr='chi2')
        lb, lbpval, bp, bppval = smsdia.acorr_ljungbox(res.resid, boxpierce=True)
        compare_t_est([lb[-1], lbpval[-1]], ljung_box_none, decimal=(13, 13))
        compare_t_est([bp[-1], bppval[-1]], ljung_box_bp_none, decimal=(13, 13))

    def test_acorr_ljung_box_small_default(self):
        res = self.res
        #test with small dataset and default lag

        #> bt = Box.test(residuals(fm), type = "Ljung-Box")
        #> mkhtest(bt, "ljung_box_small", "chi2")
        ljung_box_small = dict(statistic=9.61503968281915, pvalue=0.72507000996945,
                           parameters=(0,), distr='chi2')

        #> bt = Box.test(residuals(fm), type = "Box-Pierce")
        #> mkhtest(bt, "ljung_box_bp_small", "chi2")
        ljung_box_bp_small = dict(statistic=7.41692150864936,
                              pvalue=0.87940785887006,
                              parameters=(0,), distr='chi2')

        lb, lbpval, bp, bppval = smsdia.acorr_ljungbox(res.resid[:30], boxpierce=True)
        compare_t_est([lb[-1], lbpval[-1]], ljung_box_small, decimal=(13, 13))
        compare_t_est([bp[-1], bppval[-1]], ljung_box_bp_small, decimal=(13, 13))


    def test_harvey_collier(self):

        #> hc = harvtest(fm, order.by = NULL, data = list())
        #> mkhtest_f(hc, 'harvey_collier', 't')
        harvey_collier = dict(statistic=0.494432160939874,
                              pvalue=0.6215491310408242,
                              parameters=(198), distr='t')

        #> hc2 = harvtest(fm, order.by=ggdp , data = list())
        #> mkhtest_f(hc2, 'harvey_collier_2', 't')
        harvey_collier_2 = dict(statistic=1.42104628340473,
                                pvalue=0.1568762892441689,
                                parameters=(198), distr='t')

        hc = smsdia.linear_harvey_collier(self.res)
        compare_t_est(hc, harvey_collier, decimal=(12, 12))


    def test_rainbow(self):
        #rainbow test
        #> rt = raintest(fm)
        #> mkhtest_f(rt, 'raintest', 'f')
        raintest = dict(statistic=0.6809600116739604, pvalue=0.971832843583418,
                        parameters=(101, 98), distr='f')

        #> rt = raintest(fm, center=0.4)
        #> mkhtest_f(rt, 'raintest_center_04', 'f')
        raintest_center_04 = dict(statistic=0.682635074191527,
                                  pvalue=0.971040230422121,
                                  parameters=(101, 98), distr='f')

        #> rt = raintest(fm, fraction=0.4)
        #> mkhtest_f(rt, 'raintest_fraction_04', 'f')
        raintest_fraction_04 = dict(statistic=0.565551237772662,
                                    pvalue=0.997592305968473,
                                    parameters=(122, 77), distr='f')

        #> rt = raintest(fm, order.by=ggdp)
        #Warning message:
        #In if (order.by == "mahalanobis") { :
        #  the condition has length > 1 and only the first element will be used
        #> mkhtest_f(rt, 'raintest_order_gdp', 'f')
        raintest_order_gdp = dict(statistic=1.749346160513353,
                                  pvalue=0.002896131042494884,
                                  parameters=(101, 98), distr='f')

        rb = smsdia.linear_rainbow(self.res)
        compare_t_est(rb, raintest, decimal=(13, 14))
        rb = smsdia.linear_rainbow(self.res, frac=0.4)
        compare_t_est(rb, raintest_fraction_04, decimal=(13, 14))


    def test_compare_lr(self):
        res = self.res
        res3 = self.res3 #nested within res
        #lrtest
        #lrt = lrtest(fm, fm2)
        #Model 1: ginv ~ ggdp + lint
        #Model 2: ginv ~ ggdp

        lrtest = dict(loglike1=-763.9752181602237, loglike2=-766.3091902020184,
                      chi2value=4.66794408358942, pvalue=0.03073069384028677,
                      df=(4,3,1))
        lrt = res.compare_lr_test(res3)
        assert_almost_equal(lrt[0], lrtest['chi2value'], decimal=11)
        assert_almost_equal(lrt[1], lrtest['pvalue'], decimal=11)

        waldtest = dict(fvalue=4.65216373312492, pvalue=0.03221346195239025,
                        df=(199,200,1))

        wt = res.compare_f_test(res3)
        assert_almost_equal(wt[0], waldtest['fvalue'], decimal=11)
        assert_almost_equal(wt[1], waldtest['pvalue'], decimal=11)


    def test_compare_nonnested(self):
        res = self.res
        res2 = self.res2
        #jt = jtest(fm, lm(ginv ~ ggdp + tbilrate))
        #Estimate         Std. Error  t value Pr(>|t|)
        jtest = [('M1 + fitted(M2)', 1.591505670785873, 0.7384552861695823,
                  2.155182176352370, 0.032354572525314450, '*'),
                 ('M2 + fitted(M1)', 1.305687653016899, 0.4808385176653064,
                  2.715438978051544, 0.007203854534057954, '**')]

        jt1 = smsdia.compare_j(res2, res)
        assert_almost_equal(jt1, jtest[0][3:5], decimal=13)

        jt2 = smsdia.compare_j(res, res2)
        assert_almost_equal(jt2, jtest[1][3:5], decimal=14)

        #Estimate        Std. Error  z value   Pr(>|z|)
        coxtest = [('fitted(M1) ~ M2', -0.782030488930356, 0.599696502782265,
                    -1.304043770977755, 1.922186587840554e-01, ' '),
                   ('fitted(M2) ~ M1', -2.248817107408537, 0.392656854330139,
                    -5.727181590258883, 1.021128495098556e-08, '***')]

        ct1 = smsdia.compare_cox(res, res2)
        assert_almost_equal(ct1, coxtest[0][3:5], decimal=13)

        ct2 = smsdia.compare_cox(res2, res)
        assert_almost_equal(ct2, coxtest[1][3:5], decimal=12)
        #TODO should be approx

        #     Res.Df Df       F    Pr(>F)
        encomptest = [('M1 vs. ME',    198, -1, 4.644810213266983,
                       0.032354572525313666, '*'),
                      ('M2 vs. ME',    198, -1, 7.373608843521585,
                       0.007203854534058054, '**')]

        # Estimate          Std. Error  t value
        petest = [('M1 + log(fit(M1))-fit(M2)', -229.281878354594596,
                    44.5087822087058598, -5.15139, 6.201281252449979e-07),
                  ('M2 + fit(M1)-exp(fit(M2))',  0.000634664704814,
                   0.0000462387010349, 13.72583, 1.319536115230356e-30)]


    def test_cusum_ols(self):
        #R library(strucchange)
        #> sc = sctest(ginv ~ ggdp + lint, type="OLS-CUSUM")
        #> mkhtest(sc, 'cusum_ols', 'BB')
        cusum_ols = dict(statistic=1.055750610401214, pvalue=0.2149567397376543,
                         parameters=(), distr='BB') #Brownian Bridge

        k_vars=3
        cs_ols = smsdia.breaks_cusumolsresid(self.res.resid, ddof=k_vars) #
        compare_t_est(cs_ols, cusum_ols, decimal=(12, 12))

    def test_breaks_hansen(self):
        #> sc = sctest(ginv ~ ggdp + lint, type="Nyblom-Hansen")
        #> mkhtest(sc, 'breaks_nyblom_hansen', 'BB')
        breaks_nyblom_hansen = dict(statistic=1.0300792740544484,
                                    pvalue=0.1136087530212015,
                                    parameters=(), distr='BB')

        bh = smsdia.breaks_hansen(self.res)
        assert_almost_equal(bh[0], breaks_nyblom_hansen['statistic'],
                            decimal=13)
        #TODO: breaks_hansen doesn't return pvalues


    def test_recursive_residuals(self):

        reccumres_standardize = np.array([-2.151, -3.748, -3.114, -3.096,
        -1.865, -2.230, -1.194, -3.500, -3.638, -4.447, -4.602, -4.631, -3.999,
        -4.830, -5.429, -5.435, -6.554, -8.093, -8.567, -7.532, -7.079, -8.468,
        -9.320, -12.256, -11.932, -11.454, -11.690, -11.318, -12.665, -12.842,
        -11.693, -10.803, -12.113, -12.109, -13.002, -11.897, -10.787, -10.159,
        -9.038, -9.007, -8.634, -7.552, -7.153, -6.447, -5.183, -3.794, -3.511,
        -3.979, -3.236, -3.793, -3.699, -5.056, -5.724, -4.888, -4.309, -3.688,
        -3.918, -3.735, -3.452, -2.086, -6.520, -7.959, -6.760, -6.855, -6.032,
        -4.405, -4.123, -4.075, -3.235, -3.115, -3.131, -2.986, -1.813, -4.824,
        -4.424, -4.796, -4.000, -3.390, -4.485, -4.669, -4.560, -3.834, -5.507,
        -3.792, -2.427, -1.756, -0.354, 1.150, 0.586, 0.643, 1.773, -0.830,
        -0.388, 0.517, 0.819, 2.240, 3.791, 3.187, 3.409, 2.431, 0.668, 0.957,
        -0.928, 0.327, -0.285, -0.625, -2.316, -1.986, -0.744, -1.396, -1.728,
        -0.646, -2.602, -2.741, -2.289, -2.897, -1.934, -2.532, -3.175, -2.806,
        -3.099, -2.658, -2.487, -2.515, -2.224, -2.416, -1.141, 0.650, -0.947,
        0.725, 0.439, 0.885, 2.419, 2.642, 2.745, 3.506, 4.491, 5.377, 4.624,
        5.523, 6.488, 6.097, 5.390, 6.299, 6.656, 6.735, 8.151, 7.260, 7.846,
        8.771, 8.400, 8.717, 9.916, 9.008, 8.910, 8.294, 8.982, 8.540, 8.395,
        7.782, 7.794, 8.142, 8.362, 8.400, 7.850, 7.643, 8.228, 6.408, 7.218,
        7.699, 7.895, 8.725, 8.938, 8.781, 8.350, 9.136, 9.056, 10.365, 10.495,
        10.704, 10.784, 10.275, 10.389, 11.586, 11.033, 11.335, 11.661, 10.522,
        10.392, 10.521, 10.126, 9.428, 9.734, 8.954, 9.949, 10.595, 8.016,
        6.636, 6.975])

        rr = smsdia.recursive_olsresiduals(self.res, skip=3, alpha=0.95)
        assert_equal(np.round(rr[5][1:], 3), reccumres_standardize) #extra zero in front
        #assert_equal(np.round(rr[3][4:], 3), np.diff(reccumres_standardize))
        assert_almost_equal(rr[3][4:], np.diff(reccumres_standardize),3)
        assert_almost_equal(rr[4][3:].std(ddof=1), 10.7242, decimal=4)

        #regression number, visually checked with graph from gretl
        ub0 = np.array([ 13.37318571,  13.50758959,  13.64199346,  13.77639734,
                        13.91080121])
        ub1 = np.array([ 39.44753774,  39.58194162,  39.7163455 ,  39.85074937,
                        39.98515325])
        lb, ub = rr[6]
        assert_almost_equal(ub[:5], ub0, decimal=7)
        assert_almost_equal(lb[:5], -ub0, decimal=7)
        assert_almost_equal(ub[-5:], ub1, decimal=7)
        assert_almost_equal(lb[-5:], -ub1, decimal=7)

        #test a few values with explicit OLS
        endog = self.res.model.endog
        exog = self.res.model.exog
        params = []
        ypred = []
        for i in range(3,10):
            resi = OLS(endog[:i], exog[:i]).fit()
            ypred.append(resi.model.predict(resi.params, exog[i]))
            params.append(resi.params)
        assert_almost_equal(rr[2][3:10], ypred, decimal=12)
        assert_almost_equal(rr[0][3:10], endog[3:10] - ypred, decimal=12)
        assert_almost_equal(rr[1][2:9], params, decimal=12)

    def test_normality(self):
        res = self.res

        #> library(nortest) #Lilliefors (Kolmogorov-Smirnov) normality test
        #> lt = lillie.test(residuals(fm))
        #> mkhtest(lt, "lilliefors", "-")
        lilliefors1 = dict(statistic=0.0723390908786589,
                          pvalue=0.01204113540102896, parameters=(), distr='-')

        #> lt = lillie.test(residuals(fm)**2)
        #> mkhtest(lt, "lilliefors", "-")
        lilliefors2 = dict(statistic=0.301311621898024,
                          pvalue=1.004305736618051e-51,
                          parameters=(), distr='-')

        #> lt = lillie.test(residuals(fm)[1:20])
        #> mkhtest(lt, "lilliefors", "-")
        lilliefors3 = dict(statistic=0.1333956004203103,
                          pvalue=0.20, parameters=(), distr='-')

        lf1 = smsdia.lilliefors(res.resid)
        lf2 = smsdia.lilliefors(res.resid**2)
        lf3 = smsdia.lilliefors(res.resid[:20])

        compare_t_est(lf1, lilliefors1, decimal=(14, 14))
        compare_t_est(lf2, lilliefors2, decimal=(14, 14))  # pvalue very small
        assert_allclose(lf2[1], lilliefors2['pvalue'], rtol=1e-10)
        compare_t_est(lf3, lilliefors3, decimal=(14, 1))
        # R uses different approximation for pvalue in last case

        #> ad = ad.test(residuals(fm))
        #> mkhtest(ad, "ad3", "-")
        adr1 = dict(statistic=1.602209621518313, pvalue=0.0003937979149362316,
                    parameters=(), distr='-')

        #> ad = ad.test(residuals(fm)**2)
        #> mkhtest(ad, "ad3", "-")
        adr2 = dict(statistic=np.inf, pvalue=np.nan, parameters=(), distr='-')

        #> ad = ad.test(residuals(fm)[1:20])
        #> mkhtest(ad, "ad3", "-")
        adr3 = dict(statistic=0.3017073732210775, pvalue=0.5443499281265933,
                    parameters=(), distr='-')

        ad1 = smsdia.normal_ad(res.resid)
        compare_t_est(ad1, adr1, decimal=(11, 13))
        ad2 = smsdia.normal_ad(res.resid**2)
        assert_(np.isinf(ad2[0]))
        ad3 = smsdia.normal_ad(res.resid[:20])
        compare_t_est(ad3, adr3, decimal=(11, 12))


    def test_influence(self):
        res = self.res

        #this test is slow
        infl = oi.OLSInfluence(res)

        path = os.path.join(cur_dir, "results", "influence_lsdiag_R.json")
        with open(path, 'r') as fp:
            lsdiag = json.load(fp)

        #basic
        assert_almost_equal(np.array(lsdiag['cov.scaled']).reshape(3, 3),
                            res.cov_params(), decimal=14)
        assert_almost_equal(np.array(lsdiag['cov.unscaled']).reshape(3, 3),
                            res.normalized_cov_params, decimal=14)

        c0, c1 = infl.cooks_distance #TODO: what's c1


        assert_almost_equal(c0, lsdiag['cooks'], decimal=14)
        assert_almost_equal(infl.hat_matrix_diag, lsdiag['hat'], decimal=14)
        assert_almost_equal(infl.resid_studentized_internal,
                            lsdiag['std.res'], decimal=14)

        #slow:
        #infl._get_all_obs()  #slow, nobs estimation loop, called implicitly
        dffits, dffth = infl.dffits
        assert_almost_equal(dffits, lsdiag['dfits'], decimal=14)
        assert_almost_equal(infl.resid_studentized_external,
                            lsdiag['stud.res'], decimal=14)

        import pandas
        fn = os.path.join(cur_dir,"results/influence_measures_R.csv")
        infl_r = pandas.read_csv(fn, index_col=0)
        conv = lambda s: 1 if s=='TRUE' else 0
        fn = os.path.join(cur_dir,"results/influence_measures_bool_R.csv")
        #not used yet:
        #infl_bool_r  = pandas.read_csv(fn, index_col=0,
        #                                converters=dict(zip(lrange(7),[conv]*7)))
        infl_r2 = np.asarray(infl_r)
        assert_almost_equal(infl.dfbetas, infl_r2[:,:3], decimal=13)
        assert_almost_equal(infl.cov_ratio, infl_r2[:,4], decimal=14)
        #duplicates
        assert_almost_equal(dffits, infl_r2[:,3], decimal=14)
        assert_almost_equal(c0, infl_r2[:,5], decimal=14)
        assert_almost_equal(infl.hat_matrix_diag, infl_r2[:,6], decimal=14)

        #Note: for dffits, R uses a threshold around 0.36, mine: dffits[1]=0.24373
        #TODO: finish and check thresholds and pvalues
        '''
        R has
        >>> np.nonzero(np.asarray(infl_bool_r["dffit"]))[0]
        array([  6,  26,  63,  76,  90, 199])
        >>> np.nonzero(np.asarray(infl_bool_r["cov.r"]))[0]
        array([  4,  26,  59,  61,  63,  72,  76,  84,  91,  92,  94,  95, 108,
               197, 198])
        >>> np.nonzero(np.asarray(infl_bool_r["hat"]))[0]
        array([ 62,  76,  84,  90,  91,  92,  95, 108, 197, 199])
        '''


class TestDiagnosticGPandas(TestDiagnosticG):

    @classmethod
    def setup_class(cls):
        d = macrodata.load_pandas().data
        #growth rates
        d['gs_l_realinv'] = 400 * np.log(d['realinv']).diff()
        d['gs_l_realgdp'] = 400 * np.log(d['realgdp']).diff()
        d['lint'] = d['realint'].shift(1)
        d['tbilrate'] = d['tbilrate'].shift(1)

        d = d.dropna()
        cls.d = d
        endogg = d['gs_l_realinv']
        exogg = add_constant(d[['gs_l_realgdp', 'lint']])
        exogg2 = add_constant(d[['gs_l_realgdp', 'tbilrate']])
        exogg3 = add_constant(d[['gs_l_realgdp']])

        res_ols = OLS(endogg, exogg).fit()
        res_ols2 = OLS(endogg, exogg2).fit()

        res_ols3 = OLS(endogg, exogg3).fit()

        cls.res = res_ols
        cls.res2 = res_ols2
        cls.res3 = res_ols3
        cls.endog = cls.res.model.endog
        cls.exog = cls.res.model.exog


def grangertest():
    #> gt = grangertest(ginv, ggdp, order=4)
    #> gt
    #Granger causality test
    #
    #Model 1: ggdp ~ Lags(ggdp, 1:4) + Lags(ginv, 1:4)
    #Model 2: ggdp ~ Lags(ggdp, 1:4)

    grangertest = dict(fvalue=1.589672703015157, pvalue=0.178717196987075,
                       df=(198,193))


def test_outlier_influence_funcs(reset_randomstate):
    #smoke test
    x = add_constant(np.random.randn(10, 2))
    y = x.sum(1) + np.random.randn(10)
    res = OLS(y, x).fit()
    out_05 = oi.summary_table(res)
    # GH3344 : Check alpha has an effect
    out_01 = oi.summary_table(res, alpha=0.01)
    assert_(np.all(out_01[1][:, 6] <= out_05[1][:, 6]))
    assert_(np.all(out_01[1][:, 7] >= out_05[1][:, 7]))

    res2 = OLS(y, x[:,0]).fit()
    oi.summary_table(res2, alpha=0.05)
    infl = res2.get_influence()
    infl.summary_table()


def test_influence_wrapped():
    from pandas import DataFrame
    from pandas.util.testing import assert_series_equal

    d = macrodata.load_pandas().data
    #growth rates
    gs_l_realinv = 400 * np.log(d['realinv']).diff().dropna()
    gs_l_realgdp = 400 * np.log(d['realgdp']).diff().dropna()
    lint = d['realint'][:-1]

    # re-index these because they won't conform to lint
    gs_l_realgdp.index = lint.index
    gs_l_realinv.index = lint.index

    data = dict(const=np.ones_like(lint), lint=lint, lrealgdp=gs_l_realgdp)
    #order is important
    exog = DataFrame(data, columns=['const','lrealgdp','lint'])

    res = OLS(gs_l_realinv, exog).fit()

    #basic
    # already tested
    #assert_almost_equal(lsdiag['cov.scaled'],
    #                    res.cov_params().values.ravel(), decimal=14)
    #assert_almost_equal(lsdiag['cov.unscaled'],
    #                    res.normalized_cov_params.values.ravel(), decimal=14)

    infl = oi.OLSInfluence(res)

    # smoke test just to make sure it works, results separately tested
    df = infl.summary_frame()
    assert_(isinstance(df, DataFrame))

    #this test is slow
    path = os.path.join(cur_dir, "results", "influence_lsdiag_R.json")
    with open(path, "r") as fp:
        lsdiag = json.load(fp)

    c0, c1 = infl.cooks_distance #TODO: what's c1, it's pvalues? -ss


    #NOTE: we get a hard-cored 5 decimals with pandas testing
    assert_almost_equal(c0, lsdiag['cooks'], 14)
    assert_almost_equal(infl.hat_matrix_diag, (lsdiag['hat']), 14)
    assert_almost_equal(infl.resid_studentized_internal,
                        lsdiag['std.res'], 14)

    #slow:
    dffits, dffth = infl.dffits
    assert_almost_equal(dffits, lsdiag['dfits'], 14)
    assert_almost_equal(infl.resid_studentized_external,
                        lsdiag['stud.res'], 14)

    import pandas
    fn = os.path.join(cur_dir,"results/influence_measures_R.csv")
    infl_r = pandas.read_csv(fn, index_col=0)
    conv = lambda s: 1 if s=='TRUE' else 0
    fn = os.path.join(cur_dir,"results/influence_measures_bool_R.csv")
    #not used yet:
    #infl_bool_r  = pandas.read_csv(fn, index_col=0,
    #                                converters=dict(zip(lrange(7),[conv]*7)))
    infl_r2 = np.asarray(infl_r)
    #TODO: finish wrapping this stuff
    assert_almost_equal(infl.dfbetas, infl_r2[:,:3], decimal=13)
    assert_almost_equal(infl.cov_ratio, infl_r2[:,4], decimal=14)


def test_influence_dtype():
    # see #2148  bug when endog is integer
    y = np.ones(20)
    np.random.seed(123)
    x = np.random.randn(20, 3)
    res1 = OLS(y, x).fit()

    res2 = OLS(y*1., x).fit()
    cr1 = res1.get_influence().cov_ratio
    cr2 = res2.get_influence().cov_ratio
    assert_allclose(cr1, cr2, rtol=1e-14)
    # regression test for values
    cr3 = np.array(
      [ 1.22239215,  1.31551021,  1.52671069,  1.05003921,  0.89099323,
        1.57405066,  1.03230092,  0.95844196,  1.15531836,  1.21963623,
        0.87699564,  1.16707748,  1.10481391,  0.98839447,  1.08999334,
        1.35680102,  1.46227715,  1.45966708,  1.13659521,  1.22799038])
    assert_almost_equal(cr1, cr3, decimal=8)


def get_duncan_data():
    # results from R with NA -> 1. Just testing interface here because
    # outlier_test is just a wrapper
    labels = ['accountant', 'pilot', 'architect', 'author', 'chemist',
              'minister', 'professor', 'dentist', 'reporter', 'engineer',
              'undertaker', 'lawyer', 'physician', 'welfare.worker', 'teacher',
              'conductor', 'contractor', 'factory.owner', 'store.manager',
              'banker', 'bookkeeper', 'mail.carrier', 'insurance.agent',
              'store.clerk', 'carpenter', 'electrician', 'RR.engineer',
              'machinist', 'auto.repairman', 'plumber', 'gas.stn.attendant',
              'coal.miner', 'streetcar.motorman', 'taxi.driver',
              'truck.driver', 'machine.operator', 'barber', 'bartender',
              'shoe.shiner', 'cook', 'soda.clerk', 'watchman', 'janitor',
              'policeman', 'waiter']
    #Duncan's prestige data from car
    exog = [[1.0, 62.0, 86.0], [1.0, 72.0, 76.0], [1.0, 75.0, 92.0],
            [1.0, 55.0, 90.0], [1.0, 64.0, 86.0], [1.0, 21.0, 84.0],
            [1.0, 64.0, 93.0], [1.0, 80.0, 100.0], [1.0, 67.0, 87.0],
            [1.0, 72.0, 86.0], [1.0, 42.0, 74.0], [1.0, 76.0, 98.0],
            [1.0, 76.0, 97.0], [1.0, 41.0, 84.0], [1.0, 48.0, 91.0],
            [1.0, 76.0, 34.0], [1.0, 53.0, 45.0], [1.0, 60.0, 56.0],
            [1.0, 42.0, 44.0], [1.0, 78.0, 82.0], [1.0, 29.0, 72.0],
            [1.0, 48.0, 55.0], [1.0, 55.0, 71.0], [1.0, 29.0, 50.0],
            [1.0, 21.0, 23.0], [1.0, 47.0, 39.0], [1.0, 81.0, 28.0],
            [1.0, 36.0, 32.0], [1.0, 22.0, 22.0], [1.0, 44.0, 25.0],
            [1.0, 15.0, 29.0], [1.0, 7.0, 7.0], [1.0, 42.0, 26.0],
            [1.0, 9.0, 19.0], [1.0, 21.0, 15.0], [1.0, 21.0, 20.0],
            [1.0, 16.0, 26.0], [1.0, 16.0, 28.0], [1.0, 9.0, 17.0],
            [1.0, 14.0, 22.0], [1.0, 12.0, 30.0], [1.0, 17.0, 25.0],
            [1.0, 7.0, 20.0], [1.0, 34.0, 47.0], [1.0, 8.0, 32.0]]
    endog = [ 82.,  83.,  90.,  76.,  90.,  87.,  93.,  90.,  52.,  88.,  57.,
        89.,  97.,  59.,  73.,  38.,  76.,  81.,  45.,  92.,  39.,  34.,
        41.,  16.,  33.,  53.,  67.,  57.,  26.,  29.,  10.,  15.,  19.,
        10.,  13.,  24.,  20.,   7.,   3.,  16.,   6.,  11.,   8.,  41.,
        10.]

    return endog, exog, labels


def test_outlier_test():
    endog, exog, labels = get_duncan_data()
    ndarray_mod = OLS(endog, exog).fit()
    rstudent =  [3.1345185839, -2.3970223990,  2.0438046359, -1.9309187757,
                 1.8870465798, -1.7604905300, -1.7040324156,  1.6024285876,
                 -1.4332485037, -1.1044851583,  1.0688582315,  1.0185271840,
                 -0.9024219332, -0.9023876471, -0.8830953936,  0.8265782334,
                 0.8089220547,  0.7682770197,  0.7319491074, -0.6665962829,
                 0.5227352794, -0.5135016547,  0.5083881518,  0.4999224372,
                 -0.4980818221, -0.4759717075, -0.4293565820, -0.4114056499,
                 -0.3779540862,  0.3556874030,  0.3409200462,  0.3062248646,
                 0.3038999429, -0.3030815773, -0.1873387893,  0.1738050251,
                 0.1424246593, -0.1292266025,  0.1272066463, -0.0798902878,
                 0.0788467222,  0.0722556991,  0.0505098280,  0.0233215136,
                 0.0007112055]
    unadj_p = [0.003177202, 0.021170298, 0.047432955, 0.060427645, 0.066248120,
               0.085783008, 0.095943909, 0.116738318, 0.159368890, 0.275822623,
               0.291386358, 0.314400295, 0.372104049, 0.372122040, 0.382333561,
               0.413260793, 0.423229432, 0.446725370, 0.468363101, 0.508764039,
               0.603971990, 0.610356737, 0.613905871, 0.619802317, 0.621087703,
               0.636621083, 0.669911674, 0.682917818, 0.707414459, 0.723898263,
               0.734904667, 0.760983108, 0.762741124, 0.763360242, 0.852319039,
               0.862874018, 0.887442197, 0.897810225, 0.899398691, 0.936713197,
               0.937538115, 0.942749758, 0.959961394, 0.981506948, 0.999435989]
    bonf_p = [0.1429741, 0.9526634, 2.1344830, 2.7192440, 2.9811654, 3.8602354,
            4.3174759, 5.2532243, 7.1716001, 12.4120180, 13.1123861, 14.1480133,
            16.7446822, 16.7454918, 17.2050103, 18.5967357, 19.0453245,
            20.1026416, 21.0763395, 22.8943818, 27.1787396, 27.4660532,
            27.6257642, 27.8911043, 27.9489466, 28.6479487, 30.1460253,
            30.7313018, 31.8336506, 32.5754218, 33.0707100, 34.2442399,
            34.3233506, 34.3512109, 38.3543568, 38.8293308, 39.9348989,
            40.4014601, 40.4729411, 42.1520939, 42.1892152, 42.4237391,
            43.1982627, 44.1678127, 44.9746195]
    bonf_p = np.array(bonf_p)
    bonf_p[bonf_p > 1] = 1
    sorted_labels = ["minister", "reporter", "contractor", "insurance.agent",
            "machinist", "store.clerk", "conductor", "factory.owner",
            "mail.carrier", "streetcar.motorman", "carpenter", "coal.miner",
            "bartender", "bookkeeper", "soda.clerk", "chemist", "RR.engineer",
            "professor", "electrician", "gas.stn.attendant", "auto.repairman",
            "watchman", "banker", "machine.operator", "dentist", "waiter",
            "shoe.shiner", "welfare.worker", "plumber", "physician", "pilot",
            "engineer", "accountant", "lawyer", "undertaker", "barber",
            "store.manager", "truck.driver", "cook", "janitor", "policeman",
            "architect", "teacher", "taxi.driver", "author"]

    res2 = np.c_[rstudent, unadj_p, bonf_p]
    res = oi.outlier_test(ndarray_mod, method='b', labels=labels, order=True)
    np.testing.assert_almost_equal(res.values, res2, 7)
    np.testing.assert_equal(res.index.tolist(), sorted_labels)  # pylint: disable-msg=E1103

    data = pd.DataFrame(np.column_stack((endog, exog)),
                        columns='y const var1 var2'.split(),
                        index=labels)

    # check `order` with pandas bug in #3971
    res_pd = OLS.from_formula('y ~ const + var1 + var2 - 0', data).fit()

    res_outl2 = oi.outlier_test(res_pd, method='b', order=True)
    assert_almost_equal(res_outl2.values, res2, 7)
    assert_equal(res_outl2.index.tolist(), sorted_labels)

    res_outl1 = res_pd.outlier_test(method='b')
    res_outl1 = res_outl1.sort_values(['unadj_p'], ascending=True)
    assert_almost_equal(res_outl1.values, res2, 7)
    assert_equal(res_outl1.index.tolist(), sorted_labels)
    assert_array_equal(res_outl2.index, res_outl1.index)

    # additional keywords in method
    res_outl3 = res_pd.outlier_test(method='b', order=True)
    assert_equal(res_outl3.index.tolist(), sorted_labels)
    res_outl4 = res_pd.outlier_test(method='b', order=True, cutoff=0.15)
    assert_equal(res_outl4.index.tolist(), sorted_labels[:1])


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-vvs', '-x', '--pdb'])

    #t = TestDiagnosticG()
    #t.test_basic()
    #t.test_hac()
    #t.test_acorr_breusch_godfrey()
    #t.test_acorr_ljung_box()
    #t.test_het_goldfeldquandt()
    #t.test_het_breusch_pagan()
    #t.test_het_white()
    #t.test_compare_lr()
    #t.test_compare_nonnested()
    #t.test_influence()


    ##################################################

    '''
    J test

    Model 1: ginv ~ ggdp + lint
    Model 2: ginv ~ ggdp + tbilrate
                             Estimate         Std. Error t value  Pr(>|t|)
    M1 + fitted(M2) 1.591505670785873 0.7384552861695823 2.15518 0.0323546 *
    M2 + fitted(M1) 1.305687653016899 0.4808385176653064 2.71544 0.0072039 **
    ---
    Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1


     = lm(ginv ~ ggdp + tbilrate)
    > ct = coxtest(fm, fm3)
    > ct
    Cox test

    Model 1: ginv ~ ggdp + lint
    Model 2: ginv ~ ggdp + tbilrate
                              Estimate        Std. Error  z value   Pr(>|z|)
    fitted(M1) ~ M2 -0.782030488930356 0.599696502782265 -1.30404    0.19222
    fitted(M2) ~ M1 -2.248817107408537 0.392656854330139 -5.72718 1.0211e-08 ***
    ---
    Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1



    > et = encomptest(fm, fm3)
    > et
    Encompassing test

    Model 1: ginv ~ ggdp + lint
    Model 2: ginv ~ ggdp + tbilrate
    Model E: ginv ~ ggdp + lint + tbilrate
              Res.Df Df       F    Pr(>F)
    M1 vs. ME    198 -1 4.64481 0.0323546 *
    M2 vs. ME    198 -1 7.37361 0.0072039 **
    ---
    Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1


    > fm4 = lm(realinv ~ realgdp + realint, data=d)
    > fm5 = lm(log(realinv) ~ realgdp + realint, data=d)
    > pet = petest(fm4, fm5)
    > pet
    PE test

    Model 1: realinv ~ realgdp + realint
    Model 2: log(realinv) ~ realgdp + realint
                                          Estimate          Std. Error  t value
    M1 + log(fit(M1))-fit(M2) -229.281878354594596 44.5087822087058598 -5.15139
    M2 + fit(M1)-exp(fit(M2))    0.000634664704814  0.0000462387010349 13.72583
                                Pr(>|t|)
    M1 + log(fit(M1))-fit(M2) 6.2013e-07 ***
    M2 + fit(M1)-exp(fit(M2)) < 2.22e-16 ***
    ---
    Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

    '''
