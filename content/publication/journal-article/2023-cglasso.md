---
authors:
- Augugliaro, L.
- Sottile, G.
- Wit, E.C.
- Vinciotti, V.
date: "2023-01-18T00:00:00Z"
title: cglasso An R Package for Conditional Graphical Lasso Inference with Censored and Missing Values
publication: '*Journal of Statistical Software*'  
publication_types:
 - "2"
links:
- name: Link
  url: https://www.jstatsoft.org/article/view/v105i01
- name: Code
  url: https://cran.r-project.org/web/packages/cglasso/index.html
---

<font size="5"> <center><b> Abstract </b> </center></font>

<p style="text-align: justify;">
Sparse graphical models have revolutionized multivariate inference. With the advent of high-dimensional multivariate data in many applied fields, these methods are able to detect a much lower-dimensional structure, often represented via a sparse conditional independence graph. There have been numerous extensions of such methods in the past decade. Many practical applications have additional covariates or suffer from missing or censored data. Despite the development of these extensions of sparse inference methods for graphical models, there have been so far no implementations for, e.g., conditional graphical models. Here we present the general-purpose package cglasso for estimating sparse conditional Gaussian graphical models with potentially missing or censored data. The method employs an efficient expectation-maximization estimation of an ℓ1 -penalized likelihood via a block-coordinate descent algorithm. The package has a user-friendly data manipulation interface. It estimates a solution path and includes various automatic selection algorithms for the two ℓ1 tuning parameters, associated with the sparse precision matrix and sparse regression coefficients, respectively. The package pays particular attention to the visualization of the results, both by means of marginal tables and figures, and of the inferred conditional independence graphs. This package provides a unique and computational efficient implementation of a conditional Gaussian graphical model that is able to deal with the additional complications of missing and censored data. As such it constitutes an important contribution for empirical scientists wishing to detect sparse structures in high-dimensional data.
</p>
