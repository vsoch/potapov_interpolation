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
import scipy.constants as consts
import itertools

from sympy.physics.quantum import *
from sympy.physics.quantum.boson import *
from sympy.physics.quantum.operatorordering import *

class Chi_nonlin():
    '''
    Class to store the information in a particular nonlinear chi element.

    Args:
        delay_indices (list of indices): indices of delays to use.
        start_nonlin (positive float or list of positive floats): location of
            nonlinear crystal with respect to each edge.
        length_nonlin (float): length of the nonlinear element.
        chi_order (optional [int]): order of nonlinearity
        chi_function (optional [function]): strength of nonlinearity.
            first chi_order args are frequencies, next
            first chi_order args are frequencies, next chi_order args are
            indices of polarization.
    '''
    def __init__(self,delay_indices,start_nonlin,length_nonlin,indices_of_refraction,
                 chi_order=3,chi_function=None):
        self.delay_indices = delay_indices
        self.start_nonlin = start_nonlin
        self.length_nonlin = length_nonlin
        self.chi_order = chi_order
        self.indices_of_refraction = indices_of_refraction

        if chi_function == None:
            def chi_func(a,b,c,d,i,j,k,l):
                return 1.  #if abs(a+b+c+d) <= 2. else 0.
            self.chi_function = chi_func
        else:
            self.chi_function = chi_function

class Hamiltonian():
    def __init__(self,roots,modes,delays,
        #delay_indices,start_nonlin, length_nonlin, indices_of_refraction = 1.,
        #chi_order = 3, photons_annihilated = 2,
        nonlin_coeff = 1.,polarizations = None,
        cross_sectional_area = 1e-10,
        chi_nonlinearities = [],
        ):
        self.roots = roots
        self.modes = modes
        self.m = len(roots)
        self.delays = delays

        self.normalize_modes()

        self.cross_sectional_area = cross_sectional_area

        if polarizations == None:
            self.polarizations = [1.]*self.m
        else:
            self.polarizations = polarizations


        self.volumes = self.mode_volumes()
        self.E_field_weights = self.make_E_field_weights()

        self.chi_nonlinearities = chi_nonlinearities
        ###
        # self.delay_indices = delay_indices
        # self.start_nonlin = start_nonlin
        # self.length_nonlin = length_nonlin
        # self.indices_of_refraction = indices_of_refraction
        # self.chi_order=chi_order
        ##

        ##
        #self.photons_annihilated=photons_annihilated  ## <-- let's get rid of that
        ###

        self.a = [BosonOp('a_'+str(i)) for i in range(self.m)]
        self.H = 0.
        self.nonlin_coeff = nonlin_coeff

    def make_chi_nonlinearity(self,delay_indices,start_nonlin,
                               length_nonlin,indices_of_refraction,
                               chi_order=3,chi_function=None,
                               ):
        chi_nonlinearity = Chi_nonlin(delay_indices,start_nonlin,
                                   length_nonlin,indices_of_refraction,
                                   chi_order=chi_order,chi_function=chi_function)
        self.chi_nonlinearities.append(chi_nonlinearity)

    def normalize_modes(self,):
        for mode in self.modes:
            mode /= functions._norm_of_mode(mode,self.delays)

    def mode_volumes(self,):
        '''
        Find the effective volume of each mode to normalize the field.

        Args:
            spatial_modes (list of column vectors): the amplitudes of the modes at
            various nodes
            delays (list of floats): The duration of each delay following
            each node in the system
        Returns:
            A list of the effective lengths of the various modes.
        '''

        volumes = []
        for mode in self.modes:
            for i,delay in enumerate(self.delays):
                volumes.append( delay * abs(mode[i,0]**2) *
                                self.cross_sectional_area )
        return volumes


