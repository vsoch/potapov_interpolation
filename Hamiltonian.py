# -*- coding: utf-8 -*-
"""
Created on Mon Mar 31 2015

@author: gil
@title: Hamiltonian.py
"""

import Roots
import Potapov
import Examples
import functions

import numpy as np
import numpy.linalg as la
import sympy as sp
import itertools

class Hamiltonian():
    def __init__(self,roots,modes,delays,delay_indices,start_nonlin,
        duration_nonlin,
        indices_of_refraction = 1.,chi_order = 3, photons_annihilated = 2,
        nonlin_coeff = 1.):
        self.roots = roots
        self.modes = modes
        self.delays = delays
        self.delay_indices = delay_indices
        self.start_nonlin = start_nonlin
        self.duration_nonlin = duration_nonlin
        self.indices_of_refraction = indices_of_refraction
        self.chi_order=chi_order
        self.photons_annihilated=photons_annihilated
        self.m = len(roots)
        self.a = [sp.symbols('a_'+str(i)) for i in range(self.m)]
        self.a_H = [sp.symbols('a^H_'+str(i)) for i in range(self.m)]
        self.H = None
        self.nonlin_coeff = nonlin_coeff

    def make_nonlin_term_sp(self,combination,pm_arr):
        '''
        Make symbolic nonlinear term using sympy

        Args:
            combination (tuple/list of integers): which terms to include
            pm_arr (tuple/list of +1 and -1): creation and annihilation
                indicators for the respective terms in combination.
        Returns:
            symbolic expression for the combination of creation and annihilation
            operators.
        '''
        r = 1.
        for index,sign in zip(combination,pm_arr):
            if sign == 1:
                r*= self.a_H[index]
            else:
                r *= self.a[index]
        return r

    def make_list_of_pm_arr(self,):
        '''
        Returns:
            List of lists of +1 and -1. The length of each list is chi_order+1.
            The number of -1's in each list is the number of photons annihilated.
            Each unique combination exists once.
        '''
        plus_minus_combinations = list(itertools.combinations(
            range(self.chi_order + 1), self.photons_annihilated))  ## pick which fields are annihilated
        list_of_pm_arr = []
        for tup in plus_minus_combinations:
            ls = [1]*(self.chi_order+1)
            for i in tup:
                ls[i]=-1
            list_of_pm_arr.append(ls)
        return list_of_pm_arr

    def weight(self,combination,pm_arr):
        '''
        The weight to give to each nonlinear term characterized by the given
        combination and pm_arr.

        Args:
            combination (list/tuple of integers): which modes/roots to pick
            pm_arr (list of +1 and -1): creation and annihilation of modes
        Returns:
            The weight to add to the Hamiltonian
        '''
        roots_to_use = np.array([self.roots[i] for i in combination])
        modes_to_use = [self.modes[i] for i in combination]
        return functions.make_nonlinear_interaction(
                    roots_to_use, modes_to_use, self.delays, self.delay_indices,
                    self.start_nonlin, self.duration_nonlin, pm_arr,
                    self.indices_of_refraction)

    def make_weights(self,):
        '''
        Make a dict to store the weights for the selected components and the
        creation/annihilation information.

        Returns:
            A dictionary of weights. Each key is a tuple of a combination tuple
            and a pm_arr tuple (a tuple of +1 and -1).
        '''
        ## TODO: add a priori check to restrict exponential growth on the number
        ## of nonlienar coefficients
        list_of_pm_arr = self.make_list_of_pm_arr()
        weights = {}
        for pm_arr in list_of_pm_arr:
            field_combinations = itertools.combinations_with_replacement(
                range(self.m), self.chi_order+1)
            for combination in field_combinations:
                weights[tuple(combination),tuple(pm_arr)] = self.weight(combination,pm_arr)
        return weights

    def make_nonlin_H(self,eps=1e-5):
        '''
        Make a nonlinear Hamiltonian based on nonlinear interaction terms
        Args:
            eps (optional[float]): Cutoff for the significance of a particular term.
        Returns:
            A symbolic expression for the nonlinear Hamiltonian.
        '''

        weights = self.make_weights()
        significant_weights =  {k:v for k,v in weights.iteritems() if abs(v) > eps}

        H_nonlin_sp = 0.
        for combination,pm_arr in significant_weights:
            H_nonlin_sp += (self.make_nonlin_term_sp(combination,pm_arr) *
                            significant_weights[combination,pm_arr])
        return H_nonlin_sp

    def make_lin_H(self,Omega):
        '''
        Make a linear Hamiltonian based on Omega.
        Args:
            Omega (complex-valued matrix) describes the Hamiltonian of the system.
        Returns:
            A symbolic expression for the nonlinear Hamiltonian.
        '''
        H_lin_sp = 0.
        for i in range(self.m):
            for j in range(self.m):
                H_lin_sp += self.a_H[i]*self.a[j]*Omega[i,j]
        return H_lin_sp

    def make_H(self,Omega,eps=1e-5):
        '''
        Make a Hamiltonian combining the linear and nonlinear parts.
        Args:
            Omega (complex-valued matrix) describes the Hamiltonian of the system.
            Omega = -1j*A        #### full dynamics (not necessarily Hermitian)
            Omega = (A-A.H)/(2j) #### closed dynamics only (Hermitian part of above)
            eps (optional[float]): Cutoff for the significance of a particular term.
        Returns:
            A symbolic expression for the full Hamiltonian.
        '''
        H_nonlin = self.make_nonlin_H(eps)
        H_lin = self.make_lin_H(Omega)
        self.H = H_lin + H_nonlin * self.nonlin_coeff
        return self.H

    def make_sp_conj(self,A):
        '''
        Returns the symbolic conjugate of A.
        Args:
            A (symbolic expression in symbols a[i] and a_H[i])
        Returns:
            The complex conjugate of A
        '''
        A_H = sp.conjugate(A)
        for i in range(len(self.a)):
            A_H = A_H.subs(sp.conjugate(self.a[i]),self.a_H[i])
            A_H = A_H.subs(sp.conjugate(self.a_H[i]),self.a[i])
        return A_H

    def make_eq_motion(self,):
        '''
        Input is a tuple or list, output is a matrix vector.
        This generates Hamilton's equations of motion for a and a^H

        Returns:
            A function that yields the Hamiltonian equations of motion based on
            the Hamiltonian given.
            The equations of motion take an array as an input and return a column
            vector as an output.
        '''
        A_H = self.make_sp_conj(self.H)
        diff_ls = ([1j*sp.diff(self.H,var) for var in self.a_H] +
                   [-1j*sp.diff(A_H,var) for var in self.a])
        fs = [sp.lambdify( tuple(self.a+self.a_H),expression) for expression in diff_ls ]
        return lambda arr: (np.asmatrix([ f(* arr ) for f in fs])).T
