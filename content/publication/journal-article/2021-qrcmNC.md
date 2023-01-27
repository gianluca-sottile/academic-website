---
authors:
- Sottile, G.
- Frumento, P.
date: "2021-09-01T00:00:00Z"
title: Parametric estimation of non-crossing quantile functions
publication: '*Statistical Modelling*'  
publication_types:
 - "2"
links:
- name: Link
  url: https://journals.sagepub.com/doi/10.1177/1471082X211036517
- name: Code
  url: https://cran.r-project.org/web/packages/qrcm/index.html
---

*Abstract*

Quantile regression (QR) has gained popularity during the last decades, and is now considered a standard method by applied statisticians and practitioners in various fields. In this work, we applied QR to investigate climate change by analysing historical temperatures in the Arctic Circle. This approach proved very flexible and allowed to investigate the tails of the distribution, that correspond to extreme events. The presence of quantile crossing, however, prevented using the fitted model for prediction and extrapolation. In search of a possible solution, we first considered a different version of QR, in which the QR coefficients were described by parametric functions. This alleviated the crossing problem, but did not eliminate it completely. Finally, we exploited the imposed parametric structure to formulate a constrained optimization algorithm that enforced monotonicity. The proposed example showed how the relatively unexplored field of parametric quantile functions could offer new solutions to the long-standing problem of quantile crossing. Our approach is particularly convenient in situations, like the analysis of time series, in which the fitted model may be used to predict extreme quantiles or to perform extrapolation. The described estimator has been implemented in the R package qrcm.