################################################
    # def make_nonlin_term_sp(self,combination,pm_arr):
    #     '''
    #     Make symbolic nonlinear term using sympy.
    #
    #     Example:
    #     combination = [n,m,o]; pm_arr = [-1,1,1] ->> a(n) * a(m)^+ * a(o)^+
    #
    #     Args:
    #         combination (tuple/list of integers): indices of which terms to include
    #         pm_arr (tuple/list of +1 and -1): creation and annihilation
    #             indicators for the respective terms in combination.
    #     Returns:
    #         symbolic expression for the combination of creation and annihilation
    #         operators.
    #     '''
    #     r = 1.
    #     for index,sign in zip(combination,pm_arr):
    #         if sign == 1:
    #             r*= Dagger(self.a[index])
    #         else:
    #             r *= self.a[index]
    #     return r
    def make_nonlin_term_sympy(self,combination,pm_arr):
        '''
        Make symbolic nonlinear term using sympy.

        Example:
        combination = [n,m,o]; pm_arr = [-1,1,1] ->> a(n) * a(m)^+ * a(o)^+

        Args:
            combination (tuple/list of integers): indices of which terms to include
            pm_arr (tuple/list of +1 and -1): creation and annihilation
                indicators for the respective terms in combination.
        Returns:
            symbolic expression for the combination of creation and annihilation
            operators.
        '''
        r = 1.
        for index,sign in zip(combination,pm_arr):
            if sign == 1:
                r*= Dagger(self.a[index])
            else:
                r *= self.a[index]
        return r

    # def make_list_of_pm_arr(self,):
    #     '''
    #     Returns:
    #         List of lists of +1 and -1. The length of each list is chi_order+1.
    #         The number of -1's in each list is the number of photons annihilated.
    #         Each unique combination exists once.
    #     '''
    #     plus_minus_combinations = list(itertools.combinations(
    #         range(self.chi_order + 1), self.photons_annihilated))  ## pick which fields are annihilated
    #     list_of_pm_arr = []
    #     for tup in plus_minus_combinations:
    #         ls = [1]*(self.chi_order+1)
    #         for i in tup:
    #             ls[i]=-1
    #         list_of_pm_arr.append(ls)
    #     return list_of_pm_arr

    # def weight(self,combination,pm_arr):
    #     '''
    #     The weight to give to each nonlinear term characterized by the given
    #     combination and pm_arr.
    #
    #     Args:
    #         combination (list/tuple of integers): which modes/roots to pick
    #         pm_arr (list of +1 and -1): creation and annihilation of modes
    #     Returns:
    #         The weight to add to the Hamiltonian
    #     '''
    #     roots_to_use = np.array([self.roots[i] for i in combination])
    #     modes_to_use = [self.modes[i] for i in combination]
    #     return functions.make_nonlinear_interaction(
    #                 roots_to_use, modes_to_use, self.delays, self.delay_indices,
    #                 self.start_nonlin, self.length_nonlin, pm_arr,
    #                 self.indices_of_refraction)

    def phase_weight(self,combination,pm_arr,chi):
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
                    roots_to_use, modes_to_use, self.delays, chi.delay_indices,
                    chi.start_nonlin, chi.length_nonlin, pm_arr,
                    chi.indices_of_refraction)

    # def make_weights(self,):
    #     '''
    #     Make a dict to store the weights for the selected components and the
    #     creation/annihilation information.
    #
    #     Returns:
    #         A dictionary of weights. Each key is a tuple of a combination tuple
    #         and a pm_arr tuple (a tuple of +1 and -1).
    #     '''
    #     ## TODO: add a priori check to restrict exponential growth on the number
    #     ## of nonlienar coefficients
    #     list_of_pm_arr = self.make_list_of_pm_arr()
    #     weights = {}
    #     for pm_arr in list_of_pm_arr:
    #         field_combinations = itertools.combinations_with_replacement(
    #             range(self.m), self.chi_order+1)
    #         for combination in field_combinations:
    #             weights[tuple(combination),tuple(pm_arr)] = self.weight(combination,pm_arr)
    #     return weights

    def make_phase_matching_weights(self,chi):
        '''
        Make a dict to store the weights for the selected components and the
        creation/annihilation information.

        Returns:
            A dictionary of weights. Each key is a tuple consisting of two
            components: the first is a tuple of the indices of modes and the
            second is a tuple of +1 and -1.
        '''
        ## TODO: add a priori check to restrict exponential growth on the number
        ## of nonlienar coefficients
        list_of_pm_arr = list(itertools.product([-1, 1], repeat=3))

        weights = {}
        for pm_arr in list_of_pm_arr:
            field_combinations = itertools.combinations_with_replacement(
                range(self.m), chi.chi_order+1)
            for combination in field_combinations:
                weights[tuple(combination),tuple(pm_arr)] = self.phase_weight(
                    combination,pm_arr,chi)
        return weights

    # def make_nonlin_H(self,eps=1e-5):
    #     '''
    #     Make a nonlinear Hamiltonian based on nonlinear interaction terms
    #     Args:
    #         eps (optional[float]): Cutoff for the significance of a particular term.
    #     Returns:
    #         A symbolic expression for the nonlinear Hamiltonian.
    #     '''
    #
    #     weights = self.make_weights()
    #     significant_weights =  {k:v for k,v in weights.iteritems() if abs(v) > eps}
    #
    #     H_nonlin_sp = 0.
    #     for combination,pm_arr in significant_weights:
    #         H_nonlin_sp += (self.make_nonlin_term_sp(combination,pm_arr) *
    #                         significant_weights[combination,pm_arr])
    #     return H_nonlin_sp

########################################################

    def E_field_weight(self,mode_index):
        '''
        Make the weights for each field component E_i(n) = [weight] (a+a^+)

        Args:
            mode_index (int): The index of the mode.
        Returns:
            The weight in the equation above. It has form:
                sqrt[\hbar * \omega(n) / 2 V_eff(n) \epsilon].
        '''
        freq = self.roots[mode_index].imag
        omega = freq / (2 * consts.pi)
        if freq < 0:
            print 'Frequency is negative, taking absolute value.'
        eps0 = consts.epsilon_0
        hbar = consts.hbar
        return np.sqrt(hbar * abs(omega) / (2 * eps0 * self.volumes[mode_index]) )

    def make_E_field_weights(self,):
        '''
        Returns:
            A dictionary from mode index to the E-field weight.
        '''
        weights = {}
        for mode_index in range(self.m):
            weights[mode_index] = self.E_field_weight(mode_index)
        return weights


    def make_nonlin_H_from_chi(self,chi,eps=1e-5):
        '''
        Make a nonlinear Hamiltonian based on nonlinear interaction terms
        Args:
            chi (Chi_nonlin): nonlinearity to use
            eps (optional[float]): Cutoff for the significance of a particular term.
        Returns:
            A symbolic expression for the nonlinear Hamiltonian.
        '''

        H_nonlin_sp = 0.
        for chi in self.chi_nonlinearities:
            phase_matching_weights = self.make_phase_matching_weights(chi)
            significant_phase_matching_weights =  {k:v for k,v
                in phase_matching_weights.iteritems() if abs(v) > eps}
            for combination,pm_arr in significant_phase_matching_weights:
                chi_args = list(combination) + map(lambda i: self.polarizations[i],combination)
                H_nonlin_sp += ( self.make_nonlin_term_sympy(combination,pm_arr) *
                    chi.chi_function(*chi_args) *
                    significant_phase_matching_weights[combination,pm_arr] *
                    np.prod([self.E_field_weights[i] for i in combination]) )
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
                H_lin_sp += Dagger(self.a[i])*self.a[j]*Omega[i,j]
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
        H_nonlin = self.make_nonlin_H_from_chi(eps)
        H_lin = self.make_lin_H(Omega)
        self.H = H_lin + H_nonlin * self.nonlin_coeff
        return self.H

    def make_eq_motion(self,):
        '''
        Input is a tuple or list, output is a matrix vector.
        This generates Hamilton's equations of motion for a and a^H.
        These equations are CLASSICAL equations of motion. This means
        we replace the operators with c-numbers. The order of the operators
        will yield different results, so we assume the Hamiltonian is already
        in the desired order (e.g. normally ordered).

        Returns:
            A function that yields the Hamiltonian equations of motion based on
            the Hamiltonian given.
            The equations of motion take an array as an input and return a column
            vector as an output.
        '''

        ## c-numbers
        b = [sp.symbols('b'+str(i)) for i in range(self.m)]
        b_H = [sp.symbols('b_H'+str(i)) for i in range(self.m)]

        ## Hamiltonian is not always Hermitian. We use its complex conjugate.
        H_H = Dagger(self.H)

        def subs_c_number(expression,i):
            return expression.subs(self.a[i],b[i]).subs(Dagger(self.a[i]),b_H[i])

        H_c_numbers = self.H
        H_H_c_numbers = H_H
        for i in range(self.m):
            H_c_numbers = subs_c_number(H_c_numbers,i)
            H_H_c_numbers = subs_c_number(H_H_c_numbers,i)


        ## classical equations of motion
        diff_ls = ([1j*sp.diff(H_c_numbers,var) for var in b_H] +
                   [-1j*sp.diff(H_H_c_numbers,var) for var in b])
        fs = [sp.lambdify( tuple( b+b_H ),expression) for expression in diff_ls ]
        return lambda arr: (np.asmatrix([ f(* arr ) for f in fs])).T
